"""
FHIR R4 Communication search parameters (https://www.hl7.org/fhir/R4/communication.html#search)
plus the common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from communication_search() below. Same
arrangement as app.repository.task.search and app.repository.care_plan.search (references held as
columns, a shared token table and a shared reference table, Reference(Any) elements, canonical URLs
and `uri` values).

R4 defines no `priority`, `topic`, `about`, `in-response-to` or `reason-*` search parameter for
Communication, so none is declared.

Each parameter's SQL reads only the search index (CommunicationModel's columns and child tables,
see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
    uri_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.models.communication import (
    BASED_ON_TYPES,
    CANONICAL_TYPES,
    ENCOUNTER_TYPES,
    PART_OF_TYPES,
    RECIPIENT_TYPES,
    SENDER_TYPES,
    SUBJECT_TYPES,
    CommunicationIdentifier,
    CommunicationInstantiatesUri,
    CommunicationModel,
    CommunicationReference,
    CommunicationStatus,
    CommunicationToken,
)
from app.repository._search_targets import MODELED

P = CommunicationModel
_I = CommunicationIdentifier
_Tk = CommunicationToken
_R = CommunicationReference
_U = CommunicationInstantiatesUri
_STATUS_SYSTEM = "http://hl7.org/fhir/event-status"
_ABSOLUTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

# Every rebuilt resource type this server can chain through and `_include`: derived from
# RESOURCE_REGISTRY by app/repository/_search_targets.py, so there is no list to keep here.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = MODELED


def _model(resource_type: str):
    module, cls, id_col, *_ = _MODELED[resource_type]
    model = getattr(importlib.import_module(module), cls)
    return model, getattr(model, id_col)


def _registry_of(resource_type: str):
    def get():
        _m, _c, _i, module, factory = _MODELED[resource_type]
        return getattr(importlib.import_module(module), factory)()

    return get


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.communication_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.communication_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to
    the outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return P.communication_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the event-status system: `code` or `system|code`; another
    system or `|code` (no system) never matches; an unknown code matches nothing (rather than
    failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.status.is_not(None)
    try:
        return P.status == CommunicationStatus(token.code)
    except ValueError:
        return false()


def _range_param(start, end):
    """(match, present) for a date search over a half-open range held in two columns."""

    def match(value, modifier, ctx):
        return period_match(start, end, value)

    return match, lambda ctx: or_(start.is_not(None), end.is_not(None))


# -- identifier / the token parameters -----------------------------------------------------


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(
            _I, token_text_match((_I.type_text_norm, _I.type_display_norm), value)
        )
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(
            _I,
            _I.type_system == type_system,
            _I.type_code == type_code,
            _I.value == ident,
        )
    return _exists(_I, token_match(_I.system, _I.value, value))


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# -- references held as columns: subject / patient, encounter, sender -----------------------


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    communication row. `narrowed` restricts a multi-target element to one type (`patient` is
    `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )
    # `is_not(None)` keeps `NOT present` (`:missing=true`) from going NULL for a row whose
    # reference has no resolved type (a logical, identifier-only reference).
    type_filter = (type_.is_not(None), type_ == narrowed) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return and_(
                token_condition(ident_system, ident_value, parse_token(value)),
                *type_filter,
            )
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id with several
        # targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- based-on / part-of / recipient: the shared reference table -----------------------------


def _reference_param(param: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for one of the reference parameters held in the shared
    reference table, selected by its `param` value."""

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _R,
                _R.param == param,
                token_condition(
                    _R.reference_identifier_system,
                    _R.reference_identifier_value,
                    parse_token(value),
                ),
            )
        return _exists(
            _R,
            _R.param == param,
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _R,
            _R.param == param,
            or_(
                _R.reference_reference.is_not(None),
                _R.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


def _canonical_param():
    """`instantiates-canonical`: the values are canonical URLs, optionally versioned
    (`url|1.0`). A search value matches a stored canonical equal to it; an unversioned absolute
    URL also matches the stored versions of that URL; a relative `Type/<id>` matches by its
    resolved type and id."""
    param = "instantiates-canonical"

    def match(value, modifier, ctx):
        conditions = [
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                CANONICAL_TYPES,
                str,
            )
        ]
        if modifier is None and "|" not in value and _ABSOLUTE.match(value):
            conditions.append(
                _R.reference_reference.like(like_escape(value) + "|%", escape="\\")
            )
        return _exists(_R, _R.param == param, or_(*conditions))

    def present(ctx):
        return _exists(_R, _R.param == param)

    return (
        match,
        present,
        lambda: _child_sort(_R.reference_reference, _R, _R.param == param),
    )


def _uri_match(value, modifier, ctx):
    return _exists(_U, uri_match(_U.uri, value, modifier))


# -- _include / _revinclude ----------------------------------------------------------------


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`subject`, `encounter`, `sender`): the rows of
    `resource_type` these communications point at."""

    async def fetch(session, ctx, communications):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(c, id_)
            for c in communications
            if getattr(c, type_) == resource_type and getattr(c, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in the reference table."""

    async def fetch(session, ctx, communications):
        ids = select(model.reference_id).where(
            model.communication_pk.in_({c.id for c in communications}),
            model.reference_type == resource_type,
            model.reference_id.is_not(None),
            *conditions,
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_communications_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Communication:subject / :patient / :encounter / :sender - communications whose
    column reference points at one of these rows (matched on the public id `key(row)`). Declared
    on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(P, f"{prefix}_type"), getattr(P, f"{prefix}_id")
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_communications_via_reference(param: str, resource_type: str, key):
    """_revinclude=Communication:recipient / :part-of / :based-on - communications with a row of
    `param` in the reference table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.communication_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Communication rows."""
    from app.fhir.mappers.communication import to_fhir_communication
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Communication",
            lambda c: c.communication_id,
            to_fhir_communication,
            "communications",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def communication_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _TOKEN,
            sort=sort,
            example=example,
        )

    def date_param(name, description, expression, start, end, example):
        match, present = _range_param(start, end)
        return SearchParam(
            name,
            "date",
            description,
            expression,
            match,
            present,
            sort=lambda: start,
            example=example,
        )

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
        reachable = [t for t in targets if t in _MODELED]
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            _REFERENCE,
            targets=targets,
            chain=chain,
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    def table_ref(name, description, expression, targets, example):
        match, present, chain, sort = _reference_param(name, targets)
        reachable = [t for t in targets if t in _MODELED]
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            _REFERENCE,
            targets=targets,
            chain=chain,
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    canonical_match, canonical_present, canonical_sort = _canonical_param()
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public communication id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.communication_id,
            example="480001",
        ),
        SearchParam(
            "_lastUpdated",
            "date",
            "When the resource last changed (meta.lastUpdated)",
            "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v),
            lambda ctx: true(),
            sort=last_updated,
            example="ge2024-01-01",
        ),
        table_ref(
            "based-on",
            "Request fulfilled by this communication (Reference(Any))",
            "Communication.basedOn",
            BASED_ON_TYPES,
            "CommunicationRequest/470001",
        ),
        token(
            "category",
            "Message category",
            "Communication.category",
            "http://terminology.hl7.org/CodeSystem/communication-category|alert",
        ),
        column_ref(
            "encounter",
            "Encounter created as part of",
            "Communication.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Unique identifier",
            "Communication.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:communications|CM-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "instantiates-canonical",
            "reference",
            "Instantiates FHIR protocol or definition (a canonical URL)",
            "Communication.instantiatesCanonical",
            canonical_match,
            canonical_present,
            frozenset({"missing"}),
            targets=CANONICAL_TYPES,
            sort=canonical_sort,
            example="http://example.org/fhir/PlanDefinition/notify",
            modifier_docs={
                "missing": "`:missing=true` — resources with no canonical for this parameter; `:missing=false` — resources that have one."
            },
        ),
        SearchParam(
            "instantiates-uri",
            "uri",
            "Instantiates external protocol or definition",
            "Communication.instantiatesUri",
            _uri_match,
            lambda ctx: _exists(_U),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_U.uri, _U),
            example="http://example.org/protocols/notify",
            modifier_docs={
                "below": "`:below` — stored URIs that start with the value (`http://acme.org/p` finds `http://acme.org/p/1`).",
                "above": "`:above` — stored URIs that are a prefix of the value.",
            },
        ),
        token(
            "medium",
            "A channel of communication",
            "Communication.medium",
            "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode|WRITTEN",
        ),
        table_ref(
            "part-of",
            "Part of this action (Reference(Any))",
            "Communication.partOf",
            PART_OF_TYPES,
            "Communication/480001",
        ),
        column_ref(
            "patient",
            "Focus of message",
            "Communication.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "10001",
            narrowed="Patient",
        ),
        date_param(
            "received",
            "When received",
            "Communication.received",
            P.received_start,
            P.received_end,
            "ge2026-01-01",
        ),
        table_ref(
            "recipient",
            "Message recipient",
            "Communication.recipient",
            RECIPIENT_TYPES,
            "Practitioner/30001",
        ),
        column_ref(
            "sender",
            "Message sender",
            "Communication.sender",
            "sender",
            SENDER_TYPES,
            "Practitioner/30001",
        ),
        date_param(
            "sent",
            "When sent",
            "Communication.sent",
            P.sent_start,
            P.sent_end,
            "ge2026-01-01",
        ),
        SearchParam(
            "status",
            "token",
            f"preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown (system {_STATUS_SYSTEM})",
            "Communication.status",
            _status_match,
            lambda ctx: P.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="completed",
        ),
        column_ref(
            "subject",
            "Focus of message",
            "Communication.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("Communication", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param, targets):
        return tuple(
            IncludeTarget(
                "Communication", param, t, _include_child(_R, t, _R.param == param)
            )
            for t in targets
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="Communication",
        params={p.name: p for p in params},
        # Σ elements in the R4 Communication definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "instantiatesCanonical",
                "instantiatesUri",
                "basedOn",
                "partOf",
                "status",
                "statusReason",
                "priority",
                "subject",
                "encounter",
                "reasonCode",
                "reasonReference",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status"}),
        includes=(
            IncludeTarget(
                "Communication",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("encounter", "encounter", ENCOUNTER_TYPES),
            *column_includes("sender", "sender", SENDER_TYPES),
            *table_includes("recipient", RECIPIENT_TYPES),
            *table_includes("based-on", BASED_ON_TYPES),
            *table_includes("part-of", PART_OF_TYPES),
        ),
        # A Communication can be part of, or based on, another one.
        revincludes=(
            IncludeTarget(
                "Communication",
                "part-of",
                "Communication",
                revinclude_communications_via_reference(
                    "part-of", "Communication", lambda c: c.communication_id
                ),
                reverse=True,
            ),
            IncludeTarget(
                "Communication",
                "based-on",
                "Communication",
                revinclude_communications_via_reference(
                    "based-on", "Communication", lambda c: c.communication_id
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.communication_id.desc()],
    )

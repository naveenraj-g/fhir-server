"""
FHIR R4 Consent search parameters (https://www.hl7.org/fhir/R4/consent.html#search) plus the
common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from consent_search() below. Same
arrangement as app.repository.task.search (references held as columns, a shared token table and a
shared reference table, a Reference(Any) element).

Each parameter's SQL reads only the search index (ConsentModel's columns and child tables, see its
docstring) - never `content`.
"""

from __future__ import annotations

import importlib
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
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.consent import (
    ACTOR_TYPES,
    CONSENTOR_TYPES,
    DATA_TYPES,
    ORGANIZATION_TYPES,
    PATIENT_TYPES,
    SOURCE_TYPES,
    ConsentIdentifier,
    ConsentModel,
    ConsentReference,
    ConsentStatus,
    ConsentToken,
)
from app.repository._search_targets import MODELED

P = ConsentModel
_I = ConsentIdentifier
_Tk = ConsentToken
_R = ConsentReference
_STATUS_SYSTEM = "http://hl7.org/fhir/consent-state-codes"

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
    return exists(select(literal(1)).where(model.consent_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.consent_pk == P.id, *conditions)
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
    return P.consent_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the consent-state-codes system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing (rather
    than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.status.is_not(None)
    try:
        return P.status == ConsentStatus(token.code)
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


# -- references held as columns: patient, source-reference ----------------------------------


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    consent row."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        # `modifier` is a target type (source-reference:Consent=440001) or None; a bare id with
        # several targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- consentor / organization / actor / data: the shared reference table --------------------


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
    """_include of a reference held as columns (`patient`, `source-reference`): the rows of
    `resource_type` these consents point at."""

    async def fetch(session, ctx, consents):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(c, id_)
            for c in consents
            if getattr(c, type_) == resource_type and getattr(c, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in the reference table."""

    async def fetch(session, ctx, consents):
        ids = select(model.reference_id).where(
            model.consent_pk.in_({c.id for c in consents}),
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


def revinclude_consents_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Consent:patient / :source-reference - consents whose column reference points
    at one of these rows (matched on the public id `key(row)`). Declared on the registry of each
    target type."""

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


def revinclude_consents_via_reference(param: str, resource_type: str, key):
    """_revinclude=Consent:consentor / :organization / :actor / :data - consents with a row of
    `param` in the reference table pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.consent_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Consent rows."""
    from app.fhir.mappers.consent import to_fhir_consent
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind("Consent", lambda c: c.consent_id, to_fhir_consent, "consents")
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def consent_search() -> SearchRegistry:
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

    def column_ref(name, description, expression, prefix, targets, example):
        match, present, chain, sort = _column_ref(prefix, targets)
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

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public consent id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.consent_id,
            example="440001",
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
        token(
            "action",
            "Actions controlled by this rule",
            "Consent.provision.action",
            "http://terminology.hl7.org/CodeSystem/consentaction|access",
        ),
        table_ref(
            "actor",
            "Resource for the actor (or group, by role)",
            "Consent.provision.actor.reference",
            ACTOR_TYPES,
            "Practitioner/30001",
        ),
        token(
            "category",
            "Classification of the consent statement - for indexing/retrieval",
            "Consent.category",
            "http://loinc.org|59284-0",
        ),
        table_ref(
            "consentor",
            "Who is agreeing to the policy and rules",
            "Consent.performer",
            CONSENTOR_TYPES,
            "Patient/10001",
        ),
        table_ref(
            "data",
            "The actual data reference (Reference(Any))",
            "Consent.provision.data.reference",
            DATA_TYPES,
            "Observation/160001",
        ),
        SearchParam(
            "date",
            "date",
            "When this Consent was created or indexed",
            "Consent.dateTime",
            _range_param(P.date_start, P.date_end)[0],
            lambda ctx: P.date_start.is_not(None),
            sort=lambda: P.date_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Identifier for this record (external references)",
            "Consent.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:consents|C-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        table_ref(
            "organization",
            "Custodian of the consent",
            "Consent.organization",
            ORGANIZATION_TYPES,
            "Organization/190001",
        ),
        column_ref(
            "patient",
            "Who the consent applies to",
            "Consent.patient",
            "patient",
            PATIENT_TYPES,
            "10001",
        ),
        date_param(
            "period",
            "Timeframe for this rule",
            "Consent.provision.period",
            P.period_start,
            P.period_end,
            "ge2026-01-01",
        ),
        token(
            "purpose",
            "Context of activities covered by this rule",
            "Consent.provision.purpose",
            "http://terminology.hl7.org/CodeSystem/v3-ActReason|TREAT",
        ),
        token(
            "scope",
            "Which of the four areas this resource covers (extensible)",
            "Consent.scope",
            "http://terminology.hl7.org/CodeSystem/consentscope|patient-privacy",
        ),
        token(
            "security-label",
            "Security Labels that define affected resources",
            "Consent.provision.securityLabel",
            "http://terminology.hl7.org/CodeSystem/v3-Confidentiality|R",
        ),
        column_ref(
            "source-reference",
            "Search by reference to a Consent, DocumentReference, Contract or QuestionnaireResponse",
            "Consent.source",
            "source",
            SOURCE_TYPES,
            "DocumentReference/320001",
        ),
        SearchParam(
            "status",
            "token",
            f"draft | proposed | active | rejected | inactive | entered-in-error (system {_STATUS_SYSTEM})",
            "Consent.status",
            _status_match,
            lambda ctx: P.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="active",
        ),
    ]

    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("Consent", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param, targets):
        return tuple(
            IncludeTarget("Consent", param, t, _include_child(_R, t, _R.param == param))
            for t in targets
            if t in _MODELED
        )

    def self_revinclude(param: str):
        return IncludeTarget(
            "Consent",
            param,
            "Consent",
            revinclude_consents_via_column("source", "Consent", lambda c: c.consent_id),
            reverse=True,
        )

    return SearchRegistry(
        resource_type="Consent",
        params={p.name: p for p in params},
        # Σ elements in the R4 Consent definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "scope",
                "category",
                "patient",
                "dateTime",
                "performer",
                "organization",
                "sourceAttachment",
                "sourceReference",
                "policyRule",
                "verification",
                "provision",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "scope", "category"}),
        includes=(
            *column_includes("patient", "patient", PATIENT_TYPES),
            *column_includes("source-reference", "source", SOURCE_TYPES),
            *table_includes("consentor", CONSENTOR_TYPES),
            *table_includes("organization", ORGANIZATION_TYPES),
            *table_includes("actor", ACTOR_TYPES),
            *table_includes("data", DATA_TYPES),
        ),
        # A Consent can be the source of another one.
        revincludes=(self_revinclude("source-reference"),),
        default_sort=lambda: [P.consent_id.desc()],
    )

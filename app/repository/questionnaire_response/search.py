"""
FHIR R4 QuestionnaireResponse search parameters
(https://www.hl7.org/fhir/R4/questionnaireresponse.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include`, and the
OpenAPI docs all come from questionnaire_response_search() below. Same arrangement as
app.repository.document_reference.search (single references held as columns, one shared reference
table) - R4 defines no search parameter for the answers themselves, so the `item` tree is not
indexed at all.

Each parameter's SQL reads only the search index (QuestionnaireResponseModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.models.questionnaire_response import (
    AUTHOR_TYPES,
    ENCOUNTER_TYPES,
    REFERENCE_TYPES,
    SOURCE_TYPES,
    SUBJECT_TYPES,
    QuestionnaireResponseIdentifier,
    QuestionnaireResponseModel,
    QuestionnaireResponseReference,
    QuestionnaireResponseStatus,
)
from app.repository._consent_revinclude import column_consent_revincludes
from app.repository._search_targets import MODELED

M = QuestionnaireResponseModel
_I = QuestionnaireResponseIdentifier
_R = QuestionnaireResponseReference

# QuestionnaireResponse.status is a `code` from the R4 questionnaire-answers-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/questionnaire-answers-status"
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
    return exists(
        select(literal(1)).where(model.questionnaire_response_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.questionnaire_response_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to the
    outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.questionnaire_response_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the questionnaire-answers-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == QuestionnaireResponseStatus(token.code)
    except ValueError:
        return false()


def _authored_match(value, modifier, ctx):
    # QuestionnaireResponse.authored is a dateTime, possibly partial (`2026`, `2026-02`): matched
    # as the range it covers.
    return period_match(M.authored_start, M.authored_end, value)


def _identifier_param(model):
    """(match, present, sort) for the Identifier search held in the identifier table."""

    def match(value, modifier, ctx):
        if modifier == "text":
            return _exists(
                model,
                token_text_match(
                    (model.type_text_norm, model.type_display_norm), value
                ),
            )
        if modifier == "of-type":
            type_system, type_code, ident = parse_of_type(value)
            return _exists(
                model,
                model.type_system == type_system,
                model.type_code == type_code,
                model.value == ident,
            )
        return _exists(model, token_match(model.system, model.value, value))

    def present(ctx):
        return _exists(model)

    def sort():
        return _child_sort(model.value, model)

    return match, present, sort


# ── references held as columns: subject / patient / encounter / author / source ─


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    questionnaire_response row. `narrowed` restricts a multi-target element to one type
    (`patient` is `subject` resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(M, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(M, f"{prefix}_identifier_system"),
        getattr(M, f"{prefix}_identifier_value"),
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
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── based-on / part-of / questionnaire: one row per Reference in the shared table ──


def _reference_param(param: str):
    """(match, present, chain, sort) for one of the reference parameters held in the shared
    reference table, selected by its `param` value."""
    targets = REFERENCE_TYPES[param]

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


def _canonical_matches(row_model, ref):
    """Condition: the questionnaire reference `ref` (a reference-table row) resolves to the
    Questionnaire row `row_model` - by a relative `Questionnaire/<id>`, by an equal canonical URL
    or by `url|version` (the stored canonical starts with the Questionnaire's own url + `|`)."""
    return or_(
        and_(
            ref.reference_type == "Questionnaire",
            ref.reference_id == row_model.questionnaire_id,
        ),
        and_(row_model.url.is_not(None), ref.reference_reference == row_model.url),
        and_(
            row_model.url.is_not(None),
            func.substr(ref.reference_reference, 1, func.length(row_model.url) + 1)
            == row_model.url.concat("|"),
        ),
    )


def _questionnaire_chain(target, inner, ctx):
    """`questionnaire.title=...`: a response whose canonical resolves to a Questionnaire in the
    same tenant that matches `inner`. The canonical string is resolved against the Questionnaire's
    own `url` (an unversioned or versioned canonical) or its public id."""
    model, _id = _model("Questionnaire")
    return _exists(
        _R,
        _R.param == "questionnaire",
        exists(
            select(literal(1))
            .where(
                model.tenant_id == ctx.tenant_id, _canonical_matches(model, _R), inner
            )
            .correlate(_R)
        ),
    )


def _questionnaire_param():
    """`questionnaire` searches the canonical URL of the Questionnaire (optionally versioned,
    `url|1.0`). A search value matches a stored canonical equal to it; an unversioned absolute URL
    also matches the stored versions of that URL; a relative `Questionnaire/<id>` matches by its
    resolved type and id."""
    param = "questionnaire"
    targets = REFERENCE_TYPES[param]

    def match(value, modifier, ctx):
        conditions = [
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
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

    def sort():
        return _child_sort(_R.reference_reference, _R, _R.param == param)

    return match, present, sort


# ── _include ─────────────────────────────────────────────────────────────────


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
    """_include of a reference held as columns: the rows of `resource_type` these responses point
    at."""

    async def fetch(session, ctx, responses):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in responses
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference held in the shared reference table: the rows of `resource_type`
    these responses' `param` references point at."""

    async def fetch(session, ctx, responses):
        ids = select(_R.reference_id).where(
            _R.questionnaire_response_pk.in_({r.id for r in responses}),
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


async def _include_questionnaire(session, ctx, responses):
    """_include=QuestionnaireResponse:questionnaire - the Questionnaires these responses' canonical
    URLs (or relative `Questionnaire/<id>` references) resolve to. An unversioned canonical brings
    in every stored version of that url."""
    model, _id = _model("Questionnaire")
    rows = (
        await session.execute(
            select(_R.reference_reference, _R.reference_type, _R.reference_id).where(
                _R.questionnaire_response_pk.in_({r.id for r in responses}),
                _R.param == "questionnaire",
            )
        )
    ).all()
    urls, ids = set(), set()
    for reference, rtype, rid in rows:
        if rtype == "Questionnaire" and rid:
            ids.add(rid)
        elif reference:
            urls.add(reference.split("|", 1)[0])
    conditions = []
    if ids:
        conditions.append(model.questionnaire_id.in_(ids))
    if urls:
        conditions.append(model.url.in_(urls))
    if not conditions:
        return []
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, or_(*conditions))
    )


def revinclude_responses_via_questionnaire(key_url, key_id):
    """_revinclude=QuestionnaireResponse:questionnaire - the responses whose canonical resolves to
    one of these Questionnaires (matched on url / `url|version` / the public id). Declared on the
    Questionnaire registry."""

    async def fetch(session, ctx, rows):
        conditions = []
        for row in rows:
            url = key_url(row)
            conditions.append(
                and_(
                    _R.reference_type == "Questionnaire", _R.reference_id == key_id(row)
                )
            )
            if url:
                conditions.append(_R.reference_reference == url)
                conditions.append(
                    _R.reference_reference.like(like_escape(url) + "|%", escape="\\")
                )
        if not conditions:
            return []
        pks = select(_R.questionnaire_response_pk).where(
            _R.param == "questionnaire", or_(*conditions)
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def revinclude_responses_via_column(prefix: str, resource_type: str, key):
    """_revinclude=QuestionnaireResponse:subject / :patient / :encounter / :author / :source -
    responses whose column reference points at one of these rows (matched on the public id
    `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(M, f"{prefix}_type"), getattr(M, f"{prefix}_id")
        return await _fetch(
            session,
            select(M).where(
                M.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_responses_via_reference(param: str, resource_type: str, key):
    """_revinclude=QuestionnaireResponse:based-on / :part-of - responses with a reference row of
    `param` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.questionnaire_response_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders QuestionnaireResponse rows."""
    from app.fhir.mappers.questionnaire_response import to_fhir_questionnaire_response
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "QuestionnaireResponse",
            lambda r: r.questionnaire_response_id,
            to_fhir_questionnaire_response,
            "questionnaire-responses",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}
_TEXT_DOC = {
    "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
}


@cache
def questionnaire_response_search() -> SearchRegistry:
    _register_kind()

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
        modeled = [t for t in targets if t in _MODELED]
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
            chain_targets={t: _registry_of(t) for t in modeled},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    def table_ref(name, description, expression, example):
        match, present, chain, sort = _reference_param(name)
        targets = REFERENCE_TYPES[name]
        modeled = [t for t in targets if t in _MODELED]
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
            chain_targets={t: _registry_of(t) for t in modeled},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    identifier_match, identifier_present, identifier_sort = _identifier_param(_I)
    questionnaire_match, questionnaire_present, questionnaire_sort = (
        _questionnaire_param()
    )
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public questionnaire response id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.questionnaire_response_id,
            example="60001",
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
        column_ref(
            "author",
            "The author of the questionnaire response",
            "QuestionnaireResponse.author",
            "author",
            AUTHOR_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "authored",
            "date",
            "When the questionnaire response was last changed",
            "QuestionnaireResponse.authored",
            _authored_match,
            lambda ctx: M.authored_start.is_not(None),
            sort=lambda: M.authored_start,
            example="ge2026-01-01",
        ),
        table_ref(
            "based-on",
            "Plan/proposal/order fulfilled by this questionnaire response",
            "QuestionnaireResponse.basedOn",
            "ServiceRequest/80001",
        ),
        column_ref(
            "encounter",
            "Encounter associated with the questionnaire response",
            "QuestionnaireResponse.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "The unique identifier associated with the questionnaire response",
            "QuestionnaireResponse.identifier",
            identifier_match,
            identifier_present,
            _IDENTIFIER,
            sort=identifier_sort,
            example="urn:questionnaire-responses|QR-1",
            modifier_docs=_TEXT_DOC,
        ),
        table_ref(
            "part-of",
            "Procedure or observation this questionnaire response was performed as a part of",
            "QuestionnaireResponse.partOf",
            "Observation/160001",
        ),
        column_ref(
            "patient",
            "The patient that is the subject of the questionnaire response",
            "QuestionnaireResponse.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "questionnaire",
            "reference",
            "The questionnaire the answers are provided for (a canonical URL)",
            "QuestionnaireResponse.questionnaire",
            questionnaire_match,
            questionnaire_present,
            frozenset({"missing"}),
            targets=REFERENCE_TYPES["questionnaire"],
            chain=_questionnaire_chain,
            chain_targets={"Questionnaire": _registry_of("Questionnaire")},
            sort=questionnaire_sort,
            example="https://fhir-server.dev/fhir/Questionnaire/phq-9",
            modifier_docs={
                "missing": "`:missing=true` — responses with no questionnaire; `:missing=false` — responses that name one."
            },
        ),
        column_ref(
            "source",
            "The individual providing the information reflected in the questionnaire response",
            "QuestionnaireResponse.source",
            "source",
            SOURCE_TYPES,
            "Patient/10001",
        ),
        SearchParam(
            "status",
            "token",
            "in-progress | completed | amended | entered-in-error | stopped "
            f"(system {_STATUS_SYSTEM})",
            "QuestionnaireResponse.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="completed",
        ),
        column_ref(
            "subject",
            "The subject of the questionnaire response",
            "QuestionnaireResponse.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    # One include per target type that is a resource here, so `_include=...:author` brings in all
    # of them and `...:author:Practitioner` just the Practitioners.
    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("QuestionnaireResponse", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    def table_includes(param):
        return tuple(
            IncludeTarget(
                "QuestionnaireResponse", param, t, _include_reference(param, t)
            )
            for t in REFERENCE_TYPES[param]
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="QuestionnaireResponse",
        params={p.name: p for p in params},
        # Σ elements in the R4 QuestionnaireResponse definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "basedOn",
                "partOf",
                "questionnaire",
                "status",
                "subject",
                "encounter",
                "authored",
                "author",
                "source",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status"}),
        includes=(
            IncludeTarget(
                "QuestionnaireResponse",
                "patient",
                "Patient",
                _include_column("subject", "Patient"),
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("encounter", "encounter", ENCOUNTER_TYPES),
            *column_includes("author", "author", AUTHOR_TYPES),
            *column_includes("source", "source", SOURCE_TYPES),
            IncludeTarget(
                "QuestionnaireResponse",
                "questionnaire",
                "Questionnaire",
                _include_questionnaire,
            ),
            *table_includes("based-on"),
            *table_includes("part-of"),
        ),
        # Nothing rebuilt points at a QuestionnaireResponse through a search parameter we declare
        # a reverse include for (Observation.derivedFrom / hasMember are not followed yet).
        revincludes=(
            *column_consent_revincludes(
                ("source-reference",),
                "source",
                "QuestionnaireResponse",
                lambda x: x.questionnaire_response_id,
            ),
        ),
        default_sort=lambda: [M.questionnaire_response_id.desc()],
    )

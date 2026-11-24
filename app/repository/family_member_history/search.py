"""
FHIR R4 FamilyMemberHistory search parameters
(https://www.hl7.org/fhir/R4/familymemberhistory.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` /
`_revinclude`, and the OpenAPI docs all come from family_member_history_search() below.
Same arrangement as app.repository.procedure.search for `instantiates-canonical` /
`instantiates-uri`, and app.repository.immunization.search for the rest.

Each parameter's SQL reads only the search index (FamilyMemberHistoryModel's columns and
child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._search_targets import MODELED
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
from app.repository._clinical_impression_revinclude import (
    reference_impression_revincludes,
)
from app.models.family_member_history import (
    REFERENCE_TYPES,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryInstantiatesUri,
    FamilyMemberHistoryModel,
    FamilyMemberHistoryReference,
    FamilyMemberHistoryStatus,
    FamilyMemberHistoryToken,
)

M = FamilyMemberHistoryModel
_I = FamilyMemberHistoryIdentifier
_Tk = FamilyMemberHistoryToken
_R = FamilyMemberHistoryReference
_U = FamilyMemberHistoryInstantiatesUri
_STATUS_SYSTEM = "http://hl7.org/fhir/history-status"
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
        select(literal(1)).where(model.family_member_history_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.family_member_history_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does
    not correlate to the outer row — it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.family_member_history_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the history-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == FamilyMemberHistoryStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # FamilyMemberHistory.date is a dateTime: matched as the range it covers.
    return period_match(M.date_start, M.date_end, value)


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
    """(match, present, sort) for one of the token parameters held in the
    shared token table, selected by its `param` value."""

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


def _patient_ref():
    """(match, present, chain, sort) for `patient`, held as `patient_*` columns
    (single target, so a bare id works)."""
    ref, type_, id_ = M.patient_reference, M.patient_type, M.patient_id

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(
                M.patient_identifier_system,
                M.patient_identifier_value,
                parse_token(value),
            )
        return reference_match(type_, id_, ref, value, modifier, ctx, ("Patient",), str)

    def present(ctx):
        return or_(ref.is_not(None), M.patient_identifier_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


def _canonical_param():
    """`instantiates-canonical`: the values are canonical URLs, optionally versioned
    (`url|1.0`). A search value matches a stored canonical equal to it; an unversioned
    absolute URL also matches the stored versions of that URL; a relative `Type/<id>`
    matches by its resolved type and id."""
    param = "instantiates-canonical"
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

    return (
        match,
        present,
        lambda: _child_sort(_R.reference_reference, _R, _R.param == param),
    )


def _uri_match(value, modifier, ctx):
    return _exists(_U, uri_match(_U.uri, value, modifier))


# ── _include / _revinclude ───────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_patient():
    """_include=FamilyMemberHistory:patient — the Patients these point at."""

    async def fetch(session, ctx, histories):
        ids = {
            h.patient_id
            for h in histories
            if h.patient_type == "Patient" and h.patient_id
        }
        return await _load(session, ctx, "Patient", ids)

    return fetch


def revinclude_histories_via_patient(key):
    """_revinclude=FamilyMemberHistory:patient — histories whose patient is one of these
    Patients (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(M).where(
                M.tenant_id == ctx.tenant_id,
                M.patient_type == "Patient",
                M.patient_id.in_(ids),
            ),
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders FamilyMemberHistory rows."""
    from app.fhir.mappers.family_member_history import to_fhir_family_member_history
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "FamilyMemberHistory",
            lambda r: r.family_member_history_id,
            to_fhir_family_member_history,
            "family-member-histories",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def family_member_history_search() -> SearchRegistry:
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

    patient_match, patient_present, patient_chain, patient_sort = _patient_ref()
    canonical_match, canonical_present, canonical_sort = _canonical_param()

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public family member history id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.family_member_history_id,
            example="490001",
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
            "code",
            "A search by a condition code",
            "FamilyMemberHistory.condition.code",
            "http://snomed.info/sct|254837009",
        ),
        SearchParam(
            "date",
            "date",
            "When history was recorded or last updated",
            "FamilyMemberHistory.date",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "A search by a record identifier",
            "FamilyMemberHistory.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:histories|FMH-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "instantiates-canonical",
            "reference",
            "Instantiates FHIR protocol or definition (a canonical URL)",
            "FamilyMemberHistory.instantiatesCanonical",
            canonical_match,
            canonical_present,
            frozenset({"missing"}),
            targets=REFERENCE_TYPES["instantiates-canonical"],
            sort=canonical_sort,
            example="http://example.org/fhir/PlanDefinition/family-history",
            modifier_docs={
                "missing": "`:missing=true` — resources with no canonical for this parameter; `:missing=false` — resources that have one."
            },
        ),
        SearchParam(
            "instantiates-uri",
            "uri",
            "Instantiates external protocol or definition",
            "FamilyMemberHistory.instantiatesUri",
            _uri_match,
            lambda ctx: _exists(_U),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_U.uri, _U),
            example="http://example.org/protocols/family-history",
            modifier_docs={
                "below": "`:below` — stored URIs that start with the value (`http://acme.org/p` finds `http://acme.org/p/1`).",
                "above": "`:above` — stored URIs that are a prefix of the value.",
            },
        ),
        SearchParam(
            "patient",
            "reference",
            "The identity of a subject to list family member history items for",
            "FamilyMemberHistory.patient",
            patient_match,
            patient_present,
            _REFERENCE,
            targets=("Patient",),
            chain=patient_chain,
            chain_targets={"Patient": _registry_of("Patient")},
            sort=patient_sort,
            example="Patient/10001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "relationship",
            "A search by a relationship type",
            "FamilyMemberHistory.relationship",
            "http://terminology.hl7.org/CodeSystem/v3-RoleCode|MTH",
        ),
        token(
            "sex",
            "A search by a sex code of a family member",
            "FamilyMemberHistory.sex",
            "male",
        ),
        SearchParam(
            "status",
            "token",
            f"partial | completed | entered-in-error | health-unknown (system {_STATUS_SYSTEM})",
            "FamilyMemberHistory.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="completed",
        ),
    ]

    return SearchRegistry(
        resource_type="FamilyMemberHistory",
        params={p.name: p for p in params},
        # Σ elements in the R4 FamilyMemberHistory definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "instantiatesCanonical",
                "instantiatesUri",
                "status",
                "dataAbsentReason",
                "patient",
                "date",
                "name",
                "relationship",
                "sex",
                "ageAge",
                "ageRange",
                "ageString",
                "estimatedAge",
                "deceasedBoolean",
                "deceasedAge",
                "deceasedRange",
                "deceasedDate",
                "deceasedString",
                "reasonCode",
                "reasonReference",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "patient", "relationship"}),
        includes=(
            IncludeTarget(
                "FamilyMemberHistory", "patient", "Patient", _include_patient()
            ),
        ),
        # ClinicalImpression.investigation points here.
        revincludes=(
            *reference_impression_revincludes(
                "investigation",
                "FamilyMemberHistory",
                lambda r: r.family_member_history_id,
            ),
        ),
        default_sort=lambda: [M.family_member_history_id.desc()],
    )

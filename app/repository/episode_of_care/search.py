"""
FHIR R4 EpisodeOfCare search parameters (https://www.hl7.org/fhir/R4/episodeofcare.html#search)
plus the common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from episode_of_care_search() below.
Same arrangement as app.repository.care_team.search (single references held as columns, one shared
token table) plus one shared reference table for the two repeating reference parameters
(`condition`, `incoming-referral`).

Each parameter's SQL reads only the search index (EpisodeOfCareModel's columns and child tables,
see its docstring) - never `content`.
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
from app.models.episode_of_care import (
    ORGANIZATION_TYPES,
    PATIENT_TYPES,
    REFERENCE_TYPES,
    EpisodeOfCareIdentifier,
    EpisodeOfCareModel,
    EpisodeOfCareReference,
    EpisodeOfCareStatus,
    EpisodeOfCareToken,
)
from app.repository._document_reference_revinclude import (
    reference_document_reference_revincludes,
)
from app.repository._encounter_revinclude import reference_encounter_revincludes
from app.repository._medication_administration_revinclude import (
    column_medication_administration_revincludes,
)
from app.repository._medication_dispense_revinclude import (
    column_medication_dispense_revincludes,
)
from app.repository._medication_statement_revinclude import (
    column_medication_statement_revincludes,
)
from app.repository._search_targets import MODELED

M = EpisodeOfCareModel
_I = EpisodeOfCareIdentifier
_Tk = EpisodeOfCareToken
_R = EpisodeOfCareReference

# EpisodeOfCare.status is a `code` from the R4 episode-of-care-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/episode-of-care-status"

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
        select(literal(1)).where(model.episode_of_care_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.episode_of_care_pk == M.id, *conditions)
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
    return M.episode_of_care_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the episode-of-care-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code matches
    nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == EpisodeOfCareStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # EpisodeOfCare.period is a Period: matched as the range it covers (an episode with no period
    # never matches).
    return period_match(M.period_start, M.period_end, value)


def _identifier_param(model):
    """(match, present, sort) for an Identifier search held in one identifier-shaped table
    (`identifier`)."""

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


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system,
                _Tk.code,
                value,
                modifier,
                (_Tk.text_norm, _Tk.display_norm),
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# ── references held as columns: patient / organization / care-manager ─────────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    episode_of_care row. `narrowed` restricts a multi-target element to one type (`care-manager`
    is `careManager` resolved to a Practitioner)."""
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
        if narrowed:
            # `careManager` can also be a PractitionerRole: only a Practitioner is this
            # parameter's, so a PractitionerRole id never matches.
            return and_(
                reference_match(type_, id_, ref, value, modifier, ctx, targets, str),
                *type_filter,
            )
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── condition / incoming-referral: one row per Reference in the shared reference table ──


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


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns: the rows of `resource_type` these episodes point
    at."""

    async def fetch(session, ctx, episodes):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in episodes
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_reference(param: str, resource_type: str):
    """_include of a reference held in the shared reference table: the rows of `resource_type`
    these episodes' `param` references point at."""

    async def fetch(session, ctx, episodes):
        ids = select(_R.reference_id).where(
            _R.episode_of_care_pk.in_({r.id for r in episodes}),
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


def revinclude_episodes_via_column(prefix: str, resource_type: str, key):
    """_revinclude=EpisodeOfCare:patient / :organization / :care-manager - episodes whose column
    reference points at one of these rows (matched on the public id `key(row)`). Declared on the
    registry of each target type."""

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


def revinclude_episodes_via_reference(param: str, resource_type: str, key):
    """_revinclude=EpisodeOfCare:condition / :incoming-referral - episodes with a reference row
    of `param` pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.episode_of_care_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders EpisodeOfCare rows."""
    from app.fhir.mappers.episode_of_care import to_fhir_episode_of_care
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "EpisodeOfCare",
            lambda r: r.episode_of_care_id,
            to_fhir_episode_of_care,
            "episodes-of-care",
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
def episode_of_care_search() -> SearchRegistry:
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

    def reference(name, description, expression, example):
        # The R4 search-parameter name is also the `param` value in the reference table.
        targets = REFERENCE_TYPES[name]
        match, present, chain, sort = _reference_param(name, targets)
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
            chain_targets={t: _registry_of(t) for t in targets},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    identifier_match, identifier_present, identifier_sort = _identifier_param(_I)
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public episode of care id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.episode_of_care_id,
            example="350001",
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
            "care-manager",
            "Care manager/care coordinator for the patient",
            "EpisodeOfCare.careManager.where(resolve() is Practitioner)",
            "care_manager",
            ("Practitioner",),
            "Practitioner/30001",
            narrowed="Practitioner",
        ),
        reference(
            "condition",
            "Conditions/problems/diagnoses this episode of care is for",
            "EpisodeOfCare.diagnosis.condition",
            "Condition/120001",
        ),
        SearchParam(
            "date",
            "date",
            "The provided date search value falls within the episode of care's period",
            "EpisodeOfCare.period",
            _date_match,
            lambda ctx: M.period_start.is_not(None) | M.period_end.is_not(None),
            sort=lambda: M.period_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "Business Identifier(s) relevant for this EpisodeOfCare",
            "EpisodeOfCare.identifier",
            identifier_match,
            identifier_present,
            _IDENTIFIER,
            sort=identifier_sort,
            example="urn:episodes-of-care|EOC-1",
            modifier_docs=_TEXT_DOC,
        ),
        reference(
            "incoming-referral",
            "Incoming Referral Request",
            "EpisodeOfCare.referralRequest",
            "ServiceRequest/80001",
        ),
        column_ref(
            "organization",
            "The organization that has assumed the specific responsibilities of this EpisodeOfCare",
            "EpisodeOfCare.managingOrganization",
            "managing_organization",
            ORGANIZATION_TYPES,
            "Organization/190001",
        ),
        column_ref(
            "patient",
            "The patient who is the focus of this episode of care",
            "EpisodeOfCare.patient",
            "patient",
            PATIENT_TYPES,
            "Patient/10001",
        ),
        SearchParam(
            "status",
            "token",
            "planned | waitlist | active | onhold | finished | cancelled | entered-in-error "
            f"(system {_STATUS_SYSTEM})",
            "EpisodeOfCare.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="active",
        ),
        token(
            "type",
            "Type/class - e.g. specialist referral, disease management",
            "EpisodeOfCare.type",
            "http://terminology.hl7.org/CodeSystem/episodeofcare-type|cacp",
        ),
    ]

    return SearchRegistry(
        resource_type="EpisodeOfCare",
        params={p.name: p for p in params},
        # Σ elements in the R4 EpisodeOfCare definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "status",
                "type",
                "diagnosis",
                "patient",
                "managingOrganization",
                "period",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "patient"}),
        includes=(
            IncludeTarget(
                "EpisodeOfCare",
                "patient",
                "Patient",
                _include_column("patient", "Patient"),
            ),
            IncludeTarget(
                "EpisodeOfCare",
                "organization",
                "Organization",
                _include_column("managing_organization", "Organization"),
            ),
            IncludeTarget(
                "EpisodeOfCare",
                "care-manager",
                "Practitioner",
                _include_column("care_manager", "Practitioner"),
            ),
            IncludeTarget(
                "EpisodeOfCare",
                "condition",
                "Condition",
                _include_reference("condition", "Condition"),
            ),
            IncludeTarget(
                "EpisodeOfCare",
                "incoming-referral",
                "ServiceRequest",
                _include_reference("incoming-referral", "ServiceRequest"),
            ),
        ),
        # Encounters that name one of these episodes in `episodeOfCare`.
        revincludes=(
            *column_medication_dispense_revincludes(
                ("context",), "context", "EpisodeOfCare", lambda x: x.episode_of_care_id
            ),
            *column_medication_administration_revincludes(
                ("context",), "context", "EpisodeOfCare", lambda x: x.episode_of_care_id
            ),
            *column_medication_statement_revincludes(
                ("context",), "context", "EpisodeOfCare", lambda x: x.episode_of_care_id
            ),
            *reference_document_reference_revincludes(
                "encounter", "EpisodeOfCare", lambda x: x.episode_of_care_id
            ),
            *reference_encounter_revincludes(
                "EpisodeOfCare",
                lambda r: r.episode_of_care_id,
                ("episode-of-care",),
            ),
        ),
        default_sort=lambda: [M.episode_of_care_id.desc()],
    )

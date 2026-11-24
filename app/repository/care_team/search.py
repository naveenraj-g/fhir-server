"""
FHIR R4 CareTeam search parameters (https://www.hl7.org/fhir/R4/careteam.html#search) plus the
common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from care_team_search() below. Same
arrangement as app.repository.specimen.search (single references held as columns, one shared
token table), plus the repeating `participant` reference held in its own table (one row per
participant.member).

Each parameter's SQL reads only the search index (CareTeamModel's columns and child tables, see
its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.repository._consent_revinclude import reference_consent_revincludes
from app.repository._task_revinclude import column_task_revincludes
from app.repository._search_targets import MODELED
from app.repository._care_plan_revinclude import (
    performer_care_plan_revincludes,
    reference_care_plan_revincludes,
)
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
from app.repository._diagnostic_report_revinclude import performer_report_revincludes
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._observation_revinclude import reference_observation_revincludes
from app.repository._service_request_revinclude import (
    performer_service_request_revincludes,
)
from app.models.care_team import (
    ENCOUNTER_TYPES,
    PARTICIPANT_TYPES,
    SUBJECT_TYPES,
    CareTeamIdentifier,
    CareTeamModel,
    CareTeamParticipant,
    CareTeamStatus,
    CareTeamToken,
)

M = CareTeamModel
_I = CareTeamIdentifier
_Tk = CareTeamToken
_P = CareTeamParticipant

# CareTeam.status is a `code` from the R4 care_team-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/care-team-status"

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
    return exists(select(literal(1)).where(model.care_team_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.care_team_pk == M.id, *conditions)
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
    return M.care_team_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the care_team-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == CareTeamStatus(token.code)
    except ValueError:
        return false()


def _date_match(value, modifier, ctx):
    # CareTeam.period is a Period: matched as the range it covers (a care team with no period
    # never matches).
    return period_match(M.period_start, M.period_end, value)


def _identifier_param(model, text_cols_doc=None):
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
    """(match, present, sort) for one of the token parameters held in the
    shared token table, selected by its `param` value."""

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


# ── references held as columns: subject / patient / encounter ─────────────────


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    care_team row. `narrowed` restricts a multi-target element to one type (`patient` is
    `subject` resolved to a Patient)."""
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
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id with several
        # targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# ── participant: one row per participant.member ──────────────────────────────


def _participant_param():
    """(match, present, chain, sort) for `participant`, held in the participant table."""
    targets = PARTICIPANT_TYPES

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _P,
                token_condition(
                    _P.reference_identifier_system,
                    _P.reference_identifier_value,
                    parse_token(value),
                ),
            )
        return _exists(
            _P,
            reference_match(
                _P.reference_type,
                _P.reference_id,
                _P.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _P,
            or_(
                _P.reference_reference.is_not(None),
                _P.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _P,
            _P.reference_type == target,
            _P.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_P.reference_id, _P)

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
    """_include of a reference held as columns: the rows of `resource_type` these care_teams
    point at."""

    async def fetch(session, ctx, care_teams):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(r, id_)
            for r in care_teams
            if getattr(r, type_) == resource_type and getattr(r, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_participant(resource_type: str):
    """_include=CareTeam:participant - the rows of `resource_type` these care teams' participants
    point at."""

    async def fetch(session, ctx, care_teams):
        ids = select(_P.reference_id).where(
            _P.care_team_pk.in_({r.id for r in care_teams}),
            _P.reference_type == resource_type,
            _P.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_care_teams_via_column(prefix: str, resource_type: str, key):
    """_revinclude=CareTeam:subject / :patient / :encounter — care_teams whose column reference
    points at one of these rows (matched on the public id `key(row)`). Declared on the registry
    of each target type."""

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


def revinclude_care_teams_via_participant(resource_type: str, key):
    """_revinclude=CareTeam:participant - care teams with a participant row pointing at one of
    these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_P.care_team_pk).where(
            _P.reference_type == resource_type,
            _P.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders CareTeam rows."""
    from app.fhir.mappers.care_team import to_fhir_care_team
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "CareTeam", lambda r: r.care_team_id, to_fhir_care_team, "care-teams"
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
def care_team_search() -> SearchRegistry:
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

    def identifier(name, description, expression, model, example):
        match, present, sort = _identifier_param(model)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _IDENTIFIER,
            sort=sort,
            example=example,
            modifier_docs=_TEXT_DOC,
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

    participant_match, participant_present, participant_chain, participant_sort = (
        _participant_param()
    )
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public care team id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.care_team_id,
            example="390001",
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
            "category",
            "Type of team",
            "CareTeam.category",
            "http://loinc.org|LA27976-2",
        ),
        SearchParam(
            "date",
            "date",
            "Time period team covers",
            "CareTeam.period",
            _date_match,
            lambda ctx: M.period_start.is_not(None) | M.period_end.is_not(None),
            sort=lambda: M.period_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "Encounter created as part of",
            "CareTeam.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        identifier(
            "identifier",
            "External Ids for this team",
            "CareTeam.identifier",
            _I,
            "urn:care-teams|CT-1",
        ),
        SearchParam(
            "participant",
            "reference",
            "Who is involved",
            "CareTeam.participant.member",
            participant_match,
            participant_present,
            _REFERENCE,
            targets=PARTICIPANT_TYPES,
            chain=participant_chain,
            chain_targets={t: _registry_of(t) for t in PARTICIPANT_TYPES},
            sort=participant_sort,
            example="Practitioner/30001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        column_ref(
            "patient",
            "Who care team is for",
            "CareTeam.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "Patient/10001",
            narrowed="Patient",
        ),
        SearchParam(
            "status",
            "token",
            f"proposed | active | suspended | inactive | entered-in-error (system {_STATUS_SYSTEM})",
            "CareTeam.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="active",
        ),
        column_ref(
            "subject",
            "Who care team is for",
            "CareTeam.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    # One include per target type, so `_include=CareTeam:subject` brings in all of them and
    # `CareTeam:subject:Group` just the Groups.
    subject_includes = tuple(
        IncludeTarget("CareTeam", "subject", t, _include_column("subject", t))
        for t in SUBJECT_TYPES
    )
    participant_includes = tuple(
        IncludeTarget("CareTeam", "participant", t, _include_participant(t))
        for t in PARTICIPANT_TYPES
    )

    return SearchRegistry(
        resource_type="CareTeam",
        params={p.name: p for p in params},
        # Σ elements in the R4 CareTeam definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "category",
                "name",
                "subject",
                "encounter",
                "period",
                "participant",
                "managingOrganization",
            }
        ),
        # CareTeam has no element with min cardinality 1.
        mandatory_elements=frozenset(),
        includes=(
            IncludeTarget(
                "CareTeam", "patient", "Patient", _include_column("subject", "Patient")
            ),
            *subject_includes,
            IncludeTarget(
                "CareTeam",
                "encounter",
                "Encounter",
                _include_column("encounter", "Encounter"),
            ),
            *participant_includes,
        ),
        # A care team can name another care team as a participant (CareTeam:participant).
        revincludes=(
            *reference_consent_revincludes(
                ("actor",), "CareTeam", lambda x: x.care_team_id
            ),
            *column_task_revincludes(
                ("owner",), "owner", "CareTeam", lambda x: x.care_team_id
            ),
            *performer_report_revincludes("CareTeam", lambda x: x.care_team_id),
            *reference_observation_revincludes(
                "performer", "CareTeam", lambda x: x.care_team_id
            ),
            *performer_service_request_revincludes(
                "CareTeam", lambda x: x.care_team_id
            ),
            *column_medication_request_revincludes(
                ("intended-performer",),
                "performer",
                "CareTeam",
                lambda x: x.care_team_id,
            ),
            *reference_care_plan_revincludes(
                "care-team", "CareTeam", lambda x: x.care_team_id
            ),
            *performer_care_plan_revincludes("CareTeam", lambda x: x.care_team_id),
            IncludeTarget(
                "CareTeam",
                "participant",
                "CareTeam",
                revinclude_care_teams_via_participant(
                    "CareTeam", lambda r: r.care_team_id
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [M.care_team_id.desc()],
    )

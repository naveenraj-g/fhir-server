"""
FHIR R4 PractitionerRole search parameters
(https://www.hl7.org/fhir/R4/practitionerrole.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL,
`_sort`, `_include`, and the OpenAPI docs all come from
practitioner_role_search() below. Same arrangement as
app.repository.healthcare_service.search.

Each parameter's SQL reads only the search index (PractitionerRoleModel's
columns and child tables, see its docstring) — never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true

from app.repository._medication_statement_revinclude import column_medication_statement_revincludes
from app.repository._questionnaire_response_revinclude import (
    column_questionnaire_response_revincludes,
)
from app.repository._document_reference_revinclude import (
    column_document_reference_revincludes,
    reference_document_reference_revincludes,
)
from app.repository._care_plan_revinclude import performer_care_plan_revincludes
from app.repository._care_team_revinclude import participant_care_team_revincludes
from app.repository._group_revinclude import (
    managing_entity_group_revincludes,
    member_group_revincludes,
)
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._service_request_revinclude import (
    column_service_request_revincludes,
    performer_service_request_revincludes,
)
from app.repository._clinical_impression_revinclude import column_impression_revincludes
from app.repository._detected_issue_revinclude import column_issue_revincludes
from app.repository._specimen_revinclude import column_specimen_revincludes
from app.repository._observation_revinclude import reference_observation_revincludes
from app.repository._risk_assessment_revinclude import column_risk_revincludes
from app.repository._immunization_revinclude import performer_immunization_revincludes
from app.repository._appointment_revinclude import participant_revincludes
from app.repository._allergy_intolerance_revinclude import actor_allergy_revincludes
from app.repository._condition_revinclude import asserter_condition_revincludes
from app.repository._procedure_revinclude import performer_procedure_revincludes
from app.repository._diagnostic_report_revinclude import performer_report_revincludes
from app.repository._appointment_response_revinclude import actor_response_revincludes
from app.repository._encounter_revinclude import participant_encounter_revincludes
from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchError,
    SearchParam,
    SearchRegistry,
)
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
from app.models.practitioner_role import (
    PractitionerRoleIdentifier,
    PractitionerRoleModel,
    PractitionerRoleReference,
    PractitionerRoleTelecom,
    PractitionerRoleToken,
)

PR = PractitionerRoleModel
_I = PractitionerRoleIdentifier
_T = PractitionerRoleTelecom
_Tk = PractitionerRoleToken
_R = PractitionerRoleReference


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(
        select(literal(1)).where(model.practitioner_role_pk == PR.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per
    resource): its smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.practitioner_role_pk == PR.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(PR.updated_at, PR.created_at)


# ── _id / active / date ──────────────────────────────────────────────────────


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return PR.practitioner_role_id == int(token.code)


def _active_match(value, modifier, ctx):
    token = parse_token(value)
    if token.code not in ("true", "false") or token.system:  # boolean: no code system
        raise SearchError(value, f"'active' takes true or false, not '{value}'.")
    return PR.active.is_(token.code == "true")


def _date_match(value, modifier, ctx):
    # PractitionerRole.period is a Period: matched as a range (see period_match).
    return period_match(PR.period_start, PR.period_end, value)


# ── identifier / telecom ─────────────────────────────────────────────────────


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


def _telecom_match(system: str | None):
    """R4 token search on a ContactPoint: `code` matches `value`, the
    optional `system|` part matches `use`. `phone`/`email` also require
    ContactPoint.system to be that kind."""

    def match(value, modifier, ctx):
        condition = token_condition(_T.use, _T.value, parse_token(value))
        return (
            _exists(_T, condition, _T.system == system)
            if system
            else _exists(_T, condition)
        )

    return match


def _telecom_present(system: str | None):
    def present(ctx):
        return _exists(_T, _T.system == system) if system else _exists(_T)

    return present


# ── the two CodeableConcept token parameters (role, specialty) ───────────────


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


# ── 0..1 references held on the row: practitioner, organization ──────────────


def _single_reference(prefix: str, resource_type: str, type_enum, chain_registry):
    """(match, present, chain, sort) for a 0..1 reference stored as
    `{prefix}_reference/_type/_id/_identifier_*` columns on the row."""
    cols = {
        name: getattr(PR, f"{prefix}_{name}")
        for name in ("reference", "type", "id", "identifier_system", "identifier_value")
    }

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(
                cols["identifier_system"], cols["identifier_value"], parse_token(value)
            )
        return reference_match(
            cols["type"],
            cols["id"],
            cols["reference"],
            value,
            modifier,
            ctx,
            (resource_type,),
            type_enum,
        )

    def present(ctx):
        return or_(
            cols["reference"].is_not(None), cols["identifier_value"].is_not(None)
        )

    def chain(target, inner, ctx):
        """`<param>.<p>=v`: the referenced resource (same tenant) matches any
        of its own search parameters. The subquery doesn't correlate to the
        outer row — it ranges over the referenced resource."""
        referenced = chain_registry.ids(ctx, inner)
        return cols["id"].in_(referenced)

    return match, present, chain, lambda: cols["id"]


class _ChainTarget:
    """Lazy bridge to another resource's model for `<param>.<p>=v` chaining
    (imported on demand so the registries don't import each other at load)."""

    def __init__(self, model_path: str, model: str, id_column: str):
        self.model_path, self.model, self.id_column = model_path, model, id_column

    def ids(self, ctx, inner):
        import importlib

        model = getattr(importlib.import_module(self.model_path), self.model)
        return (
            select(getattr(model, self.id_column))
            .where(model.tenant_id == ctx.tenant_id, inner)
            .correlate(None)
        )


_PRACTITIONER = _ChainTarget(
    "app.models.practitioner", "PractitionerModel", "practitioner_id"
)
_ORGANIZATION = _ChainTarget(
    "app.models.organization", "OrganizationModel", "organization_id"
)


# ── 0..* references held in the shared reference table ───────────────────────


def _reference_param(param: str, resource_type: str, chain_target: _ChainTarget | None):
    """(match, present, chain, sort) for one of the 0..* reference parameters
    held in the shared reference table, selected by its `param` value."""

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
            # reference_type is a plain string here (the value is fixed by `param`).
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                (resource_type,),
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
        """`<param>.<p>=v`: some referenced resource (same tenant) matches
        `<p>=v`."""
        return _exists(
            _R, _R.param == param, _R.reference_id.in_(chain_target.ids(ctx, inner))
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# ── _include ─────────────────────────────────────────────────────────────────


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _include_practitioner(session, ctx, roles):
    """_include=PractitionerRole:practitioner — the practitioners."""
    from app.models.practitioner import PractitionerModel as Prac

    ids = {r.practitioner_id for r in roles if r.practitioner_id is not None}
    if not ids:
        return []
    return await _fetch(
        session,
        select(Prac).where(
            Prac.tenant_id == ctx.tenant_id, Prac.practitioner_id.in_(ids)
        ),
    )


async def _include_organization(session, ctx, roles):
    """_include=PractitionerRole:organization — the organizations."""
    from app.models.organization import OrganizationModel as Org

    ids = {r.organization_id for r in roles if r.organization_id is not None}
    if not ids:
        return []
    return await _fetch(
        session,
        select(Org).where(Org.tenant_id == ctx.tenant_id, Org.organization_id.in_(ids)),
    )


def _include_via_reference_table(
    param: str, model_path: str, model: str, id_column: str
):
    """_include=PractitionerRole:<param> — the Locations / HealthcareServices
    / Endpoints these roles point at."""

    async def fetch(session, ctx, roles):
        import importlib

        target = getattr(importlib.import_module(model_path), model)
        referenced = select(_R.reference_id).where(
            _R.practitioner_role_pk.in_({r.id for r in roles}),
            _R.param == param,
            _R.reference_id.is_not(None),
        )
        return await _fetch(
            session,
            select(target).where(
                target.tenant_id == ctx.tenant_id,
                getattr(target, id_column).in_(referenced),
            ),
        )

    return fetch


def _revinclude_schedules(resource_type: str, key):
    """_revinclude=Schedule:actor — schedules with an actor of this type
    pointing at one of these rows (matched on the public id `key(row)`)."""

    async def fetch(session, ctx, rows):
        from app.models.schedule import ScheduleActor as A
        from app.models.schedule import ScheduleModel as S

        ids = {key(r) for r in rows}
        pks = select(A.schedule_pk).where(
            A.reference_type == resource_type, A.reference_id.in_(ids)
        )
        stmt = select(S).where(S.tenant_id == ctx.tenant_id, S.id.in_(pks))
        return list((await session.execute(stmt)).scalars().all())

    return fetch


def _revinclude_patients(param: str, resource_type: str, key):
    """_revinclude=Patient:<param> — patients pointing at one of these rows
    (resolved lazily so the registries don't import each other at load)."""

    async def fetch(session, ctx, rows):
        from app.repository.patient.search import revinclude_patients_via_reference

        return await revinclude_patients_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders PractitionerRole rows —
    for PractitionerRole searches and for roles included by others."""
    from app.fhir.mappers.practitioner_role import to_fhir_practitioner_role
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "PractitionerRole",
            lambda r: r.practitioner_role_id,
            to_fhir_practitioner_role,
            "practitioner-roles",
        )
    )


# ── registry ─────────────────────────────────────────────────────────────────

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_TELECOM = frozenset({"not", "missing"})


def _search_of(module: str, factory: str):
    def get():
        import importlib

        return getattr(importlib.import_module(module), factory)()

    return get


@cache
def practitioner_role_search() -> SearchRegistry:
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

    def single(
        name,
        description,
        expression,
        example,
        prefix,
        resource_type,
        type_enum,
        chain_target,
        registry,
    ):
        match, present, chain, sort = _single_reference(
            prefix, resource_type, type_enum, chain_target
        )
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            frozenset({"identifier", "missing"}),
            targets=(resource_type,),
            chain=chain,
            chain_targets={resource_type: registry},
            sort=sort,
            example=example,
        )

    def multi(
        name, description, expression, example, resource_type, chain_target, registry
    ):
        match, present, chain, sort = _reference_param(
            name, resource_type, chain_target
        )
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            frozenset({"identifier", "missing"}),
            targets=(resource_type,),
            chain=chain if chain_target else None,
            chain_targets={resource_type: registry} if chain_target else {},
            sort=sort,
            example=example,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public practitioner role id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: PR.practitioner_role_id,
            example="140001",
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
        SearchParam(
            "active",
            "token",
            "Whether this practitioner role record is in active use",
            "PractitionerRole.active",
            _active_match,
            lambda ctx: PR.active.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: PR.active,
            example="true",
            modifier_docs={
                "not": "`:not` — active is not this value, or is not recorded at all."
            },
        ),
        SearchParam(
            "date",
            "date",
            "The period during which the practitioner is authorized to perform in these role(s)",
            "PractitionerRole.period",
            _date_match,
            lambda ctx: or_(PR.period_start.is_not(None), PR.period_end.is_not(None)),
            sort=lambda: PR.period_start,
            example="ge2026-01-01",
            modifier_docs={},
        ),
        SearchParam(
            "email",
            "token",
            "A value in an email contact (ContactPoint.value where system = email)",
            "PractitionerRole.telecom.where(system='email')",
            _telecom_match("email"),
            _telecom_present("email"),
            _TELECOM,
            example="role@example.org",
        ),
        multi(
            "endpoint",
            "Technical endpoints providing access to services operated for the practitioner with this role",
            "PractitionerRole.endpoint",
            "Endpoint/620001",
            "Endpoint",
            None,
            None,
        ),
        SearchParam(
            "identifier",
            "token",
            "A practitioner's Identifier",
            "PractitionerRole.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:roles|R-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        multi(
            "location",
            "One of the locations at which this practitioner provides care",
            "PractitionerRole.location",
            "Location/230001",
            "Location",
            _ChainTarget("app.models.location", "LocationModel", "location_id"),
            _search_of("app.repository.location.search", "location_search"),
        ),
        single(
            "organization",
            "The identity of the organization the practitioner represents / acts on behalf of",
            "PractitionerRole.organization",
            "Organization/190001",
            "organization",
            "Organization",
            str,
            _ORGANIZATION,
            _search_of("app.repository.organization.search", "organization_search"),
        ),
        SearchParam(
            "phone",
            "token",
            "A value in a phone contact (ContactPoint.value where system = phone)",
            "PractitionerRole.telecom.where(system='phone')",
            _telecom_match("phone"),
            _telecom_present("phone"),
            _TELECOM,
            example="555-0100",
        ),
        single(
            "practitioner",
            "Practitioner that is able to provide the defined services for the organization",
            "PractitionerRole.practitioner",
            "Practitioner/30001",
            "practitioner",
            "Practitioner",
            str,
            _PRACTITIONER,
            _search_of("app.repository.practitioner.search", "practitioner_search"),
        ),
        token(
            "role",
            "The practitioner can perform this role at for the organization",
            "PractitionerRole.code",
            "http://terminology.hl7.org/CodeSystem/practitioner-role|doctor",
        ),
        multi(
            "service",
            "The list of healthcare services that this worker provides for this role's Organization/Location(s)",
            "PractitionerRole.healthcareService",
            "HealthcareService/150001",
            "HealthcareService",
            _ChainTarget(
                "app.models.healthcare_service",
                "HealthcareServiceModel",
                "healthcare_service_id",
            ),
            _search_of(
                "app.repository.healthcare_service.search", "healthcare_service_search"
            ),
        ),
        token(
            "specialty",
            "The practitioner has this specialty at an organization",
            "PractitionerRole.specialty",
            "http://snomed.info/sct|394579002",
        ),
        SearchParam(
            "telecom",
            "token",
            "The value in any kind of contact (ContactPoint.value; `use|value` also matches the use)",
            "PractitionerRole.telecom",
            _telecom_match(None),
            _telecom_present(None),
            _TELECOM,
            example="555-0100",
        ),
    ]

    return SearchRegistry(
        resource_type="PractitionerRole",
        params={p.name: p for p in params},
        # Σ elements in the R4 PractitionerRole definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "active",
                "period",
                "practitioner",
                "organization",
                "code",
                "specialty",
                "location",
                "telecom",
            }
        ),
        includes=(
            IncludeTarget(
                "PractitionerRole",
                "practitioner",
                "Practitioner",
                _include_practitioner,
            ),
            IncludeTarget(
                "PractitionerRole",
                "organization",
                "Organization",
                _include_organization,
            ),
            IncludeTarget(
                "PractitionerRole",
                "location",
                "Location",
                _include_via_reference_table(
                    "location", "app.models.location", "LocationModel", "location_id"
                ),
            ),
            IncludeTarget(
                "PractitionerRole",
                "service",
                "HealthcareService",
                _include_via_reference_table(
                    "service",
                    "app.models.healthcare_service",
                    "HealthcareServiceModel",
                    "healthcare_service_id",
                ),
            ),
            IncludeTarget(
                "PractitionerRole",
                "endpoint",
                "Endpoint",
                _include_via_reference_table(
                    "endpoint", "app.models.endpoint", "EndpointModel", "endpoint_id"
                ),
            ),
        ),
        # Schedule.actor points here (Appointment, ... will add theirs when rebuilt).
        revincludes=(
            *column_medication_statement_revincludes(
                ('source',), 'source', 'PractitionerRole', lambda x: x.practitioner_role_id
            ),
            *column_questionnaire_response_revincludes(
                ("author",),
                "author",
                "PractitionerRole",
                lambda x: x.practitioner_role_id,
            ),
            *column_questionnaire_response_revincludes(
                ("source",),
                "source",
                "PractitionerRole",
                lambda x: x.practitioner_role_id,
            ),
            *column_document_reference_revincludes(
                ("authenticator",),
                "authenticator",
                "PractitionerRole",
                lambda x: x.practitioner_role_id,
            ),
            *reference_document_reference_revincludes(
                "author", "PractitionerRole", lambda x: x.practitioner_role_id
            ),
            *performer_care_plan_revincludes(
                "PractitionerRole", lambda x: x.practitioner_role_id
            ),
            *participant_care_team_revincludes(
                "PractitionerRole", lambda p: p.practitioner_role_id
            ),
            *member_group_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *managing_entity_group_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *column_medication_request_revincludes(
                ("requester",),
                "requester",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *column_medication_request_revincludes(
                ("intended-performer",),
                "performer",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *column_service_request_revincludes(
                ("requester",),
                "requester",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *performer_service_request_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *participant_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id, ("actor",)
            ),
            *actor_response_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id, ("actor",)
            ),
            *participant_encounter_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id, ("participant",)
            ),
            *actor_allergy_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *asserter_condition_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *performer_procedure_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *performer_immunization_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *performer_report_revincludes(
                "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            *column_risk_revincludes(
                ("performer",),
                "performer",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *column_impression_revincludes(
                ("assessor",),
                "assessor",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *column_issue_revincludes(
                ("author",),
                "author",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *column_specimen_revincludes(
                ("collector",),
                "collector",
                "PractitionerRole",
                lambda r: r.practitioner_role_id,
            ),
            *reference_observation_revincludes(
                "performer", "PractitionerRole", lambda r: r.practitioner_role_id
            ),
            IncludeTarget(
                "Schedule",
                "actor",
                "PractitionerRole",
                _revinclude_schedules(
                    "PractitionerRole", lambda r: r.practitioner_role_id
                ),
                reverse=True,
            ),
            # Patient.generalPractitioner points here.
            IncludeTarget(
                "Patient",
                "general-practitioner",
                "PractitionerRole",
                _revinclude_patients(
                    "general-practitioner",
                    "PractitionerRole",
                    lambda r: r.practitioner_role_id,
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [PR.practitioner_role_id.desc()],
    )

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant, fhir_telecom

if TYPE_CHECKING:
    from app.models.practitioner_role import PractitionerRoleModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on PractitionerRole (identifier.assigner, practitioner,
    organization, location, healthcareService, endpoint) — mirrors
    app.fhir.mappers.healthcare_service.fhir._fhir_reference."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(
        obj, f"{prefix}_identifier_type_user_selected", None
    )
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_coding_list(codings) -> list[dict]:
    """Render a list of FhirCodingMixin-shaped rows as a FHIR `coding[]`
    array — shared by code/specialty/identifier.type, all of which are real
    0..* child tables now — mirrors
    app.fhir.mappers.healthcare_service.fhir._fhir_coding_list."""
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def _fhir_cc(codings, text) -> dict:
    """(codings relationship, text) -> FHIR CodeableConcept dict. Shared by
    every PractitionerRole CodeableConcept-list field below."""
    coding = _fhir_coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_pr_identifier(i) -> dict:
    """PractitionerRole.identifier (Identifier) → FHIR camelCase dict.
    `type.coding[]` is a real 0..* child table (type_codings), not a single
    flattened coding — same reasoning as HealthcareServiceIdentifier's own
    type.coding[] promotion."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_cc(i.type_codings, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start),
                "end": fhir_instant(i.period_end),
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_pr_code(c) -> dict:
    return _fhir_cc(c.codings, c.text)


def fhir_pr_specialty(sp) -> dict:
    return _fhir_cc(sp.codings, sp.text)


def fhir_pr_location(loc) -> dict:
    return _fhir_reference(loc, "reference")


def fhir_pr_healthcare_service(hs) -> dict:
    return _fhir_reference(hs, "reference")


def fhir_pr_telecom(t) -> dict:
    return fhir_telecom(t)


def fhir_pr_available_time(at) -> dict:
    """`days_of_week` is a real Postgres ARRAY(Enum) column — SQLAlchemy
    hands back a list of PractitionerRoleDayOfWeek members, so each one
    goes through fhir_enum() same as any other enum-typed field."""
    entry: dict = {}
    if at.days_of_week:
        entry["daysOfWeek"] = [fhir_enum(d) for d in at.days_of_week]
    if at.all_day is not None:
        entry["allDay"] = at.all_day
    if at.available_start_time:
        entry["availableStartTime"] = at.available_start_time.isoformat()
    if at.available_end_time:
        entry["availableEndTime"] = at.available_end_time.isoformat()
    return entry


def fhir_pr_not_available(na) -> dict:
    entry: dict = {}
    if na.description:
        entry["description"] = na.description
    if na.during_start or na.during_end:
        entry["during"] = {
            k: v
            for k, v in {
                "start": fhir_instant(na.during_start),
                "end": fhir_instant(na.during_end),
            }.items()
            if v
        }
    return entry


def fhir_pr_endpoint(ep) -> dict:
    """PractitionerRole.endpoint (Reference(Endpoint)) → FHIR camelCase
    dict. Uses the shared resolved-reference-plus-fallback renderer since
    Endpoint isn't a modeled resource — the identifier fallback is often
    the only populated half."""
    return _fhir_reference(ep, "reference")


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(pr: PractitionerRoleModel) -> dict:
    """Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    rendered into Resource.meta — same convention as
    app.fhir.mappers.healthcare_service.fhir._fhir_meta. PractitionerRole
    has no user_id (see the model's docstring), so there's no equivalent of
    a user-scoped extension here."""
    meta: dict = {}
    if pr.updated_at:
        meta["lastUpdated"] = fhir_instant(pr.updated_at)

    extensions = []
    if pr.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": pr.tenant_id}
        )
    if pr.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": pr.created_by}
        )
    if pr.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": pr.updated_by}
        )
    if pr.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(pr.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_practitioner_role(pr: PractitionerRoleModel) -> dict:
    result: dict = {
        "resourceType": "PractitionerRole",
        "id": str(pr.practitioner_role_id),
    }

    meta = _fhir_meta(pr)
    if meta:
        result["meta"] = meta

    if pr.extension:
        result["extension"] = list(pr.extension)

    identifiers = [fhir_pr_identifier(i) for i in (pr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if pr.active is not None:
        result["active"] = pr.active

    if pr.period_start or pr.period_end:
        result["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(pr.period_start),
                "end": fhir_instant(pr.period_end),
            }.items()
            if v
        }

    practitioner = _fhir_reference(pr, "practitioner")
    if practitioner:
        result["practitioner"] = practitioner

    organization = _fhir_reference(pr, "organization")
    if organization:
        result["organization"] = organization

    codes = [fhir_pr_code(c) for c in (pr.codes or [])]
    codes = [c for c in codes if c]
    if codes:
        result["code"] = codes

    specialties = [fhir_pr_specialty(sp) for sp in (pr.specialties or [])]
    specialties = [sp for sp in specialties if sp]
    if specialties:
        result["specialty"] = specialties

    locations = [fhir_pr_location(loc) for loc in (pr.locations or [])]
    if locations:
        result["location"] = locations

    healthcare_services = [
        fhir_pr_healthcare_service(hs) for hs in (pr.healthcare_services or [])
    ]
    if healthcare_services:
        result["healthcareService"] = healthcare_services

    telecoms = [fhir_pr_telecom(t) for t in (pr.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    avt = [fhir_pr_available_time(at) for at in (pr.available_times or [])]
    if avt:
        result["availableTime"] = avt

    not_av = [fhir_pr_not_available(na) for na in (pr.not_available or [])]
    if not_av:
        result["notAvailable"] = not_av

    if pr.availability_exceptions:
        result["availabilityExceptions"] = pr.availability_exceptions

    endpoints = [fhir_pr_endpoint(ep) for ep in (pr.endpoints or [])]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.schedule import ScheduleModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Schedule (identifier.assigner, actor) —
    mirrors app.fhir.mappers.practitioner_role.fhir._fhir_reference."""
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
    array — shared by serviceCategory/serviceType/specialty/identifier.type,
    all real 0..* child tables now — mirrors
    app.fhir.mappers.practitioner_role.fhir._fhir_coding_list."""
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
    every Schedule CodeableConcept-list field below."""
    coding = _fhir_coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_sch_identifier(i) -> dict:
    """Schedule.identifier (Identifier) → FHIR camelCase dict. `type.coding[]`
    is a real 0..* child table (type_codings), not a single flattened
    coding — same reasoning as PractitionerRoleIdentifier's own
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


def fhir_sch_service_category(sc) -> dict:
    return _fhir_cc(sc.codings, sc.text)


def fhir_sch_service_type(st) -> dict:
    return _fhir_cc(st.codings, st.text)


def fhir_sch_specialty(sp) -> dict:
    return _fhir_cc(sp.codings, sp.text)


def fhir_sch_actor(a) -> dict:
    return _fhir_reference(a, "reference")


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(sch: ScheduleModel) -> dict:
    """Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    rendered into Resource.meta — same convention as
    app.fhir.mappers.practitioner_role.fhir._fhir_meta. Schedule has no
    user_id (see the model's docstring), so there's no equivalent of a
    user-scoped extension here."""
    meta: dict = {}
    if sch.updated_at:
        meta["lastUpdated"] = fhir_instant(sch.updated_at)

    extensions = []
    if sch.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": sch.tenant_id}
        )
    if sch.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": sch.created_by}
        )
    if sch.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": sch.updated_by}
        )
    if sch.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(sch.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_schedule(sch: ScheduleModel) -> dict:
    result: dict = {
        "resourceType": "Schedule",
        "id": str(sch.schedule_id),
    }

    meta = _fhir_meta(sch)
    if meta:
        result["meta"] = meta

    identifiers = [fhir_sch_identifier(i) for i in (sch.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if sch.active is not None:
        result["active"] = sch.active

    service_categories = [
        fhir_sch_service_category(sc) for sc in (sch.service_categories or [])
    ]
    service_categories = [sc for sc in service_categories if sc]
    if service_categories:
        result["serviceCategory"] = service_categories

    service_types = [fhir_sch_service_type(st) for st in (sch.service_types or [])]
    service_types = [st for st in service_types if st]
    if service_types:
        result["serviceType"] = service_types

    specialties = [fhir_sch_specialty(sp) for sp in (sch.specialties or [])]
    specialties = [sp for sp in specialties if sp]
    if specialties:
        result["specialty"] = specialties

    actors = [fhir_sch_actor(a) for a in (sch.actors or [])]
    if actors:
        result["actor"] = actors

    if sch.planning_horizon_start or sch.planning_horizon_end:
        result["planningHorizon"] = {
            k: v
            for k, v in {
                "start": fhir_instant(sch.planning_horizon_start),
                "end": fhir_instant(sch.planning_horizon_end),
            }.items()
            if v
        }

    if sch.comment:
        result["comment"] = sch.comment

    return {k: v for k, v in result.items() if v is not None}

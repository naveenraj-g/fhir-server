from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.appointment_response import AppointmentResponseModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on AppointmentResponse (identifier.assigner,
    appointment, actor) — mirrors app.fhir.mappers.appointment.fhir._fhir_reference."""
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
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
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
    array — mirrors app.fhir.mappers.appointment.fhir._fhir_coding_list."""
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
    """(codings relationship, text) -> FHIR CodeableConcept dict."""
    coding = _fhir_coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_appointment_response_identifier(i) -> dict:
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


def fhir_appointment_response_participant_type(pt) -> dict:
    return _fhir_cc(pt.codings, pt.text)


# AppointmentResponseParticipantStatus's member .value intentionally equals
# its underscore-only member .name (same reasoning as AppointmentStatus/
# SlotStatus) — the real hyphenated FHIR wire code (`needs-action`) is
# derived here.
def _fhir_status(status) -> str | None:
    value = fhir_enum(status)
    return value.replace("_", "-") if value else value


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(appointment_response: AppointmentResponseModel) -> dict:
    """Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    rendered into Resource.meta — same convention as
    app.fhir.mappers.appointment.fhir._fhir_meta. AppointmentResponse has
    no user_id (see the model's docstring), so there's no equivalent of a
    user-scoped extension here."""
    meta: dict = {}
    if appointment_response.updated_at:
        meta["lastUpdated"] = fhir_instant(appointment_response.updated_at)

    extensions = []
    if appointment_response.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": appointment_response.tenant_id}
        )
    if appointment_response.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": appointment_response.created_by}
        )
    if appointment_response.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": appointment_response.updated_by}
        )
    if appointment_response.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(appointment_response.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_appointment_response(appointment_response: AppointmentResponseModel) -> dict:
    result: dict = {
        "resourceType": "AppointmentResponse",
        "id": str(appointment_response.appointment_response_id),
    }

    meta = _fhir_meta(appointment_response)
    if meta:
        result["meta"] = meta

    if appointment_response.extension:
        result["extension"] = list(appointment_response.extension)

    identifiers = [
        fhir_appointment_response_identifier(i)
        for i in (appointment_response.identifiers or [])
    ]
    if identifiers:
        result["identifier"] = identifiers

    appointment = _fhir_reference(appointment_response, "appointment")
    if appointment:
        result["appointment"] = appointment

    if appointment_response.start:
        result["start"] = fhir_instant(appointment_response.start)
    if appointment_response.end:
        result["end"] = fhir_instant(appointment_response.end)

    participant_types = [
        fhir_appointment_response_participant_type(pt)
        for pt in (appointment_response.participant_types or [])
    ]
    participant_types = [pt for pt in participant_types if pt]
    if participant_types:
        result["participantType"] = participant_types

    actor = _fhir_reference(appointment_response, "actor")
    if actor:
        result["actor"] = actor

    status = _fhir_status(appointment_response.participant_status)
    if status:
        result["participantStatus"] = status

    if appointment_response.comment:
        result["comment"] = appointment_response.comment

    return {k: v for k, v in result.items() if v is not None}

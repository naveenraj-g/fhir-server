from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.encounter import EncounterModel


def _audit_fields(obj) -> dict:
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        **_audit_fields(c),
    }


def _plain_single_coding_fields(obj, output_prefix: str) -> dict:
    """Flat `{output_prefix}system`/`{output_prefix}version`/`{output_prefix}code`/
    `{output_prefix}display`/`{output_prefix}user_selected` OUTPUT dict
    keys for a bare-Coding embed (Encounter.class / Encounter.classHistory.class)
    — `output_prefix` (e.g. "class_") only shapes the *returned dict's
    keys*, matching PlainEncounterResponse's own `class_system` etc.
    field names. It is NOT used to read `obj`: FhirCodingMixin's
    `_coding_prefix` only renames the underlying DB column, never the
    Python attribute, so `obj.system` (bare) is always the right read —
    see app.repository.encounter.full._single_coding_kwargs's docstring
    for the full reasoning (and the TypeError that first caught this)."""
    return {
        f"{output_prefix}system": obj.system,
        f"{output_prefix}version": obj.version,
        f"{output_prefix}code": obj.code,
        f"{output_prefix}display": obj.display,
        f"{output_prefix}user_selected": obj.user_selected,
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        prefix: f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(getattr(obj, f"{prefix}_identifier_use", None)),
        f"{prefix}_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        f"{prefix}_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        f"{prefix}_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        f"{prefix}_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        f"{prefix}_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat() if id_period_start else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat() if id_period_end else None,
    }


def plain_encounter_identifier(i) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_encounter_status_history(sh) -> dict:
    return {
        "id": sh.id,
        "status": fhir_enum(sh.status),
        "period_start": sh.period_start.isoformat() if sh.period_start else None,
        "period_end": sh.period_end.isoformat() if sh.period_end else None,
        **_audit_fields(sh),
    }


def plain_encounter_class_history(ch) -> dict:
    return {
        "id": ch.id,
        **_plain_single_coding_fields(ch, "class_"),
        "period_start": ch.period_start.isoformat() if ch.period_start else None,
        "period_end": ch.period_end.isoformat() if ch.period_end else None,
        **_audit_fields(ch),
    }


def _plain_cc_row(obj) -> dict:
    return {
        "id": obj.id,
        "codings": [plain_coding(x) for x in (obj.codings or [])],
        "text": obj.text,
        **_audit_fields(obj),
    }


def plain_encounter_type(t) -> dict:
    return _plain_cc_row(t)


def plain_encounter_reason_code(rc) -> dict:
    return _plain_cc_row(rc)


def _plain_reference_row(obj) -> dict:
    return {
        "id": obj.id,
        **_plain_reference_fields(obj, "reference"),
        **_audit_fields(obj),
    }


def plain_encounter_episode_of_care(eoc) -> dict:
    return _plain_reference_row(eoc)


def plain_encounter_based_on(bo) -> dict:
    return _plain_reference_row(bo)


def plain_encounter_appointment(ap) -> dict:
    return _plain_reference_row(ap)


def plain_encounter_reason_reference(rr) -> dict:
    return _plain_reference_row(rr)


def plain_encounter_account(ac) -> dict:
    return _plain_reference_row(ac)


def plain_encounter_participant_type(pt) -> dict:
    return _plain_cc_row(pt)


def plain_encounter_participant(p) -> dict:
    return {
        "id": p.id,
        "types": [plain_encounter_participant_type(t) for t in (p.types or [])],
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
        **_plain_reference_fields(p, "individual"),
        **_audit_fields(p),
    }


def plain_encounter_diagnosis(d) -> dict:
    return {
        "id": d.id,
        **_plain_reference_fields(d, "condition"),
        "use_codings": [plain_coding(c) for c in (d.use_codings or [])],
        "use_text": d.use_text,
        "rank": d.rank,
        **_audit_fields(d),
    }


def plain_encounter_hospitalization_diet_preference(dp) -> dict:
    return _plain_cc_row(dp)


def plain_encounter_hospitalization_special_courtesy(sc) -> dict:
    return _plain_cc_row(sc)


def plain_encounter_hospitalization_special_arrangement(sa) -> dict:
    return _plain_cc_row(sa)


def plain_encounter_hospitalization(h) -> dict:
    return {
        "id": h.id,
        "pre_admission_identifier_use": fhir_enum(h.pre_admission_identifier_use),
        "pre_admission_identifier_type_codings": [
            plain_coding(c) for c in (h.pre_admission_identifier_type_codings or [])
        ],
        "pre_admission_identifier_type_text": h.pre_admission_identifier_type_text,
        "pre_admission_identifier_system": h.pre_admission_identifier_system,
        "pre_admission_identifier_value": h.pre_admission_identifier_value,
        "pre_admission_identifier_period_start": h.pre_admission_identifier_period_start.isoformat()
        if h.pre_admission_identifier_period_start else None,
        "pre_admission_identifier_period_end": h.pre_admission_identifier_period_end.isoformat()
        if h.pre_admission_identifier_period_end else None,
        **_plain_reference_fields(h, "pre_admission_identifier_assigner"),
        **_plain_reference_fields(h, "origin"),
        "admit_source_codings": [plain_coding(c) for c in (h.admit_source_codings or [])],
        "admit_source_text": h.admit_source_text,
        "re_admission_codings": [plain_coding(c) for c in (h.re_admission_codings or [])],
        "re_admission_text": h.re_admission_text,
        "diet_preference": [
            plain_encounter_hospitalization_diet_preference(dp) for dp in (h.diet_preferences or [])
        ],
        "special_courtesy": [
            plain_encounter_hospitalization_special_courtesy(sc) for sc in (h.special_courtesies or [])
        ],
        "special_arrangement": [
            plain_encounter_hospitalization_special_arrangement(sa) for sa in (h.special_arrangements or [])
        ],
        **_plain_reference_fields(h, "destination"),
        "discharge_disposition_codings": [
            plain_coding(c) for c in (h.discharge_disposition_codings or [])
        ],
        "discharge_disposition_text": h.discharge_disposition_text,
        **_audit_fields(h),
    }


def plain_encounter_location(loc) -> dict:
    return {
        "id": loc.id,
        **_plain_reference_fields(loc, "location"),
        "status": fhir_enum(loc.status),
        "physical_type_codings": [plain_coding(c) for c in (loc.physical_type_codings or [])],
        "physical_type_text": loc.physical_type_text,
        "period_start": loc.period_start.isoformat() if loc.period_start else None,
        "period_end": loc.period_end.isoformat() if loc.period_end else None,
        **_audit_fields(loc),
    }


def to_plain_encounter(encounter: EncounterModel) -> dict:
    return {
        "id": encounter.encounter_id,
        "extension": encounter.extension or [],
        "status": fhir_enum(encounter.status),
        **_plain_single_coding_fields(encounter, "class_"),
        "service_type_codings": [plain_coding(c) for c in (encounter.service_type_codings or [])],
        "service_type_text": encounter.service_type_text,
        "priority_codings": [plain_coding(c) for c in (encounter.priority_codings or [])],
        "priority_text": encounter.priority_text,
        **_plain_reference_fields(encounter, "subject"),
        "period_start": encounter.period_start.isoformat() if encounter.period_start else None,
        "period_end": encounter.period_end.isoformat() if encounter.period_end else None,
        "length_value": str(encounter.length_value) if encounter.length_value is not None else None,
        "length_comparator": fhir_enum(encounter.length_comparator),
        "length_unit": encounter.length_unit,
        "length_system": encounter.length_system,
        "length_code": encounter.length_code,
        **_plain_reference_fields(encounter, "service_provider"),
        **_plain_reference_fields(encounter, "part_of"),
        "identifier": [plain_encounter_identifier(i) for i in (encounter.identifiers or [])],
        "status_history": [plain_encounter_status_history(sh) for sh in (encounter.status_history or [])],
        "class_history": [plain_encounter_class_history(ch) for ch in (encounter.class_history or [])],
        "type": [plain_encounter_type(t) for t in (encounter.types or [])],
        "episode_of_care": [plain_encounter_episode_of_care(eoc) for eoc in (encounter.episode_of_cares or [])],
        "based_on": [plain_encounter_based_on(bo) for bo in (encounter.based_ons or [])],
        "appointment": [plain_encounter_appointment(ap) for ap in (encounter.appointments or [])],
        "reason_code": [plain_encounter_reason_code(rc) for rc in (encounter.reason_codes or [])],
        "reason_reference": [
            plain_encounter_reason_reference(rr) for rr in (encounter.reason_references or [])
        ],
        "account": [plain_encounter_account(ac) for ac in (encounter.accounts or [])],
        "participant": [plain_encounter_participant(p) for p in (encounter.participants or [])],
        "diagnosis": [plain_encounter_diagnosis(d) for d in (encounter.diagnoses or [])],
        "hospitalization": plain_encounter_hospitalization(encounter.hospitalization)
        if encounter.hospitalization else None,
        "location": [plain_encounter_location(loc) for loc in (encounter.locations or [])],
        "org_id": encounter.tenant_id,
        "created_at": encounter.created_at.isoformat() if encounter.created_at else None,
        "updated_at": encounter.updated_at.isoformat() if encounter.updated_at else None,
        "created_by": encounter.created_by,
        "updated_by": encounter.updated_by,
    }

"""FHIR R4 conformance for `to_fhir_encounter()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Encounter is stored Medplum-style (like Appointment, AppointmentResponse, Slot,
Patient and the other content-based resources): the resource lives whole in
EncounterModel.content, and to_fhir_encounter() only stamps `id` and `meta` onto
it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 — each
case below is a `content` document as the write path would store it, run through
the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.encounter import to_fhir_encounter
from app.models.encounter import EncounterModel

from .support import assert_valid, fhir_json_text

encounter_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.encounter_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
ACT = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
CLASS = {"system": ACT, "code": "AMB", "display": "ambulatory"}


def _encounter(content: dict, **overrides) -> EncounterModel:
    fields = {
        "encounter_id": 20001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return EncounterModel(**fields)


def _with(**elements) -> EncounterModel:
    return _encounter({"status": "in-progress", "class": CLASS, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _encounter(
        {"status": "finished", "class": CLASS}, updated_by="u-other", updated_at=D
    ),
    **{
        f"status_{s}": _with(status=s)
        for s in (
            "planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled", "entered-in-error",
            "unknown",
        )
    },
    "class_with_version_and_user_selected": _with(
        **{"class": {"system": ACT, "version": "2.0", "code": "IMP", "display": "inpatient", "userSelected": True}}
    ),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "VN"}]},
                "system": "http://hospital.example.org/encounters",
                "value": "E-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "status_history": _with(
        statusHistory=[
            {"status": "planned", "period": {"start": "2026-05-30T08:00:00Z", "end": "2026-06-01T09:00:00Z"}},
            {"status": "in-progress", "period": {"start": "2026-06-01T09:00:00Z"}},
        ]
    ),
    "class_history": _with(
        classHistory=[{"class": {"system": ACT, "code": "EMER"}, "period": {"start": "2026-05-30T08:00:00Z"}}]
    ),
    "type_and_service_type_and_priority": _with(
        type=[{"coding": [{"system": "http://snomed.info/sct", "code": "270427003"}], "text": "Initial"}],
        serviceType={"coding": [{"system": "http://terminology.hl7.org/CodeSystem/service-type", "code": "124"}]},
        priority={"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority", "code": "R"}]},
    ),
    "several_types": _with(type=[{"text": "a"}, {"coding": [{"code": "x"}]}]),
    "subject_patient": _with(subject={"reference": "Patient/10001", "display": "A. Patient"}),
    "subject_group": _with(subject={"reference": "Group/1"}),
    "subject_logical": _with(subject={"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "Ext"}),
    "subject_absolute_url": _with(subject={"reference": "https://other.example.org/fhir/Patient/9"}),
    "episode_of_care_and_based_on": _with(
        episodeOfCare=[{"reference": "EpisodeOfCare/350001"}], basedOn=[{"reference": "ServiceRequest/80001"}]
    ),
    "participant": _with(
        participant=[
            {
                "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType", "code": "ATND"}]}],
                "period": {"start": "2026-06-01T09:00:00Z"},
                "individual": {"reference": "Practitioner/30001", "display": "Dr Careful"},
            },
            {"individual": {"reference": "RelatedPerson/5"}},
            {"individual": {"identifier": {"system": "urn:staff", "value": "S-1"}}},
        ]
    ),
    "appointment": _with(appointment=[{"reference": "Appointment/40001"}]),
    "period": _with(period={"start": "2026-06-01T09:00:00Z", "end": "2026-06-01T09:40:00Z"}),
    "period_open_ended": _with(period={"start": "2026-06-01T09:00:00Z"}),
    "length_with_comparator": _with(
        length={"value": 2.5, "comparator": ">", "unit": "d", "system": "http://unitsofmeasure.org", "code": "d"}
    ),
    "reason_code_and_reference": _with(
        reasonCode=[{"coding": [{"system": "http://snomed.info/sct", "code": "185347001"}], "text": "Check-up"}],
        reasonReference=[{"reference": "Condition/120001"}, {"reference": "Observation/5"}],
    ),
    "diagnosis": _with(
        diagnosis=[
            {
                "condition": {"reference": "Condition/120001"},
                "use": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/diagnosis-role", "code": "AD"}]},
                "rank": 1,
            }
        ]
    ),
    "account": _with(account=[{"reference": "Account/7"}]),
    "hospitalization": _with(
        hospitalization={
            "preAdmissionIdentifier": {"system": "urn:pre", "value": "PRE-1", "assigner": {"reference": "Organization/190001"}},
            "origin": {"reference": "Location/230001"},
            "admitSource": {"text": "Referral"},
            "reAdmission": {"text": "Re-admission"},
            "dietPreference": [{"text": "Vegetarian"}],
            "specialCourtesy": [{"text": "VIP"}],
            "specialArrangement": [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-EncounterSpecialCourtesy", "code": "wheel"}]}
            ],
            "destination": {"reference": "Organization/190001"},
            "dischargeDisposition": {"text": "Home"},
        }
    ),
    "location": _with(
        location=[
            {
                "location": {"reference": "Location/230001"},
                "status": "completed",
                "physicalType": {"text": "Room"},
                "period": {"start": "2026-06-01T09:00:00Z", "end": "2026-06-01T09:30:00Z"},
            },
            {"location": {"reference": "Location/230002"}},
        ]
    ),
    **{f"location_status_{s}": _with(location=[{"location": {"reference": "Location/1"}, "status": s}])
       for s in ("planned", "active", "reserved", "completed")},
    "service_provider_and_part_of": _with(
        serviceProvider={"reference": "Organization/190001"}, partOf={"reference": "Encounter/20000"}
    ),
    "extension": _with(extension=[{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_encounter_mapper_emits_valid_fhir_r4(case):
    assert_valid(encounter_pb2.Encounter, to_fhir_encounter(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "finished", "class": CLASS, "period": {"start": "2026-06-01T09:00:00Z"}}
    out = to_fhir_encounter(_encounter(content))
    assert out["resourceType"] == "Encounter"
    assert out["id"] == "20001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `class` or `hospitalization` as a one-item list —
# and an unknown code for `status`; the integration tests cover those.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"statuss": "x"}),
        ("class as CodeableConcept", {"class": {"coding": [{"code": "AMB"}]}}),
        ("status as number", {"status": 1}),
        ("period start not a dateTime", {"period": {"start": "tomorrow"}}),
        ("length as string", {"length": "2 days"}),
        ("length comparator not a code", {"length": {"value": 1, "comparator": "!="}}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("participant as object not a list", {"participant": {"individual": {"reference": "Practitioner/1"}}}),
        ("diagnosis rank as string", {"diagnosis": [{"condition": {"reference": "Condition/1"}, "rank": "first"}]}),
        ("location status not a code", {"location": [{"location": {"reference": "Location/1"}, "status": "broken"}]}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Encounter", "id": "20001", "status": "in-progress", "class": CLASS, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(fhir_json_text(payload), encounter_pb2.Encounter, validate=True)

"""FHIR R4 conformance for `to_fhir_allergy_intolerance()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

AllergyIntolerance is stored Medplum-style (like Patient, Appointment, Encounter
and the other content-based resources): the resource lives whole in
AllergyIntoleranceModel.content, and to_fhir_allergy_intolerance() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that stamping
(e.g. a malformed meta extension) or a stored document the server returns that
isn't valid R4 — each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.allergy_intolerance import to_fhir_allergy_intolerance
from app.models.allergy_intolerance import AllergyIntoleranceModel

from .support import assert_valid, fhir_json_text

allergy_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.allergy_intolerance_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
PATIENT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"
CLIN = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
VERIF = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"


def _allergy(content: dict, **overrides) -> AllergyIntoleranceModel:
    fields = {
        "allergy_intolerance_id": 260001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return AllergyIntoleranceModel(**fields)


def _with(**elements) -> AllergyIntoleranceModel:
    return _allergy({"patient": PATIENT, **elements})


REACTION = {
    "substance": {
        "coding": [{"system": SCT, "code": "227493005", "display": "Cashew nuts"}],
        "text": "Cashew",
    },
    "manifestation": [
        {"coding": [{"system": SCT, "code": "64305001", "display": "Urticaria"}]},
        {"text": "Rash"},
    ],
    "description": "Severe hives",
    "onset": "2023-01-15T09:40:00Z",
    "severity": "severe",
    "exposureRoute": {"coding": [{"system": SCT, "code": "26643006"}]},
    "note": [
        {
            "authorString": "Nurse",
            "time": "2023-01-15T10:00:00Z",
            "text": "Resolved after epinephrine.",
        }
    ],
}

CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _allergy(
        {"patient": PATIENT}, updated_by="u-other", updated_at=D
    ),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PRN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/allergy-id",
                "value": "AI-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "clinical_status": _with(
        clinicalStatus={"coding": [{"system": CLIN, "code": "active"}]}
    ),
    **{
        f"clinical_status_{c}": _with(
            clinicalStatus={"coding": [{"system": CLIN, "code": c}]},
            verificationStatus={"coding": [{"system": VERIF, "code": "confirmed"}]},
        )
        for c in ("active", "inactive", "resolved")
    },
    **{
        f"verification_status_{v}": _with(
            verificationStatus={"coding": [{"system": VERIF, "code": v}]},
            **(
                {}
                if v == "entered-in-error"
                else {
                    "clinicalStatus": {"coding": [{"system": CLIN, "code": "active"}]}
                }
            ),
        )
        for v in ("unconfirmed", "confirmed", "refuted", "entered-in-error")
    },
    **{f"type_{t}": _with(type=t) for t in ("allergy", "intolerance")},
    "category_all": _with(category=["food", "medication", "environment", "biologic"]),
    **{
        f"criticality_{c}": _with(criticality=c)
        for c in ("low", "high", "unable-to-assess")
    },
    "code": _with(
        code={
            "coding": [{"system": SCT, "code": "227493005", "display": "Cashew nuts"}],
            "text": "Cashew",
        }
    ),
    "patient_with_display": _with(
        patient={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "patient_logical": _allergy(
        {"patient": {"identifier": {"system": "urn:pts", "value": "P-9"}}}
    ),
    "patient_absolute_url": _allergy(
        {"patient": {"reference": "https://other.example.org/fhir/Patient/9"}}
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "onset_date_time": _with(onsetDateTime="2023-01-15T09:30:00Z"),
    "onset_date_time_partial": _with(onsetDateTime="2023-01"),
    "onset_age": _with(
        onsetAge={
            "value": 12,
            "unit": "years",
            "system": "http://unitsofmeasure.org",
            "code": "a",
        }
    ),
    "onset_period": _with(onsetPeriod={"start": "2020-01-01", "end": "2020-02-01"}),
    "onset_range": _with(
        onsetRange={
            "low": {"value": 5, "unit": "years"},
            "high": {"value": 10, "unit": "years"},
        }
    ),
    "onset_string": _with(onsetString="as a child"),
    "recorded_date": _with(recordedDate="2023-01-15T10:00:00Z"),
    **{
        f"recorder_{t}": _with(recorder={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    **{
        f"asserter_{t}": _with(asserter={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    "asserter_logical": _with(
        asserter={"identifier": {"system": "urn:who", "value": "W-1"}}
    ),
    "last_occurrence": _with(lastOccurrence="2023-06-01T12:00:00Z"),
    "note_author_reference": _with(
        note=[
            {
                "authorReference": {"reference": "Practitioner/30001"},
                "time": "2023-01-15T10:05:00Z",
                "text": "Hives",
            }
        ]
    ),
    "note_author_string": _with(note=[{"authorString": "Dr Smith", "text": "Hives"}]),
    "reaction": _with(reaction=[REACTION]),
    "reaction_minimal": _with(reaction=[{"manifestation": [{"text": "Rash"}]}]),
    "reactions_two": _with(
        reaction=[REACTION, {"manifestation": [{"text": "Nausea"}], "severity": "mild"}]
    ),
    **{
        f"reaction_severity_{s}": _with(
            reaction=[{"manifestation": [{"text": "x"}], "severity": s}]
        )
        for s in ("mild", "moderate", "severe")
    },
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:ai", "value": "AI-1"}],
        clinicalStatus={"coding": [{"system": CLIN, "code": "active"}]},
        verificationStatus={"coding": [{"system": VERIF, "code": "confirmed"}]},
        type="allergy",
        category=["food"],
        criticality="high",
        code={"coding": [{"system": SCT, "code": "227493005"}]},
        encounter={"reference": "Encounter/20001"},
        onsetDateTime="2023-01-15T09:30:00Z",
        recordedDate="2023-01-15T10:00:00Z",
        recorder={"reference": "Practitioner/30001"},
        asserter={"reference": "Patient/10001"},
        lastOccurrence="2023-06-01T12:00:00Z",
        note=[{"text": "Hives"}],
        reaction=[REACTION],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_allergy_intolerance_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(CASES[case])
    )


def test_mapper_serves_content_unchanged():
    content = {
        "patient": PATIENT,
        "type": "allergy",
        "category": ["food"],
        "criticality": "high",
    }
    out = to_fhir_allergy_intolerance(_allergy(content))
    assert out["resourceType"] == "AllergyIntolerance"
    assert out["id"] == "260001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient` as a one-item list — and rules ait-1 /
# ait-2, which tie clinicalStatus to verificationStatus; the integration tests
# cover what they can and the java_validator backend enforces the rest.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "allergy"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        (
            "clinicalStatus as string not a CodeableConcept",
            {"clinicalStatus": "active"},
        ),
        ("category as string not a list", {"category": "food"}),
        ("category with an unknown code", {"category": ["cosmic"]}),
        ("type as number", {"type": 1}),
        ("type with an unknown code", {"type": "robot"}),
        ("criticality with an unknown code", {"criticality": "extreme"}),
        ("recordedDate not a dateTime", {"recordedDate": "tomorrow"}),
        ("onsetDateTime not a dateTime", {"onsetDateTime": "yesterday"}),
        ("lastOccurrence not a dateTime", {"lastOccurrence": "soon"}),
        ("reaction as object not a list", {"reaction": {"severity": "mild"}}),
        (
            "reaction severity with an unknown code",
            {"reaction": [{"manifestation": [{"text": "x"}], "severity": "dire"}]},
        ),
        (
            "manifestation as object not a list",
            {"reaction": [{"manifestation": {"text": "x"}}]},
        ),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("onsetAge value as string", {"onsetAge": {"value": "twelve"}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "AllergyIntolerance",
        "id": "260001",
        "patient": PATIENT,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), allergy_pb2.AllergyIntolerance, validate=True
        )

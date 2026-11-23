"""FHIR R4 conformance for `to_fhir_questionnaire_response()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

QuestionnaireResponse is stored whole in `content` (like CareTeam, CarePlan, Encounter and the
other content-based resources): the resource lives in QuestionnaireResponseModel.content, and
to_fhir_questionnaire_response() only stamps `id` and `meta` onto it. So what can go wrong on the
read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 - each case below is a `content` document as the write path would store
it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.questionnaire_response import to_fhir_questionnaire_response
from app.models.questionnaire_response import QuestionnaireResponseModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.questionnaire_response_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"


def _c(content: dict, **overrides) -> QuestionnaireResponseModel:
    fields = {
        "questionnaire_response_id": 60001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return QuestionnaireResponseModel(**fields)


def _base(**extra) -> dict:
    return {"status": "completed", **extra}


def _answers(*answers) -> dict:
    return _base(item=[{"linkId": "1", "answer": list(answers)}])


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in ("in-progress", "completed", "amended", "entered-in-error", "stopped")
    },
    "identifier": _c(
        _base(
            identifier={
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "ACSN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-response-id",
                "value": "QR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        )
    ),
    "references": _c(
        _base(
            basedOn=[
                {"reference": "CarePlan/290001"},
                {"reference": "ServiceRequest/80001"},
            ],
            partOf=[
                {"reference": "Observation/160001"},
                {"reference": "Procedure/100001"},
            ],
            subject={"reference": "Patient/10001"},
            encounter={"reference": "Encounter/20001"},
            author={"reference": "Practitioner/30001"},
            source={"reference": "Patient/10001"},
        )
    ),
    "subject_any_resource": _c(_base(subject={"reference": "Observation/160001"})),
    "subject_absolute_url": _c(
        _base(subject={"reference": "https://other.example.org/fhir/Patient/1"})
    ),
    "subject_logical_identifier": _c(
        _base(subject={"identifier": {"system": "urn:mrn", "value": "M-1"}})
    ),
    "authored_and_questionnaire": _c(
        _base(
            authored="2026-02-01T10:00:00Z",
            questionnaire="https://fhir-server.dev/fhir/Questionnaire/phq-9|1.0",
        )
    ),
    "nested_items": _c(
        _base(
            item=[
                {
                    "linkId": "1",
                    "text": "Mood",
                    "definition": "http://example.org/definitions/mood",
                    "item": [
                        {"linkId": "1.1", "answer": [{"valueInteger": 2}]},
                        {"linkId": "1.2", "item": [{"linkId": "1.2.1"}]},
                    ],
                }
            ]
        )
    ),
    "answer_boolean": _c(_answers({"valueBoolean": False})),
    "answer_decimal": _c(_answers({"valueDecimal": 3.25})),
    "answer_integer": _c(_answers({"valueInteger": 2})),
    "answer_date": _c(_answers({"valueDate": "2026-01-05"})),
    "answer_date_time": _c(_answers({"valueDateTime": "2026-01-05T08:30:00Z"})),
    "answer_time": _c(_answers({"valueTime": "08:30:00"})),
    "answer_string": _c(_answers({"valueString": "free text"})),
    "answer_uri": _c(_answers({"valueUri": "http://example.org/x"})),
    "answer_attachment": _c(
        _answers(
            {
                "valueAttachment": {
                    "contentType": "application/pdf",
                    "url": "https://documents.example.org/scan.pdf",
                    "title": "Scan",
                }
            }
        )
    ),
    "answer_coding": _c(
        _answers(
            {"valueCoding": {"system": SCT, "code": "373066001", "display": "Yes"}}
        )
    ),
    "answer_quantity": _c(
        _answers(
            {
                "valueQuantity": {
                    "value": 72.5,
                    "comparator": ">",
                    "unit": "kg",
                    "system": "http://unitsofmeasure.org",
                    "code": "kg",
                }
            }
        )
    ),
    "answer_reference": _c(
        _answers({"valueReference": {"reference": "Observation/160001"}})
    ),
    "answer_with_nested_item": _c(
        _answers(
            {
                "valueCoding": {"system": SCT, "code": "373066001"},
                "item": [{"linkId": "1.1", "answer": [{"valueString": "why"}]}],
            }
        )
    ),
    "several_answers": _c(
        _answers({"valueString": "a"}, {"valueString": "b"}, {"valueInteger": 3})
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_questionnaire_response_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.QuestionnaireResponse, to_fhir_questionnaire_response(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(item=[{"linkId": "1", "answer": [{"valueString": "x"}]}])
    out = to_fhir_questionnaire_response(_c(content))
    assert out["resourceType"] == "QuestionnaireResponse"
    assert out["id"] == "60001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `identifier` or `subject` as a one-item list - and the old
# underscore spelling `in_progress`, which the library accepts; the integration tests cover
# both.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("identifier as list", {"identifier": [{"value": "x"}]}),
        ("basedOn as object not a list", {"basedOn": {"reference": "CarePlan/1"}}),
        ("basedOn entry as string", {"basedOn": ["CarePlan/1"]}),
        ("partOf as object not a list", {"partOf": {"reference": "Observation/1"}}),
        (
            "questionnaire as object",
            {"questionnaire": {"reference": "Questionnaire/1"}},
        ),
        ("subject as string", {"subject": "Patient/1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("authored as number", {"authored": 5}),
        ("authored not a dateTime", {"authored": "yesterday"}),
        ("author as list", {"author": [{"reference": "Practitioner/1"}]}),
        ("source as string", {"source": "Patient/1"}),
        ("item as object not a list", {"item": {"linkId": "1"}}),
        ("item entry as string", {"item": ["x"]}),
        ("item linkId as number", {"item": [{"linkId": 1}]}),
        (
            "answer as object not a list",
            {"item": [{"linkId": "1", "answer": {"valueString": "x"}}]},
        ),
        (
            "answer valueInteger as string",
            {"item": [{"linkId": "1", "answer": [{"valueInteger": "two"}]}]},
        ),
        (
            "answer valueBoolean as string",
            {"item": [{"linkId": "1", "answer": [{"valueBoolean": "yes"}]}]},
        ),
        (
            "answer valueCoding as string",
            {"item": [{"linkId": "1", "answer": [{"valueCoding": "x"}]}]},
        ),
        (
            "answer valueDate not a date",
            {"item": [{"linkId": "1", "answer": [{"valueDate": "tomorrow"}]}]},
        ),
        (
            "answer item as object",
            {"item": [{"linkId": "1", "answer": [{"item": {"linkId": "2"}}]}]},
        ),
        (
            "nested item as string",
            {"item": [{"linkId": "1", "item": [{"linkId": "2", "item": "x"}]}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "QuestionnaireResponse", "id": "60001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.QuestionnaireResponse, validate=True
        )

"""FHIR R4 conformance for `to_fhir_questionnaire()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Questionnaire is stored whole in `content` (like QuestionnaireResponse, CareTeam, CarePlan and the
other content-based resources): the resource lives in QuestionnaireModel.content, and
to_fhir_questionnaire() only stamps `id` and `meta` onto it. So what can go wrong on the read side
is that stamping (e.g. a malformed meta extension) or a stored document the server returns that
isn't valid R4 - each case below is a `content` document as the write path would store it, run
through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.questionnaire import to_fhir_questionnaire
from app.models.questionnaire import QuestionnaireModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.questionnaire_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE = "http://terminology.hl7.org/CodeSystem/usage-context-type"


def _c(content: dict, **overrides) -> QuestionnaireModel:
    fields = {
        "questionnaire_id": 380001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return QuestionnaireModel(**fields)


def _base(**extra) -> dict:
    return {"status": "active", **extra}


def _items(*items) -> dict:
    return _base(item=list(items))


def _item(item_type: str, **extra) -> dict:
    return {"linkId": "1", "type": item_type, **extra}


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in ("draft", "active", "retired", "unknown")
    },
    "url_version_name_title": _c(
        _base(
            url="https://fhir-server.dev/fhir/Questionnaire/phq-9",
            version="1.0",
            name="PHQ9",
            title="Patient Health Questionnaire 9",
            derivedFrom=["https://fhir-server.dev/fhir/Questionnaire/base"],
            experimental=False,
        )
    ),
    "identifier": _c(
        _base(
            identifier=[
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ACSN",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-id",
                    "value": "PHQ-9",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                },
                {"system": "urn:other", "value": "second"},
            ]
        )
    ),
    "subject_type": _c(_base(subjectType=["Patient", "Group", "Encounter"])),
    "dates": _c(
        _base(
            date="2026-01-15T10:00:00Z",
            approvalDate="2026-01-10",
            lastReviewDate="2026-01-12",
            effectivePeriod={"start": "2026-01-01", "end": "2026-12-31"},
        )
    ),
    "partial_dates": _c(_base(date="2026", effectivePeriod={"start": "2026-01"})),
    "publisher_contact_text": _c(
        _base(
            publisher="Example Health",
            contact=[
                {
                    "name": "Help desk",
                    "telecom": [
                        {"system": "phone", "value": "555-1234", "use": "work"}
                    ],
                }
            ],
            description="A nine-question depression screen.",
            purpose="Screening",
            copyright="(c) Example",
        )
    ),
    "use_context_concept": _c(
        _base(
            useContext=[
                {
                    "code": {"system": USAGE, "code": "focus"},
                    "valueCodeableConcept": {
                        "coding": [{"system": SCT, "code": "35489007"}],
                        "text": "Depression",
                    },
                }
            ]
        )
    ),
    "use_context_quantity": _c(
        _base(
            useContext=[
                {
                    "code": {"system": USAGE, "code": "age"},
                    "valueQuantity": {
                        "value": 18,
                        "comparator": ">=",
                        "unit": "years",
                        "system": UCUM,
                        "code": "a",
                    },
                }
            ]
        )
    ),
    "use_context_range": _c(
        _base(
            useContext=[
                {
                    "code": {"system": USAGE, "code": "age"},
                    "valueRange": {
                        "low": {"value": 12, "system": UCUM, "code": "a"},
                        "high": {"value": 17, "system": UCUM, "code": "a"},
                    },
                }
            ]
        )
    ),
    "use_context_reference": _c(
        _base(
            useContext=[
                {
                    "code": {"system": USAGE, "code": "venue"},
                    "valueReference": {"reference": "Organization/190001"},
                }
            ]
        )
    ),
    "jurisdiction": _c(
        _base(
            jurisdiction=[
                {
                    "coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}],
                    "text": "US",
                }
            ]
        )
    ),
    "code": _c(_base(code=[{"system": LOINC, "code": "44249-1", "display": "PHQ-9"}])),
    **{
        f"item_{t}": _c(_items(_item(t)))
        for t in (
            "group",
            "display",
            "boolean",
            "decimal",
            "integer",
            "date",
            "dateTime",
            "time",
            "string",
            "text",
            "url",
            "choice",
            "open-choice",
            "attachment",
            "reference",
            "quantity",
        )
    },
    "nested_items": _c(
        _items(
            _item(
                "group",
                text="Mood",
                prefix="1",
                definition="http://example.org/definitions/mood",
                item=[
                    {"linkId": "1.1", "type": "integer"},
                    {
                        "linkId": "1.2",
                        "type": "group",
                        "item": [{"linkId": "1.2.1", "type": "string"}],
                    },
                ],
            )
        )
    ),
    "item_code_and_flags": _c(
        _items(
            _item(
                "string",
                code=[{"system": LOINC, "code": "44250-9"}],
                required=True,
                repeats=False,
                readOnly=False,
                maxLength=40,
            )
        )
    ),
    "item_enable_when": _c(
        _items(
            _item(
                "string",
                enableBehavior="any",
                enableWhen=[
                    {"question": "0", "operator": "exists", "answerBoolean": True},
                    {"question": "0.1", "operator": "=", "answerDecimal": 3.5},
                    {"question": "0.2", "operator": "!=", "answerInteger": 3},
                    {"question": "0.3", "operator": ">", "answerDate": "2026-01-05"},
                    {
                        "question": "0.4",
                        "operator": "<",
                        "answerDateTime": "2026-01-05T08:30:00Z",
                    },
                    {"question": "0.5", "operator": ">=", "answerTime": "08:30:00"},
                    {"question": "0.6", "operator": "<=", "answerString": "x"},
                    {
                        "question": "0.7",
                        "operator": "=",
                        "answerCoding": {"system": SCT, "code": "1"},
                    },
                    {
                        "question": "0.8",
                        "operator": "=",
                        "answerQuantity": {"value": 5, "unit": "mg"},
                    },
                    {
                        "question": "0.9",
                        "operator": "=",
                        "answerReference": {"reference": "Observation/160001"},
                    },
                ],
            )
        )
    ),
    "item_answer_option": _c(
        _items(
            _item(
                "choice",
                answerValueSet="http://example.org/ValueSet/yn",
                answerOption=[
                    {"valueInteger": 1},
                    {"valueDate": "2026-01-05"},
                    {"valueTime": "08:30:00"},
                    {"valueString": "other"},
                    {
                        "valueCoding": {"system": LOINC, "code": "LA6568-5"},
                        "initialSelected": True,
                    },
                    {"valueReference": {"reference": "Organization/190001"}},
                ],
            )
        )
    ),
    "item_initial": _c(
        _items(
            _item(
                "string",
                initial=[
                    {"valueBoolean": True},
                    {"valueDecimal": 2.5},
                    {"valueInteger": 3},
                    {"valueDate": "2026-01-05"},
                    {"valueDateTime": "2026-01-05T08:30:00Z"},
                    {"valueTime": "08:30:00"},
                    {"valueString": "seed"},
                    {"valueUri": "http://example.org/x"},
                    {
                        "valueAttachment": {
                            "contentType": "application/pdf",
                            "title": "Scan",
                        }
                    },
                    {"valueCoding": {"system": SCT, "code": "1"}},
                    {"valueQuantity": {"value": 72.5, "unit": "kg"}},
                    {"valueReference": {"reference": "Observation/160001"}},
                ],
            )
        )
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_questionnaire_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Questionnaire, to_fhir_questionnaire(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(item=[{"linkId": "1", "type": "string"}])
    out = to_fhir_questionnaire(_c(content))
    assert out["resourceType"] == "Questionnaire"
    assert out["id"] == "380001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1; the integration tests cover that.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "in-progress"}),
        ("status as number", {"status": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("url as number", {"url": 5}),
        ("version as number", {"version": 1}),
        ("experimental as string", {"experimental": "yes"}),
        ("subjectType as string", {"subjectType": "Patient"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("approvalDate not a date", {"approvalDate": "tomorrow"}),
        ("effectivePeriod as string", {"effectivePeriod": "2026"}),
        ("contact as object", {"contact": {"name": "x"}}),
        ("useContext as object", {"useContext": {"code": {"code": "x"}}}),
        ("jurisdiction as object", {"jurisdiction": {"coding": []}}),
        ("code as object", {"code": {"system": LOINC, "code": "x"}}),
        ("item as object not a list", {"item": {"linkId": "1", "type": "string"}}),
        ("item entry as string", {"item": ["x"]}),
        ("item linkId as number", {"item": [{"linkId": 1, "type": "string"}]}),
        ("item type unknown", {"item": [{"linkId": "1", "type": "nonsense"}]}),
        (
            "item required as string",
            {"item": [{"linkId": "1", "type": "string", "required": "yes"}]},
        ),
        (
            "item maxLength as string",
            {"item": [{"linkId": "1", "type": "string", "maxLength": "ten"}]},
        ),
        (
            "item enableBehavior unknown",
            {"item": [{"linkId": "1", "type": "string", "enableBehavior": "some"}]},
        ),
        (
            "enableWhen operator unknown",
            {
                "item": [
                    {
                        "linkId": "1",
                        "type": "string",
                        "enableWhen": [{"question": "0", "operator": "between"}],
                    }
                ]
            },
        ),
        (
            "nested item as string",
            {
                "item": [
                    {
                        "linkId": "1",
                        "type": "group",
                        "item": [{"linkId": "2", "type": "string", "item": "x"}],
                    }
                ]
            },
        ),
        (
            "answerOption valueInteger as string",
            {
                "item": [
                    {
                        "linkId": "1",
                        "type": "choice",
                        "answerOption": [{"valueInteger": "one"}],
                    }
                ]
            },
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Questionnaire", "id": "380001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Questionnaire, validate=True
        )

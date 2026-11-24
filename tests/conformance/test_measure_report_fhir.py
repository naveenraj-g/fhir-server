"""FHIR R4 conformance for `to_fhir_measure_report()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MeasureReport is stored whole in `content` (like QuestionnaireResponse, Measure and the other
content-based resources): the resource lives in MeasureReportModel.content, and
to_fhir_measure_report() only stamps `id` and `meta` onto it. So what can go wrong on the read side
is that stamping (e.g. a malformed meta extension) or a stored document the server returns that
isn't valid R4 - each case below is a `content` document as the write path would store it, run
through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.measure_report import to_fhir_measure_report
from app.models.measure_report import MeasureReportModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.measure_report_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
POPULATION = "http://terminology.hl7.org/CodeSystem/measure-population"
MEASURE = "https://fhir-server.dev/fhir/Measure/readmission"
PERIOD = {"start": "2026-01-01", "end": "2026-01-31"}


def _c(content: dict, **overrides) -> MeasureReportModel:
    fields = {
        "measure_report_id": 570001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MeasureReportModel(**fields)


def _base(**extra) -> dict:
    return {
        "status": "complete",
        "type": "summary",
        "measure": MEASURE,
        "period": PERIOD,
        **extra,
    }


def _population(code="numerator", **extra) -> dict:
    return {
        "code": {"coding": [{"system": POPULATION, "code": code}]},
        **extra,
    }


def _group(**extra) -> dict:
    return _base(group=[extra])


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{f"status_{s}": _c(_base(status=s)) for s in ("complete", "pending", "error")},
    **{
        f"type_{t}": _c(_base(type=t))
        for t in ("individual", "subject-list", "summary", "data-collection")
    },
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
                    "system": "urn:mr",
                    "value": "MR-1",
                    "assigner": {"reference": "Organization/190001"},
                },
                {"value": "MR-2"},
            ]
        )
    ),
    "measure_versioned": _c(_base(measure=f"{MEASURE}|1.0")),
    "measure_relative": _c(_base(measure="Measure/560001")),
    "subject_patient": _c(_base(subject={"reference": "Patient/10001"})),
    "subject_group": _c(_base(subject={"reference": "Group/430001"})),
    "subject_logical": _c(
        _base(
            subject={
                "identifier": {"system": "urn:mrn", "value": "M-1"},
                "display": "J",
            }
        )
    ),
    "date_datetime": _c(_base(date="2026-02-01T10:00:00Z")),
    "date_partial": _c(_base(date="2026-02")),
    "reporter_organization": _c(_base(reporter={"reference": "Organization/190001"})),
    "reporter_practitioner": _c(_base(reporter={"reference": "Practitioner/30001"})),
    "period_open_end": _c(_base(period={"start": "2026-01-01"})),
    "period_datetimes": _c(
        _base(period={"start": "2026-01-01T00:00:00Z", "end": "2026-01-31T23:59:59Z"})
    ),
    "improvement_notation": _c(
        _base(
            improvementNotation={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                        "code": "increase",
                    }
                ],
                "text": "Higher is better",
            }
        )
    ),
    "group_with_code_and_score": _c(
        _group(
            id="g1",
            code={"coding": [{"system": SCT, "code": "1"}], "text": "overall"},
            measureScore={"value": 0.15, "unit": "1", "system": UCUM, "code": "1"},
        )
    ),
    "group_population": _c(
        _group(
            population=[
                _population("initial-population", count=120),
                _population(
                    "numerator", count=18, subjectResults={"reference": "List/1"}
                ),
            ]
        )
    ),
    "group_several": _c(
        _base(group=[{"code": {"text": "a"}}, {"code": {"text": "b"}}, {}])
    ),
    "group_stratifier_codes": _c(
        _group(
            stratifier=[
                {"code": [{"text": "age"}, {"coding": [{"system": SCT, "code": "2"}]}]}
            ]
        )
    ),
    "group_stratum_value_and_score": _c(
        _group(
            stratifier=[
                {
                    "stratum": [
                        {
                            "value": {"text": "adult"},
                            "measureScore": {"value": 0.1},
                        }
                    ]
                }
            ]
        )
    ),
    "group_stratum_population": _c(
        _group(
            stratifier=[
                {
                    "stratum": [
                        {
                            "value": {"text": "adult"},
                            "population": [
                                _population("numerator", count=7),
                                _population("denominator", count=40),
                            ],
                        }
                    ]
                }
            ]
        )
    ),
    "group_stratum_components": _c(
        _group(
            stratifier=[
                {
                    "code": [{"text": "sex"}, {"text": "ward"}],
                    "stratum": [
                        {
                            "component": [
                                {"code": {"text": "sex"}, "value": {"text": "female"}},
                                {"code": {"text": "ward"}, "value": {"text": "A"}},
                            ],
                            "measureScore": {"value": 0.2},
                        }
                    ],
                }
            ]
        )
    ),
    "evaluated_resource": _c(
        _base(
            evaluatedResource=[
                {"reference": "Patient/10001"},
                {"reference": "https://other.example.org/fhir/Observation/9"},
                {"identifier": {"system": "urn:x", "value": "E-1"}},
            ]
        )
    ),
    "extension": _c(
        _base(
            extension=[{"url": "https://fhir-server.dev/ext/note", "valueString": "x"}]
        )
    ),
    "everything": _c(
        _base(
            identifier=[{"system": "urn:mr", "value": "MR-1"}],
            subject={"reference": "Patient/10001"},
            date="2026-02-01T10:00:00Z",
            reporter={"reference": "Organization/190001"},
            improvementNotation={"text": "up"},
            group=[
                {
                    "code": {"text": "overall"},
                    "population": [_population("numerator", count=1)],
                    "measureScore": {"value": 0.5},
                    "stratifier": [
                        {
                            "code": [{"text": "age"}],
                            "stratum": [
                                {
                                    "value": {"text": "adult"},
                                    "population": [_population("numerator", count=1)],
                                    "measureScore": {"value": 0.5},
                                }
                            ],
                        }
                    ],
                }
            ],
            evaluatedResource=[{"reference": "Patient/10001"}],
        )
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_measure_report_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.MeasureReport, to_fhir_measure_report(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(
        group=[{"code": {"text": "x"}, "population": [_population(count=3)]}]
    )
    out = to_fhir_measure_report(_c(content))
    assert out["resourceType"] == "MeasureReport"
    assert out["id"] == "570001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("type with an unknown code", {"type": "banana"}),
        ("type as number", {"type": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("measure as object", {"measure": {"reference": "Measure/1"}}),
        ("measure as number", {"measure": 5}),
        ("subject as string", {"subject": "Patient/1"}),
        ("subject as list", {"subject": [{"reference": "Patient/1"}]}),
        ("date as number", {"date": 5}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("reporter as string", {"reporter": "Organization/1"}),
        ("period as string", {"period": "2026"}),
        ("period start not a date", {"period": {"start": "soon"}}),
        ("improvementNotation as string", {"improvementNotation": "increase"}),
        ("group as object not a list", {"group": {"code": {"text": "x"}}}),
        ("group entry as string", {"group": ["x"]}),
        ("group code as string", {"group": [{"code": "x"}]}),
        ("population as object", {"group": [{"population": {"count": 1}}]}),
        (
            "population count as string",
            {"group": [{"population": [{"count": "many"}]}]},
        ),
        (
            "population subjectResults as string",
            {"group": [{"population": [{"subjectResults": "List/1"}]}]},
        ),
        ("measureScore as number", {"group": [{"measureScore": 0.5}]}),
        ("stratifier as object", {"group": [{"stratifier": {"code": []}}]}),
        (
            "stratifier code as object",
            {"group": [{"stratifier": [{"code": {"text": "x"}}]}]},
        ),
        (
            "stratum as object",
            {"group": [{"stratifier": [{"stratum": {"value": {}}}]}]},
        ),
        (
            "stratum value as string",
            {"group": [{"stratifier": [{"stratum": [{"value": "adult"}]}]}]},
        ),
        (
            "component as object",
            {"group": [{"stratifier": [{"stratum": [{"component": {"code": {}}}]}]}]},
        ),
        (
            "evaluatedResource as object",
            {"evaluatedResource": {"reference": "Patient/1"}},
        ),
        ("evaluatedResource entry as string", {"evaluatedResource": ["Patient/1"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MeasureReport", "id": "570001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MeasureReport, validate=True
        )

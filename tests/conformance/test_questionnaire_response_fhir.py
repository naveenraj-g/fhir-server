"""FHIR R4 conformance for `to_fhir_questionnaire_response()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.questionnaire_response import to_fhir_questionnaire_response
from app.models.questionnaire_response import (
    QuestionnaireResponseAnswer,
    QuestionnaireResponseBasedOn,
    QuestionnaireResponseItem,
    QuestionnaireResponseModel,
    QuestionnaireResponsePartOf,
    QuestionnaireResponseStatus,
)

from .support import assert_valid

qr_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.questionnaire_response_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifier_type_codings",
    "based_ons",
    "part_ofs",
    "items",
    "answers",
)


def _qr(**overrides) -> QuestionnaireResponseModel:
    fields = {
        "questionnaire_response_id": 60001,
        "tenant_id": "org-test",
        "status": QuestionnaireResponseStatus.completed,
        "authored": D,
        "created_by": "u-test",
        "created_at": D,
        "extension": [],
    }
    fields.update(overrides)
    model = QuestionnaireResponseModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(model, attr, None) is None:
            setattr(model, attr, [])
    return model


def _with(attr, *rows) -> QuestionnaireResponseModel:
    model = _qr()
    setattr(model, attr, list(rows))
    return model


CASES = {
    "minimal": _qr(),
    "subject_resolved": _qr(
        subject_type="Patient",
        subject_id=10001,
        subject_display="Alice Doe",
    ),
    "subject_fallback": _qr(
        subject_display="External Subject",
        subject_identifier_system="http://external-patients.example.org",
        subject_identifier_value="EXT-PAT-88",
        subject_identifier_use="official",
    ),
    "encounter_fallback": _qr(
        encounter_display="External Encounter",
        encounter_identifier_system="http://encounters.example.org",
        encounter_identifier_value="ENC-88",
        encounter_identifier_use="official",
    ),
    "author_fallback": _qr(
        author_display="External Author",
        author_identifier_system="http://practitioners.example.org",
        author_identifier_value="PRAC-88",
        author_identifier_use="official",
    ),
    "source_fallback": _qr(
        source_display="External Source",
        source_identifier_system="http://sources.example.org",
        source_identifier_value="SRC-88",
        source_identifier_use="official",
    ),
    "based_on_fallback": _with(
        "based_ons",
        QuestionnaireResponseBasedOn(
            id=1,
            tenant_id="org-test",
            reference_display="External Referral",
            reference_identifier_system="http://referrals.example.org",
            reference_identifier_value="REF-22",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "part_of_fallback": _with(
        "part_ofs",
        QuestionnaireResponsePartOf(
            id=1,
            tenant_id="org-test",
            reference_display="External Procedure",
            reference_identifier_system="http://procedures.example.org",
            reference_identifier_value="PROC-33",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "answer_value_reference_fallback": (
        lambda: (
            _qr(
                items=[
                    QuestionnaireResponseItem(
                        id=1,
                        questionnaire_response_pk=1,
                        tenant_id="org-test",
                        link_id="q1",
                        text="Prior observation",
                        created_by="u-test",
                        created_at=D,
                    )
                ],
                answers=[
                    QuestionnaireResponseAnswer(
                        id=1,
                        questionnaire_response_pk=1,
                        item_id=1,
                        tenant_id="org-test",
                        value_reference_display="Lab Result 99",
                        value_reference_identifier_system="http://labs.example.org",
                        value_reference_identifier_value="LAB-99",
                        value_reference_identifier_use="official",
                        created_by="u-test",
                        created_at=D,
                    )
                ],
            )
        )
    )(),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_questionnaire_response_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_questionnaire_response(model)
    assert_valid(qr_pb2.QuestionnaireResponse, output)

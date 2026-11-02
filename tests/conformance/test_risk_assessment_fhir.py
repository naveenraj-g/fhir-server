"""FHIR R4 conformance for `to_fhir_risk_assessment()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.risk_assessment import to_fhir_risk_assessment
from app.models.enums import IdentifierUse, OrganizationReferenceType, SubjectReferenceType
from app.models.risk_assessment import (
    RiskAssessmentBasisModel,
    RiskAssessmentCodeCodingModel,
    RiskAssessmentConditionReferenceType,
    RiskAssessmentIdentifierModel,
    RiskAssessmentIdentifierTypeCodingModel,
    RiskAssessmentMethodCodingModel,
    RiskAssessmentModel,
    RiskAssessmentNoteAuthorReferenceType,
    RiskAssessmentNoteModel,
    RiskAssessmentPerformerReferenceType,
    RiskAssessmentPredictionModel,
    RiskAssessmentPredOutcomeCodingModel,
    RiskAssessmentPredQualRiskCodingModel,
    RiskAssessmentReasonCodeCodingModel,
    RiskAssessmentReasonCodeModel,
    RiskAssessmentReasonReferenceModel,
    RiskAssessmentReasonReferenceType,
    RiskAssessmentStatus,
)

from .support import assert_valid

risk_assessment_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.risk_assessment_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "method_codings",
    "code_codings",
    "reason_codes",
    "reason_references",
    "basis",
    "predictions",
    "notes",
)


def _risk_assessment(**overrides) -> RiskAssessmentModel:
    fields = {
        "id": 1,
        "risk_assessment_id": 520001,
        "tenant_id": "org-test",
        "status": RiskAssessmentStatus.final,
        "subject_reference": "Patient/10001",
        "subject_type": SubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "occurrence_date_time": D,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = RiskAssessmentModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_risk_assessment_conforms():
    m = _risk_assessment()
    resource = to_fhir_risk_assessment(m)
    assert_valid(risk_assessment_pb2.RiskAssessment, resource)


def test_full_risk_assessment_conforms():
    ident = RiskAssessmentIdentifierModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        use=IdentifierUse.official,
        system="http://example.org/risk-assessment-ids",
        value="RA-2026-001",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Clinic",
        type_text="Usual ID",
    )
    ident.type_codings = [
        RiskAssessmentIdentifierTypeCodingModel(
            id=1,
            risk_assessment_identifier_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            user_selected=True,
        )
    ]

    method_coding = RiskAssessmentMethodCodingModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        system="http://snomed.info/sct",
        code="709510001",
        display="Framingham risk score",
        user_selected=True,
    )

    code_coding = RiskAssessmentCodeCodingModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        system="http://loinc.org",
        code="89243-0",
        display="Cardiovascular disease 10Y risk [Likelihood]",
        user_selected=True,
    )

    reason_code = RiskAssessmentReasonCodeModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Cardiovascular screening",
    )
    reason_code.codings = [
        RiskAssessmentReasonCodeCodingModel(
            id=1,
            risk_assessment_reason_code_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="171121004",
            display="Screening for cardiovascular disease",
            user_selected=True,
        )
    ]

    reason_ref = RiskAssessmentReasonReferenceModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        reference_reference="Condition/120001",
        reference_type=RiskAssessmentReasonReferenceType.Condition,
        reference_id=120001,
        reference_display="Hypertension",
    )

    basis_ref = RiskAssessmentBasisModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        reference_reference="Observation/160001",
        reference_type="Observation",
        reference_id=160001,
        reference_display="Blood pressure measurement",
    )

    pred = RiskAssessmentPredictionModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        outcome_text="Atrial fibrillation",
        probability_decimal=0.12,
        qualitative_risk_text="Moderate risk",
        relative_risk=1.5,
        when_period_start=D,
        when_period_end=D,
        rationale="Elevated systolic BP and family history.",
    )
    pred.outcome_codings = [
        RiskAssessmentPredOutcomeCodingModel(
            id=1,
            risk_assessment_prediction_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="49436004",
            display="Atrial fibrillation",
            user_selected=True,
        )
    ]
    pred.qualitative_risk_codings = [
        RiskAssessmentPredQualRiskCodingModel(
            id=1,
            risk_assessment_prediction_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://terminology.hl7.org/CodeSystem/risk-probability",
            code="moderate",
            display="Moderate likelihood",
            user_selected=True,
        )
    ]

    note = RiskAssessmentNoteModel(
        id=1,
        risk_assessment_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Re-evaluate in 12 months.",
        time=D,
        author_string="Dr. Alice Smith",
    )

    m = _risk_assessment(
        condition_reference="Condition/120001",
        condition_type=RiskAssessmentConditionReferenceType.Condition,
        condition_id=120001,
        condition_display="Hypertension",
        performer_reference="Practitioner/30001",
        performer_type=RiskAssessmentPerformerReferenceType.Practitioner,
        performer_id=30001,
        performer_display="Dr. Alice Smith",
        method_text="Framingham 10-year risk",
        code_text="CVD risk",
        mitigation="Lifestyle modifications and therapy.",
        identifiers=[ident],
        method_codings=[method_coding],
        code_codings=[code_coding],
        reason_codes=[reason_code],
        reason_references=[reason_ref],
        basis=[basis_ref],
        predictions=[pred],
        notes=[note],
    )

    resource = to_fhir_risk_assessment(m)
    assert_valid(risk_assessment_pb2.RiskAssessment, resource)

"""FHIR R4 conformance for `to_fhir_immunization_evaluation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.immunization_evaluation import to_fhir_immunization_evaluation
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.immunization_evaluation import (
    ImmunizationEvaluationAuthorityReferenceType,
    ImmunizationEvaluationDoseStatusCodingModel,
    ImmunizationEvaluationDoseStatusReasonCodingModel,
    ImmunizationEvaluationDoseStatusReasonModel,
    ImmunizationEvaluationIdentifierModel,
    ImmunizationEvaluationIdentifierTypeCodingModel,
    ImmunizationEvaluationImmunizationEventReferenceType,
    ImmunizationEvaluationModel,
    ImmunizationEvaluationPatientReferenceType,
    ImmunizationEvaluationStatus,
    ImmunizationEvaluationTargetDiseaseCodingModel,
)

from .support import assert_valid

immunization_evaluation_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_evaluation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "target_disease_codings",
    "dose_status_codings",
    "dose_status_reasons",
)


def _immunization_evaluation(**overrides) -> ImmunizationEvaluationModel:
    fields = {
        "id": 1,
        "immunization_evaluation_id": 610001,
        "tenant_id": "org-test",
        "status": ImmunizationEvaluationStatus.completed,
        "patient_reference": "Patient/10001",
        "patient_type": ImmunizationEvaluationPatientReferenceType.PATIENT,
        "patient_id": 10001,
        "patient_display": "Jane Doe",
        "target_disease_text": "Measles",
        "immunization_event_reference": "Immunization/330001",
        "immunization_event_type": ImmunizationEvaluationImmunizationEventReferenceType.IMMUNIZATION,
        "immunization_event_id": 330001,
        "dose_status_text": "Valid",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ImmunizationEvaluationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_immunization_evaluation_conforms():
    m = _immunization_evaluation()
    m.target_disease_codings = [
        ImmunizationEvaluationTargetDiseaseCodingModel(
            system="http://snomed.info/sct",
            code="14189004",
            display="Measles",
        )
    ]
    m.dose_status_codings = [
        ImmunizationEvaluationDoseStatusCodingModel(
            system="http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
            code="valid",
            display="Valid",
        )
    ]
    resource = to_fhir_immunization_evaluation(m)
    assert_valid(immunization_evaluation_pb2.ImmunizationEvaluation, resource)


def test_full_immunization_evaluation_conforms():
    ident = ImmunizationEvaluationIdentifierModel(
        use=IdentifierUse.official,
        system="http://example.org/evals",
        value="EVAL-2026-001",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Clinic",
        type_text="Evaluation ID",
    )
    ident.type_codings = [
        ImmunizationEvaluationIdentifierTypeCodingModel(
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
        )
    ]

    target_disease_coding = ImmunizationEvaluationTargetDiseaseCodingModel(
        system="http://snomed.info/sct",
        code="14189004",
        display="Measles",
        user_selected=True,
    )

    dose_status_coding = ImmunizationEvaluationDoseStatusCodingModel(
        system="http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
        code="valid",
        display="Valid",
        user_selected=True,
    )

    reason = ImmunizationEvaluationDoseStatusReasonModel(
        text="Administered per CDC schedule",
    )
    reason.codings = [
        ImmunizationEvaluationDoseStatusReasonCodingModel(
            system="http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason",
            code="outsideschedule",
            display="Outside Schedule",
        )
    ]

    m = _immunization_evaluation(
        date=D,
        authority_reference="Organization/190001",
        authority_type=ImmunizationEvaluationAuthorityReferenceType.ORGANIZATION,
        authority_id=190001,
        authority_display="CDC",
        description="Routine MMR dose 1 evaluation",
        series="MMR 2-dose",
        dose_number_positive_int=1,
        series_doses_positive_int=2,
        identifiers=[ident],
        target_disease_codings=[target_disease_coding],
        dose_status_codings=[dose_status_coding],
        dose_status_reasons=[reason],
    )

    resource = to_fhir_immunization_evaluation(m)
    assert_valid(immunization_evaluation_pb2.ImmunizationEvaluation, resource)

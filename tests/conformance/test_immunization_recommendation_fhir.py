"""FHIR R4 conformance for `to_fhir_immunization_recommendation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.immunization_recommendation import to_fhir_immunization_recommendation
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.immunization_recommendation import (
    ImmunizationRecommendationAuthorityReferenceType,
    ImmunizationRecommendationContraindicatedCodeCodingModel,
    ImmunizationRecommendationContraindicatedCodeModel,
    ImmunizationRecommendationDateCriterionCodeCodingModel,
    ImmunizationRecommendationDateCriterionModel,
    ImmunizationRecommendationForecastReasonCodingModel,
    ImmunizationRecommendationForecastReasonModel,
    ImmunizationRecommendationForecastStatusCodingModel,
    ImmunizationRecommendationIdentifierModel,
    ImmunizationRecommendationIdentifierTypeCodingModel,
    ImmunizationRecommendationModel,
    ImmunizationRecommendationPatientReferenceType,
    ImmunizationRecommendationRecommendationModel,
    ImmunizationRecommendationSupportingImmunizationModel,
    ImmunizationRecommendationSupportingImmunizationReferenceType,
    ImmunizationRecommendationSupportingPatientInformationModel,
    ImmunizationRecommendationSupportingPatientInformationReferenceType,
    ImmunizationRecommendationTargetDiseaseCodingModel,
    ImmunizationRecommendationVaccineCodeCodingModel,
    ImmunizationRecommendationVaccineCodeModel,
)

from .support import assert_valid

immunization_recommendation_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_recommendation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)
D_DUE = dt.datetime(2026, 2, 15, 0, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "recommendations",
)


def _immunization_recommendation(**overrides) -> ImmunizationRecommendationModel:
    fields = {
        "id": 1,
        "immunization_recommendation_id": 510001,
        "tenant_id": "org-test",
        "patient_reference": "Patient/10001",
        "patient_type": ImmunizationRecommendationPatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "Jane Doe",
        "date": D,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ImmunizationRecommendationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def _minimal_recommendation() -> ImmunizationRecommendationRecommendationModel:
    rec = ImmunizationRecommendationRecommendationModel(
        id=1,
        immunization_recommendation_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        forecast_status_text="Due",
    )
    rec.forecast_status_codings = [
        ImmunizationRecommendationForecastStatusCodingModel(
            recommendation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
            code="due",
            display="Due",
        )
    ]
    rec.vaccine_codes = []
    rec.target_disease_codings = []
    rec.contraindicated_vaccine_codes = []
    rec.forecast_reasons = []
    rec.date_criteria = []
    rec.supporting_immunizations = []
    rec.supporting_patient_information = []
    return rec


def test_minimal_conformance():
    m = _immunization_recommendation()
    m.recommendations = [_minimal_recommendation()]

    resource = to_fhir_immunization_recommendation(m)
    assert_valid(immunization_recommendation_pb2.ImmunizationRecommendation, resource)


def test_full_conformance():
    m = _immunization_recommendation(
        authority_reference="Organization/190001",
        authority_type=ImmunizationRecommendationAuthorityReferenceType.Organization,
        authority_id=190001,
        authority_display="National Health Authority",
    )

    ident = ImmunizationRecommendationIdentifierModel(
        immunization_recommendation_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        use=IdentifierUse.official,
        system="http://example.org/recommendations",
        value="REC-12345",
        period_start=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="National Health Authority",
    )
    ident.type_codings = [
        ImmunizationRecommendationIdentifierTypeCodingModel(
            identifier_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
        )
    ]
    m.identifiers = [ident]

    rec = _minimal_recommendation()
    rec.description = "Annual influenza vaccination"
    rec.series = "Annual"
    rec.dose_number_positive_int = 1
    rec.series_doses_positive_int = 1

    vc = ImmunizationRecommendationVaccineCodeModel(
        recommendation_id=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Fluzone High-Dose Quadrivalent",
    )
    vc.codings = [
        ImmunizationRecommendationVaccineCodeCodingModel(
            vaccine_code_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://hl7.org/fhir/sid/cvx",
            code="197",
            display="influenza, high-dose, quadrivalent",
        )
    ]
    rec.vaccine_codes = [vc]

    rec.target_disease_text = "Influenza"
    rec.target_disease_codings = [
        ImmunizationRecommendationTargetDiseaseCodingModel(
            recommendation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="6142004",
            display="Influenza",
        )
    ]

    cvc = ImmunizationRecommendationContraindicatedCodeModel(
        recommendation_id=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Live Attenuated Influenza Vaccine",
    )
    cvc.codings = [
        ImmunizationRecommendationContraindicatedCodeCodingModel(
            contraindicated_code_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://hl7.org/fhir/sid/cvx",
            code="111",
            display="influenza, live, intranasal",
        )
    ]
    rec.contraindicated_vaccine_codes = [cvc]

    fr = ImmunizationRecommendationForecastReasonModel(
        recommendation_id=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Age-based recommendation",
    )
    fr.codings = [
        ImmunizationRecommendationForecastReasonCodingModel(
            forecast_reason_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="428191000124101",
            display="Documentation of reason for immunization",
        )
    ]
    rec.forecast_reasons = [fr]

    dc = ImmunizationRecommendationDateCriterionModel(
        recommendation_id=1,
        tenant_id="org-test",
        created_by="u-test",
        code_text="Date vaccine due",
        value=D_DUE,
    )
    dc.code_codings = [
        ImmunizationRecommendationDateCriterionCodeCodingModel(
            date_criterion_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://loinc.org",
            code="30980-7",
            display="Date vaccine due",
        )
    ]
    rec.date_criteria = [dc]

    rec.supporting_immunizations = [
        ImmunizationRecommendationSupportingImmunizationModel(
            recommendation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            reference_reference="Immunization/330001",
            reference_type=ImmunizationRecommendationSupportingImmunizationReferenceType.Immunization,
            reference_id=330001,
            reference_display="Prior influenza vaccination",
        )
    ]

    rec.supporting_patient_information = [
        ImmunizationRecommendationSupportingPatientInformationModel(
            recommendation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            reference_reference="Observation/160001",
            reference_type=ImmunizationRecommendationSupportingPatientInformationReferenceType.Observation,
            reference_id=160001,
            reference_display="Patient age observation",
        )
    ]

    m.recommendations = [rec]

    resource = to_fhir_immunization_recommendation(m)
    assert_valid(immunization_recommendation_pb2.ImmunizationRecommendation, resource)

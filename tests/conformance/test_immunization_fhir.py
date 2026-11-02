"""FHIR R4 conformance for `to_fhir_immunization()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt
from decimal import Decimal

import pytest

from app.fhir.mappers.immunization import to_fhir_immunization
from app.models.enums import IdentifierUse
from app.models.immunization import (
    ImmunizationEducationModel,
    ImmunizationEncounterReferenceType,
    ImmunizationFundingSourceCodingModel,
    ImmunizationIdentifierModel,
    ImmunizationIdentifierTypeCodingModel,
    ImmunizationLocationReferenceType,
    ImmunizationManufacturerReferenceType,
    ImmunizationModel,
    ImmunizationNoteAuthorReferenceType,
    ImmunizationNoteModel,
    ImmunizationPatientReferenceType,
    ImmunizationPerformerActorReferenceType,
    ImmunizationPerformerFunctionCodingModel,
    ImmunizationPerformerModel,
    ImmunizationProgramEligibilityCodingModel,
    ImmunizationProgramEligibilityModel,
    ImmunizationProtocolAppliedAuthorityReferenceType,
    ImmunizationProtocolAppliedModel,
    ImmunizationProtocolAppliedTargetDiseaseCodingModel,
    ImmunizationProtocolAppliedTargetDiseaseModel,
    ImmunizationReactionDetailReferenceType,
    ImmunizationReactionModel,
    ImmunizationReasonCodeCodingModel,
    ImmunizationReasonCodeModel,
    ImmunizationReasonReferenceModel,
    ImmunizationReasonReferenceType,
    ImmunizationReportOriginCodingModel,
    ImmunizationRouteCodingModel,
    ImmunizationSiteCodingModel,
    ImmunizationStatus,
    ImmunizationStatusReasonCodingModel,
    ImmunizationSubpotentReasonCodingModel,
    ImmunizationSubpotentReasonModel,
    ImmunizationVaccineCodingModel,
)

from .support import assert_valid

immunization_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
D_EXP = dt.date(2027, 1, 1)

_CHILD_ATTRS = (
    "identifiers",
    "status_reason_codings",
    "vaccine_codings",
    "report_origin_codings",
    "site_codings",
    "route_codings",
    "funding_source_codings",
    "performers",
    "notes",
    "reason_codes",
    "reason_references",
    "subpotent_reasons",
    "education_items",
    "program_eligibilities",
    "reactions",
    "protocol_applied_items",
)


def _immunization(**overrides) -> ImmunizationModel:
    fields = {
        "id": 1,
        "immunization_id": 330001,
        "tenant_id": "org-test",
        "status": ImmunizationStatus.completed,
        "vaccine_code_text": "COVID-19 Vaccine mRNA",
        "patient_reference": "Patient/10001",
        "patient_type": ImmunizationPatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "John Doe",
        "occurrence_date_time": D,
        "primary_source": True,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ImmunizationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_immunization_minimal_conformance():
    m = _immunization()
    m.vaccine_codings = [
        ImmunizationVaccineCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/sid/cvx",
            code="207",
            display="COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5mL dose",
        )
    ]
    resource = to_fhir_immunization(m)
    assert_valid(immunization_pb2.Immunization, resource)


def test_immunization_full_conformance():
    m = _immunization(
        status=ImmunizationStatus.completed,
        status_reason_text="Patient requested postponement",
        lot_number="LOT-9988",
        expiration_date=D_EXP,
        is_subpotent=False,
        recorded=D,
        dose_quantity_value=Decimal("0.5"),
        dose_quantity_unit="mL",
        dose_quantity_system="http://unitsofmeasure.org",
        dose_quantity_code="mL",
        encounter_reference="Encounter/20001",
        encounter_type=ImmunizationEncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Vaccination Clinic Visit",
        location_reference="Location/230001",
        location_type=ImmunizationLocationReferenceType.Location,
        location_id=230001,
        location_display="Main Clinic Room 1",
        manufacturer_reference="Organization/190001",
        manufacturer_type=ImmunizationManufacturerReferenceType.Organization,
        manufacturer_id=190001,
        manufacturer_display="Moderna US",
    )

    m.identifiers = [
        ImmunizationIdentifierModel(
            immunization_pk=1,
            tenant_id="org-test",
            use=IdentifierUse.official,
            system="http://example.org/immunizations",
            value="IMM-2026-001",
            type_codings=[
                ImmunizationIdentifierTypeCodingModel(
                    identifier_id=1,
                    tenant_id="org-test",
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="MR",
                    display="Medical Record Number",
                )
            ],
        )
    ]

    m.vaccine_codings = [
        ImmunizationVaccineCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/sid/cvx",
            code="207",
            display="COVID-19 mRNA",
        )
    ]

    m.status_reason_codings = [
        ImmunizationStatusReasonCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
            code="MEDPREC",
            display="medical precaution",
        )
    ]

    m.report_origin_codings = [
        ImmunizationReportOriginCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/immunization-origin",
            code="recall",
            display="Parent/Guardian/Patient Recall",
        )
    ]

    m.site_codings = [
        ImmunizationSiteCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActSite",
            code="LA",
            display="Left Arm",
        )
    ]

    m.route_codings = [
        ImmunizationRouteCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
            code="IM",
            display="Intramuscular",
        )
    ]

    m.funding_source_codings = [
        ImmunizationFundingSourceCodingModel(
            immunization_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/immunization-funding-source",
            code="private",
            display="Private",
        )
    ]

    m.performers = [
        ImmunizationPerformerModel(
            immunization_pk=1,
            tenant_id="org-test",
            actor_reference="Practitioner/30001",
            actor_type=ImmunizationPerformerActorReferenceType.Practitioner,
            actor_id=30001,
            actor_display="Dr. Alice Smith",
            function_codings=[
                ImmunizationPerformerFunctionCodingModel(
                    performer_id=1,
                    tenant_id="org-test",
                    system="http://terminology.hl7.org/CodeSystem/v2-0443",
                    code="AP",
                    display="Administering Provider",
                )
            ],
        )
    ]

    m.notes = [
        ImmunizationNoteModel(
            immunization_pk=1,
            tenant_id="org-test",
            author_reference="Practitioner/30001",
            author_type=ImmunizationNoteAuthorReferenceType.Practitioner,
            author_id=30001,
            author_display="Dr. Alice Smith",
            time=D,
            text="Administered smoothly with no immediate adverse effects.",
        )
    ]

    m.reason_codes = [
        ImmunizationReasonCodeModel(
            immunization_pk=1,
            tenant_id="org-test",
            text="Annual vaccination requirement",
            codings=[
                ImmunizationReasonCodeCodingModel(
                    reason_code_id=1,
                    tenant_id="org-test",
                    system="http://snomed.info/sct",
                    code="429060002",
                    display="Procedure to produce and evaluate active immunity",
                )
            ],
        )
    ]

    m.reason_references = [
        ImmunizationReasonReferenceModel(
            immunization_pk=1,
            tenant_id="org-test",
            reference_reference="Condition/120001",
            reference_type=ImmunizationReasonReferenceType.Condition,
            reference_id=120001,
            reference_display="High risk condition",
        )
    ]

    m.subpotent_reasons = [
        ImmunizationSubpotentReasonModel(
            immunization_pk=1,
            tenant_id="org-test",
            text="Partial Dose",
            codings=[
                ImmunizationSubpotentReasonCodingModel(
                    subpotent_reason_id=1,
                    tenant_id="org-test",
                    system="http://terminology.hl7.org/CodeSystem/immunization-subpotent-reason",
                    code="partialdose",
                    display="Partial Dose",
                )
            ],
        )
    ]

    m.education_items = [
        ImmunizationEducationModel(
            immunization_pk=1,
            tenant_id="org-test",
            document_type="VIS",
            publication_date=dt.date(2025, 8, 6),
            presentation_date=dt.date(2026, 1, 1),
            reference="https://www.cdc.gov/vaccines/hcp/vis/vis-statements/covid-19.pdf",
        )
    ]

    m.program_eligibilities = [
        ImmunizationProgramEligibilityModel(
            immunization_pk=1,
            tenant_id="org-test",
            text="Not Eligible",
            codings=[
                ImmunizationProgramEligibilityCodingModel(
                    program_eligibility_id=1,
                    tenant_id="org-test",
                    system="http://terminology.hl7.org/CodeSystem/immunization-program-eligibility",
                    code="ineligible",
                    display="Not Eligible",
                )
            ],
        )
    ]

    m.reactions = [
        ImmunizationReactionModel(
            immunization_pk=1,
            tenant_id="org-test",
            date=D,
            reported=True,
            detail_reference="Observation/160001",
            detail_type=ImmunizationReactionDetailReferenceType.Observation,
            detail_id=160001,
            detail_display="Mild injection site redness",
        )
    ]

    proto = ImmunizationProtocolAppliedModel(
        immunization_pk=1,
        tenant_id="org-test",
        series="COVID-19 Primary Series",
        dose_number_positive_int=1,
        series_doses_positive_int=2,
        authority_reference="Organization/190001",
        authority_type=ImmunizationProtocolAppliedAuthorityReferenceType.Organization,
        authority_id=190001,
        authority_display="CDC",
    )
    td = ImmunizationProtocolAppliedTargetDiseaseModel(
        protocol_applied_id=1,
        tenant_id="org-test",
        text="COVID-19",
        codings=[
            ImmunizationProtocolAppliedTargetDiseaseCodingModel(
                target_disease_id=1,
                tenant_id="org-test",
                system="http://snomed.info/sct",
                code="840539006",
                display="COVID-19",
            )
        ],
    )
    proto.target_diseases = [td]
    m.protocol_applied_items = [proto]

    resource = to_fhir_immunization(m)
    assert_valid(immunization_pb2.Immunization, resource)

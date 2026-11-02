"""FHIR R4 conformance for `to_fhir_clinical_impression()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.clinical_impression import to_fhir_clinical_impression
from app.models.clinical_impression import (
    ClinicalImpressionAssessorReferenceType,
    ClinicalImpressionFindingItemCodingModel,
    ClinicalImpressionFindingModel,
    ClinicalImpressionFindingReferenceType,
    ClinicalImpressionIdentifierModel,
    ClinicalImpressionIdentifierTypeCodingModel,
    ClinicalImpressionInvestigationCodeCodingModel,
    ClinicalImpressionInvestigationItemModel,
    ClinicalImpressionInvestigationModel,
    ClinicalImpressionModel,
    ClinicalImpressionNoteAuthorReferenceType,
    ClinicalImpressionNoteModel,
    ClinicalImpressionPreviousReferenceType,
    ClinicalImpressionProblemModel,
    ClinicalImpressionProblemReferenceType,
    ClinicalImpressionPrognosisCodeableConceptModel,
    ClinicalImpressionPrognosisCodingModel,
    ClinicalImpressionPrognosisReferenceModel,
    ClinicalImpressionPrognosisReferenceType,
    ClinicalImpressionProtocolModel,
    ClinicalImpressionStatus,
    ClinicalImpressionStatusReasonCodingModel,
    ClinicalImpressionCodeCodingModel,
    ClinicalImpressionSupportingInfoModel,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    OrganizationReferenceType,
    SubjectReferenceType,
)

from .support import assert_valid

clinical_impression_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.clinical_impression_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "status_reason_codings",
    "code_codings",
    "problems",
    "investigations",
    "protocols",
    "findings",
    "prognosis_codeable_concepts",
    "prognosis_references",
    "supporting_info",
    "notes",
)


def _clinical_impression(**overrides) -> ClinicalImpressionModel:
    fields = {
        "id": 1,
        "clinical_impression_id": 530001,
        "tenant_id": "org-test",
        "status": ClinicalImpressionStatus.completed,
        "description": "Initial clinical evaluation for acute chest pain.",
        "subject_reference": "Patient/10001",
        "subject_type": SubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "effective_date_time": D,
        "date": D,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ClinicalImpressionModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_clinical_impression_conforms():
    m = _clinical_impression()
    resource = to_fhir_clinical_impression(m)
    assert_valid(clinical_impression_pb2.ClinicalImpression, resource)


def test_full_clinical_impression_conforms():
    ident = ClinicalImpressionIdentifierModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        use=IdentifierUse.official,
        system="http://example.org/ci-ids",
        value="CI-2026-001",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Clinic",
        type_text="Usual ID",
    )
    ident.type_codings = [
        ClinicalImpressionIdentifierTypeCodingModel(
            id=1,
            clinical_impression_identifier_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
        )
    ]

    status_reason_coding = ClinicalImpressionStatusReasonCodingModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        system="http://terminology.hl7.org/CodeSystem/clinicalimpression-status-reason",
        code="treatment-completed",
        display="Treatment Completed",
    )

    code_coding = ClinicalImpressionCodeCodingModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        system="http://snomed.info/sct",
        code="4241000179101",
        display="Initial evaluation",
    )

    problem = ClinicalImpressionProblemModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        problem_reference="Condition/120001",
        problem_type=ClinicalImpressionProblemReferenceType.Condition,
        problem_id=120001,
        problem_display="Chest pain",
    )

    inv = ClinicalImpressionInvestigationModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        code_text="Initial physical exam and ECG",
    )
    inv.code_codings = [
        ClinicalImpressionInvestigationCodeCodingModel(
            id=1,
            clinical_impression_investigation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="271336007",
            display="Examination / signs",
        )
    ]
    inv.items = [
        ClinicalImpressionInvestigationItemModel(
            id=1,
            clinical_impression_investigation_id=1,
            tenant_id="org-test",
            created_by="u-test",
            item_reference="Observation/160001",
            item_type="Observation",
            item_id=160001,
            item_display="12-lead ECG",
        )
    ]

    protocol = ClinicalImpressionProtocolModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        uri="http://example.org/protocols/chest-pain-eval",
    )

    finding = ClinicalImpressionFindingModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        item_codeable_concept_text="Musculoskeletal chest pain",
        item_reference="Condition/120001",
        item_reference_type=ClinicalImpressionFindingReferenceType.Condition,
        item_reference_id=120001,
        item_reference_display="Chest pain",
        basis="Normal ECG and troponin levels",
    )
    finding.item_codings = [
        ClinicalImpressionFindingItemCodingModel(
            id=1,
            clinical_impression_finding_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="29857009",
            display="Chest pain, unspecified",
        )
    ]

    prog_cc = ClinicalImpressionPrognosisCodeableConceptModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        text="Good prognosis with outpatient follow-up",
    )
    prog_cc.codings = [
        ClinicalImpressionPrognosisCodingModel(
            id=1,
            clinical_impression_prognosis_id=1,
            tenant_id="org-test",
            created_by="u-test",
            system="http://snomed.info/sct",
            code="170968001",
            display="Good prognosis",
        )
    ]

    prog_ref = ClinicalImpressionPrognosisReferenceModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        reference="RiskAssessment/520001",
        reference_type=ClinicalImpressionPrognosisReferenceType.RiskAssessment,
        reference_id=520001,
        display="10-year CVD risk score",
    )

    supp_info = ClinicalImpressionSupportingInfoModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        reference="Observation/160002",
        reference_type="Observation",
        reference_id=160002,
        display="Blood pressure recording",
    )

    note = ClinicalImpressionNoteModel(
        id=1,
        clinical_impression_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        author_string="Dr. Alice Smith",
        time=D,
        text="Patient advised to take NSAIDs as needed.",
    )

    m = _clinical_impression(
        status_reason_text="Treatment completed successfully",
        code_text="Initial cardiac evaluation",
        encounter_reference="Encounter/20001",
        encounter_type=EncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="ER Encounter",
        assessor_reference="Practitioner/30001",
        assessor_type=ClinicalImpressionAssessorReferenceType.Practitioner,
        assessor_id=30001,
        assessor_display="Dr. Alice Smith",
        previous_reference="ClinicalImpression/530000",
        previous_type=ClinicalImpressionPreviousReferenceType.ClinicalImpression,
        previous_id=530000,
        previous_display="Previous triage impression",
        summary="Patient stable, non-cardiac chest pain confirmed.",
        extension=[{"url": "http://example.org/ext", "valueString": "test-extension"}],
        identifiers=[ident],
        status_reason_codings=[status_reason_coding],
        code_codings=[code_coding],
        problems=[problem],
        investigations=[inv],
        protocols=[protocol],
        findings=[finding],
        prognosis_codeable_concepts=[prog_cc],
        prognosis_references=[prog_ref],
        supporting_info=[supp_info],
        notes=[note],
    )

    resource = to_fhir_clinical_impression(m)
    assert_valid(clinical_impression_pb2.ClinicalImpression, resource)

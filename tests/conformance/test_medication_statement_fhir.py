"""FHIR R4 conformance for `to_fhir_medication_statement()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_statement import to_fhir_medication_statement
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.medication_statement import (
    MedicationStatementBasedOn,
    MedicationStatementBasedOnReferenceType,
    MedicationStatementCategoryCoding,
    MedicationStatementContextReferenceType,
    MedicationStatementDerivedFrom,
    MedicationStatementDosage,
    MedicationStatementDosageAdditionalInstruction,
    MedicationStatementDosageAdditionalInstructionCoding,
    MedicationStatementDosageAsNeededCoding,
    MedicationStatementDosageMethodCoding,
    MedicationStatementDosageRouteCoding,
    MedicationStatementDosageSiteCoding,
    MedicationStatementIdentifier,
    MedicationStatementIdentifierTypeCoding,
    MedicationStatementInformationSourceReferenceType,
    MedicationStatementMedicationCoding,
    MedicationStatementMedicationReferenceType,
    MedicationStatementModel,
    MedicationStatementNote,
    MedicationStatementNoteAuthorReferenceType,
    MedicationStatementPartOf,
    MedicationStatementPartOfReferenceType,
    MedicationStatementReasonCode,
    MedicationStatementReasonCodeCoding,
    MedicationStatementReasonReference,
    MedicationStatementReasonReferenceType,
    MedicationStatementStatus,
    MedicationStatementStatusReason,
    MedicationStatementStatusReasonCoding,
    MedicationStatementSubjectReferenceType,
)

from .support import assert_valid

medication_statement_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_statement_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "based_on",
    "part_of",
    "status_reasons",
    "category_codings",
    "medication_codings",
    "derived_from",
    "reason_codes",
    "reason_references",
    "notes",
    "dosages",
)


def _medication_statement(**overrides) -> MedicationStatementModel:
    fields = {
        "id": 1,
        "medication_statement_id": 500001,
        "tenant_id": "org-test",
        "status": MedicationStatementStatus.active,
        "medication_codeable_concept_text": "Amoxicillin 500mg capsule",
        "subject_reference": "Patient/10001",
        "subject_type": MedicationStatementSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MedicationStatementModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_medication_statement_minimal_conformance():
    m = _medication_statement()
    m.medication_codings = [
        MedicationStatementMedicationCoding(
            medication_statement_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin 500mg capsule",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_medication_statement(m)
    assert_valid(medication_statement_pb2.MedicationStatement, fhir)


def test_medication_statement_full_conformance():
    ident = MedicationStatementIdentifier(
        medication_statement_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="MRN",
        system="http://hospital.example.org",
        value="MS-001",
        created_by="u-test",
    )
    ident.type_codings = [
        MedicationStatementIdentifierTypeCoding(
            medication_statement_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]

    med_coding = MedicationStatementMedicationCoding(
        medication_statement_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="372687004",
        display="Amoxicillin 500mg capsule",
        created_by="u-test",
    )

    cat_coding = MedicationStatementCategoryCoding(
        medication_statement_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/medication-statement-category",
        code="inpatient",
        display="Inpatient",
        created_by="u-test",
    )

    status_reason = MedicationStatementStatusReason(
        medication_statement_pk=1,
        tenant_id="org-test",
        text="Treatment completed",
        created_by="u-test",
    )
    status_reason.codings = [
        MedicationStatementStatusReasonCoding(
            medication_statement_status_reason_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="182992009",
            display="Treatment completed",
            created_by="u-test",
        )
    ]

    based_on = MedicationStatementBasedOn(
        medication_statement_pk=1,
        tenant_id="org-test",
        reference_reference="MedicationRequest/90001",
        reference_type=MedicationStatementBasedOnReferenceType.MedicationRequest,
        reference_id=90001,
        created_by="u-test",
    )

    part_of = MedicationStatementPartOf(
        medication_statement_pk=1,
        tenant_id="org-test",
        reference_reference="Procedure/100001",
        reference_type=MedicationStatementPartOfReferenceType.Procedure,
        reference_id=100001,
        created_by="u-test",
    )

    derived_from = MedicationStatementDerivedFrom(
        medication_statement_pk=1,
        tenant_id="org-test",
        reference_reference="Observation/160001",
        reference_type="Observation",
        reference_id=160001,
        created_by="u-test",
    )

    reason_code = MedicationStatementReasonCode(
        medication_statement_pk=1,
        tenant_id="org-test",
        text="Bacterial infection",
        created_by="u-test",
    )
    reason_code.codings = [
        MedicationStatementReasonCodeCoding(
            medication_statement_reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="87628006",
            display="Bacterial infectious disease",
            created_by="u-test",
        )
    ]

    reason_ref = MedicationStatementReasonReference(
        medication_statement_pk=1,
        tenant_id="org-test",
        reference_reference="Condition/120001",
        reference_type=MedicationStatementReasonReferenceType.Condition,
        reference_id=120001,
        created_by="u-test",
    )

    note = MedicationStatementNote(
        medication_statement_pk=1,
        tenant_id="org-test",
        text="Patient tolerated medication well without adverse reactions.",
        time=D,
        author_string="Dr. Alice Smith",
        created_by="u-test",
    )

    dosage = MedicationStatementDosage(
        medication_statement_pk=1,
        tenant_id="org-test",
        sequence=1,
        text="Take 1 capsule by mouth three times daily with meals.",
        timing={"code": {"text": "TID"}},
        as_needed_boolean=False,
        route_text="Oral",
        created_by="u-test",
    )
    dosage.additional_instructions = [
        MedicationStatementDosageAdditionalInstruction(
            medication_statement_dosage_id=1,
            tenant_id="org-test",
            text="Take with food",
            created_by="u-test",
        )
    ]
    dosage.site_codings = [
        MedicationStatementDosageSiteCoding(
            medication_statement_dosage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="181220002",
            display="Entire oral cavity",
            created_by="u-test",
        )
    ]
    dosage.route_codings = [
        MedicationStatementDosageRouteCoding(
            medication_statement_dosage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="260548002",
            display="Oral",
            created_by="u-test",
        )
    ]
    dosage.method_codings = [
        MedicationStatementDosageMethodCoding(
            medication_statement_dosage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="738995006",
            display="Swallow",
            created_by="u-test",
        )
    ]
    dosage.as_needed_codings = []

    m = _medication_statement(
        effective_date_time=D,
        date_asserted=D,
        context_reference="Encounter/20001",
        context_type=MedicationStatementContextReferenceType.Encounter,
        context_id=20001,
        information_source_reference="Practitioner/30001",
        information_source_type=MedicationStatementInformationSourceReferenceType.Practitioner,
        information_source_id=30001,
        identifiers=[ident],
        based_on=[based_on],
        part_of=[part_of],
        status_reasons=[status_reason],
        category_codings=[cat_coding],
        medication_codings=[med_coding],
        derived_from=[derived_from],
        reason_codes=[reason_code],
        reason_references=[reason_ref],
        notes=[note],
        dosages=[dosage],
    )

    fhir = to_fhir_medication_statement(m)
    assert_valid(medication_statement_pb2.MedicationStatement, fhir)

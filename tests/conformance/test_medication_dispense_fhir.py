"""FHIR R4 conformance for `to_fhir_medication_dispense()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt
from decimal import Decimal

import pytest

from app.fhir.mappers.medication_dispense import to_fhir_medication_dispense
from app.models.enums import IdentifierUse
from app.models.medication_dispense import (
    MedicationDispenseAuthorizingPrescription,
    MedicationDispenseAuthorizingPrescriptionReferenceType,
    MedicationDispenseCategoryCoding,
    MedicationDispenseContextReferenceType,
    MedicationDispenseDestinationReferenceType,
    MedicationDispenseDetectedIssue,
    MedicationDispenseDetectedIssueReferenceType,
    MedicationDispenseDosageAdditionalInstruction,
    MedicationDispenseDosageAdditionalInstructionCoding,
    MedicationDispenseDosageAsNeededCoding,
    MedicationDispenseDosageInstruction,
    MedicationDispenseDosageMethodCoding,
    MedicationDispenseDosageRouteCoding,
    MedicationDispenseDosageSiteCoding,
    MedicationDispenseEventHistory,
    MedicationDispenseEventHistoryReferenceType,
    MedicationDispenseIdentifier,
    MedicationDispenseIdentifierTypeCoding,
    MedicationDispenseLocationReferenceType,
    MedicationDispenseMedicationCoding,
    MedicationDispenseMedicationReferenceType,
    MedicationDispenseModel,
    MedicationDispenseNote,
    MedicationDispenseNoteAuthorReferenceType,
    MedicationDispensePartOf,
    MedicationDispensePartOfReferenceType,
    MedicationDispensePerformer,
    MedicationDispensePerformerActorReferenceType,
    MedicationDispensePerformerFunctionCoding,
    MedicationDispenseReceiver,
    MedicationDispenseReceiverReferenceType,
    MedicationDispenseStatus,
    MedicationDispenseStatusReasonCoding,
    MedicationDispenseStatusReasonReferenceType,
    MedicationDispenseSubjectReferenceType,
    MedicationDispenseSubstitutionReason,
    MedicationDispenseSubstitutionReasonCoding,
    MedicationDispenseSubstitutionResponsibleParty,
    MedicationDispenseSubstitutionResponsiblePartyReferenceType,
    MedicationDispenseSubstitutionTypeCoding,
    MedicationDispenseSupportingInfo,
    MedicationDispenseTypeCoding,
)

from .support import assert_valid

medication_dispense_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_dispense_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "part_of",
    "status_reason_codings",
    "category_codings",
    "medication_codings",
    "supporting_informations",
    "performers",
    "authorizing_prescriptions",
    "type_codings",
    "receivers",
    "notes",
    "dosage_instructions",
    "substitution_type_codings",
    "substitution_reasons",
    "substitution_responsible_parties",
    "detected_issues",
    "event_history",
)


def _medication_dispense(**overrides) -> MedicationDispenseModel:
    fields = {
        "id": 1,
        "medication_dispense_id": 590001,
        "tenant_id": "org-test",
        "status": MedicationDispenseStatus.completed,
        "medication_codeable_concept_text": "Amoxicillin 500mg capsule",
        "subject_reference": "Patient/10001",
        "subject_type": MedicationDispenseSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MedicationDispenseModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_medication_dispense_minimal_conformance():
    m = _medication_dispense()
    m.medication_codings = [
        MedicationDispenseMedicationCoding(
            medication_dispense_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin 500mg capsule",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_medication_dispense(m)
    assert_valid(medication_dispense_pb2.MedicationDispense, fhir)


def test_medication_dispense_full_conformance():
    ident = MedicationDispenseIdentifier(
        medication_dispense_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="MRN",
        system="http://hospital.example.org",
        value="MD-001",
        created_by="u-test",
    )
    ident.type_codings = [
        MedicationDispenseIdentifierTypeCoding(
            medication_dispense_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]

    med_coding = MedicationDispenseMedicationCoding(
        medication_dispense_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="372687004",
        display="Amoxicillin 500mg capsule",
        created_by="u-test",
    )

    cat_coding = MedicationDispenseCategoryCoding(
        medication_dispense_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/medicationdispense-category",
        code="inpatient",
        display="Inpatient",
        created_by="u-test",
    )

    status_reason_coding = MedicationDispenseStatusReasonCoding(
        medication_dispense_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/medicationdispense-status-reason",
        code="frr01",
        display="Order Stopped",
        created_by="u-test",
    )

    type_coding = MedicationDispenseTypeCoding(
        medication_dispense_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
        code="FF",
        display="First Fill",
        created_by="u-test",
    )

    part_of = MedicationDispensePartOf(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="Procedure/100001",
        reference_type=MedicationDispensePartOfReferenceType.Procedure,
        reference_id=100001,
        created_by="u-test",
    )

    supp_info = MedicationDispenseSupportingInfo(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="Observation/160001",
        reference_type="Observation",
        reference_id=160001,
        created_by="u-test",
    )

    performer = MedicationDispensePerformer(
        medication_dispense_pk=1,
        tenant_id="org-test",
        actor_reference="Practitioner/30001",
        actor_type=MedicationDispensePerformerActorReferenceType.Practitioner,
        actor_id=30001,
        actor_display="Dr. Bob Jones",
        function_text="Packager",
        created_by="u-test",
    )
    performer.function_codings = [
        MedicationDispensePerformerFunctionCoding(
            medication_dispense_performer_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
            code="packager",
            display="Packager",
            created_by="u-test",
        )
    ]

    authorizing_prescription = MedicationDispenseAuthorizingPrescription(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="MedicationRequest/90001",
        reference_type=MedicationDispenseAuthorizingPrescriptionReferenceType.MedicationRequest,
        reference_id=90001,
        created_by="u-test",
    )

    receiver = MedicationDispenseReceiver(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="Patient/10001",
        reference_type=MedicationDispenseReceiverReferenceType.Patient,
        reference_id=10001,
        created_by="u-test",
    )

    note = MedicationDispenseNote(
        medication_dispense_pk=1,
        tenant_id="org-test",
        text="Patient counseled on completing full course.",
        time=D,
        author_string="Pharmacist Alice",
        created_by="u-test",
    )

    dosage = MedicationDispenseDosageInstruction(
        medication_dispense_pk=1,
        tenant_id="org-test",
        sequence=1,
        text="Take 1 capsule by mouth three times daily for 10 days",
        timing={"code": {"text": "TID"}},
        as_needed_boolean=False,
        site_text="Oral cavity",
        route_text="Oral",
        method_text="Swallow",
        max_dose_per_administration_value=Decimal("500"),
        max_dose_per_administration_unit="mg",
        max_dose_per_administration_system="http://unitsofmeasure.org",
        max_dose_per_administration_code="mg",
        created_by="u-test",
    )
    dosage.site_codings = [
        MedicationDispenseDosageSiteCoding(
            medication_dispense_dosage_instruction_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="181220002",
            display="Oral cavity",
            created_by="u-test",
        )
    ]
    dosage.route_codings = [
        MedicationDispenseDosageRouteCoding(
            medication_dispense_dosage_instruction_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="260548002",
            display="Oral",
            created_by="u-test",
        )
    ]
    dosage.method_codings = [
        MedicationDispenseDosageMethodCoding(
            medication_dispense_dosage_instruction_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="738995006",
            display="Swallow",
            created_by="u-test",
        )
    ]

    sub_type_coding = MedicationDispenseSubstitutionTypeCoding(
        medication_dispense_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
        code="G",
        display="Generic Composition",
        created_by="u-test",
    )

    sub_reason = MedicationDispenseSubstitutionReason(
        medication_dispense_pk=1,
        tenant_id="org-test",
        text="Formulary policy",
        created_by="u-test",
    )
    sub_reason.codings = [
        MedicationDispenseSubstitutionReasonCoding(
            medication_dispense_substitution_reason_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActSubstanceAdminSubstitutionReason",
            code="FP",
            display="Formulary Policy",
            created_by="u-test",
        )
    ]

    sub_party = MedicationDispenseSubstitutionResponsibleParty(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30001",
        reference_type=MedicationDispenseSubstitutionResponsiblePartyReferenceType.Practitioner,
        reference_id=30001,
        created_by="u-test",
    )

    detected_issue = MedicationDispenseDetectedIssue(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="DetectedIssue/540001",
        reference_type=MedicationDispenseDetectedIssueReferenceType.DetectedIssue,
        reference_id=540001,
        created_by="u-test",
    )

    event_history = MedicationDispenseEventHistory(
        medication_dispense_pk=1,
        tenant_id="org-test",
        reference_reference="Provenance/270001",
        reference_type=MedicationDispenseEventHistoryReferenceType.Provenance,
        reference_id=270001,
        created_by="u-test",
    )

    m = _medication_dispense(
        category_text="Inpatient",
        status_reason_codeable_concept_text="Order Stopped",
        type_text="First Fill",
        context_reference="Encounter/20001",
        context_type=MedicationDispenseContextReferenceType.Encounter,
        context_id=20001,
        location_reference="Location/230001",
        location_type=MedicationDispenseLocationReferenceType.Location,
        location_id=230001,
        destination_reference="Location/230002",
        destination_type=MedicationDispenseDestinationReferenceType.Location,
        destination_id=230002,
        quantity_value=Decimal("30"),
        quantity_unit="capsule",
        quantity_system="http://unitsofmeasure.org",
        quantity_code="capsule",
        days_supply_value=Decimal("10"),
        days_supply_unit="d",
        days_supply_system="http://unitsofmeasure.org",
        days_supply_code="d",
        when_prepared=D,
        when_handed_over=D,
        substitution_was_substituted=True,
        substitution_type_text="Generic Composition",
        identifiers=[ident],
        part_of=[part_of],
        status_reason_codings=[status_reason_coding],
        category_codings=[cat_coding],
        medication_codings=[med_coding],
        supporting_informations=[supp_info],
        performers=[performer],
        authorizing_prescriptions=[authorizing_prescription],
        type_codings=[type_coding],
        receivers=[receiver],
        notes=[note],
        dosage_instructions=[dosage],
        substitution_type_codings=[sub_type_coding],
        substitution_reasons=[sub_reason],
        substitution_responsible_parties=[sub_party],
        detected_issues=[detected_issue],
        event_history=[event_history],
    )

    fhir = to_fhir_medication_dispense(m)
    assert_valid(medication_dispense_pb2.MedicationDispense, fhir)

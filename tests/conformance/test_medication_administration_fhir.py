"""FHIR R4 conformance for `to_fhir_medication_administration()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_administration import to_fhir_medication_administration
from app.models.enums import IdentifierUse
from app.models.medication_administration import (
    MedicationAdministrationCategoryCoding,
    MedicationAdministrationDevice,
    MedicationAdministrationDeviceReferenceType,
    MedicationAdministrationDosageMethodCoding,
    MedicationAdministrationDosageRouteCoding,
    MedicationAdministrationDosageSiteCoding,
    MedicationAdministrationEventHistory,
    MedicationAdministrationIdentifier,
    MedicationAdministrationIdentifierTypeCoding,
    MedicationAdministrationMedicationCoding,
    MedicationAdministrationModel,
    MedicationAdministrationNote,
    MedicationAdministrationPartOf,
    MedicationAdministrationPartOfReferenceType,
    MedicationAdministrationPerformer,
    MedicationAdministrationPerformerActorReferenceType,
    MedicationAdministrationPerformerFunctionCoding,
    MedicationAdministrationReasonCode,
    MedicationAdministrationReasonCodeCoding,
    MedicationAdministrationReasonReference,
    MedicationAdministrationReasonReferenceType,
    MedicationAdministrationStatus,
    MedicationAdministrationStatusReason,
    MedicationAdministrationStatusReasonCoding,
    MedicationAdministrationSubjectReferenceType,
    MedicationAdministrationSupportingInformation,
)

from .support import assert_valid

medication_administration_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_administration_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "part_of",
    "status_reasons",
    "category_codings",
    "medication_codings",
    "supporting_informations",
    "performers",
    "reason_codes",
    "reason_references",
    "devices",
    "notes",
    "event_history",
    "dosage_site_codings",
    "dosage_route_codings",
    "dosage_method_codings",
)


def _medication_administration(**overrides) -> MedicationAdministrationModel:
    fields = {
        "id": 1,
        "medication_administration_id": 580001,
        "tenant_id": "org-test",
        "status": MedicationAdministrationStatus.completed,
        "medication_codeable_concept_text": "Amoxicillin 500mg capsule",
        "subject_reference": "Patient/10001",
        "subject_type": MedicationAdministrationSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "effective_date_time": D,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MedicationAdministrationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_medication_administration_minimal_conformance():
    m = _medication_administration()
    m.medication_codings = [
        MedicationAdministrationMedicationCoding(
            medication_administration_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin 500mg capsule",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_medication_administration(m)
    assert_valid(medication_administration_pb2.MedicationAdministration, fhir)


def test_medication_administration_full_conformance():
    ident = MedicationAdministrationIdentifier(
        medication_administration_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="MRN",
        system="http://hospital.example.org",
        value="MA-001",
        created_by="u-test",
    )
    ident.type_codings = [
        MedicationAdministrationIdentifierTypeCoding(
            medication_administration_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]

    med_coding = MedicationAdministrationMedicationCoding(
        medication_administration_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="372687004",
        display="Amoxicillin 500mg capsule",
        created_by="u-test",
    )

    cat_coding = MedicationAdministrationCategoryCoding(
        medication_administration_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/medication-admin-category",
        code="inpatient",
        display="Inpatient",
        created_by="u-test",
    )

    status_reason = MedicationAdministrationStatusReason(
        medication_administration_pk=1,
        tenant_id="org-test",
        text="Treatment completed normally",
        created_by="u-test",
    )
    status_reason.codings = [
        MedicationAdministrationStatusReasonCoding(
            medication_administration_status_reason_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="182992009",
            display="Treatment completed",
            created_by="u-test",
        )
    ]

    part_of = MedicationAdministrationPartOf(
        medication_administration_pk=1,
        tenant_id="org-test",
        reference_reference="Procedure/100001",
        reference_type=MedicationAdministrationPartOfReferenceType.Procedure,
        reference_id=100001,
        created_by="u-test",
    )

    supp_info = MedicationAdministrationSupportingInformation(
        medication_administration_pk=1,
        tenant_id="org-test",
        reference_reference="Observation/160001",
        reference_type="Observation",
        reference_id=160001,
        created_by="u-test",
    )

    performer = MedicationAdministrationPerformer(
        medication_administration_pk=1,
        tenant_id="org-test",
        actor_reference="Practitioner/30001",
        actor_type=MedicationAdministrationPerformerActorReferenceType.Practitioner,
        actor_id=30001,
        actor_display="Dr. Bob Jones",
        function_text="Administering Provider",
        created_by="u-test",
    )
    performer.function_codings = [
        MedicationAdministrationPerformerFunctionCoding(
            medication_administration_performer_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/med-admin-perform-function",
            code="performer",
            display="Performer",
            created_by="u-test",
        )
    ]

    reason_code = MedicationAdministrationReasonCode(
        medication_administration_pk=1,
        tenant_id="org-test",
        text="Bacterial infection",
        created_by="u-test",
    )
    reason_code.codings = [
        MedicationAdministrationReasonCodeCoding(
            medication_administration_reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="87628006",
            display="Bacterial infectious disease",
            created_by="u-test",
        )
    ]

    reason_ref = MedicationAdministrationReasonReference(
        medication_administration_pk=1,
        tenant_id="org-test",
        reference_reference="Condition/120001",
        reference_type=MedicationAdministrationReasonReferenceType.Condition,
        reference_id=120001,
        created_by="u-test",
    )

    device = MedicationAdministrationDevice(
        medication_administration_pk=1,
        tenant_id="org-test",
        reference_reference="Device/130001",
        reference_type=MedicationAdministrationDeviceReferenceType.Device,
        reference_id=130001,
        created_by="u-test",
    )

    note = MedicationAdministrationNote(
        medication_administration_pk=1,
        tenant_id="org-test",
        text="Infusion completed with no adverse reaction.",
        time=D,
        author_string="Nurse Alice",
        created_by="u-test",
    )

    event_hist = MedicationAdministrationEventHistory(
        medication_administration_pk=1,
        tenant_id="org-test",
        reference_reference="Provenance/270001",
        reference_type="Provenance",
        reference_id=270001,
        created_by="u-test",
    )

    site_coding = MedicationAdministrationDosageSiteCoding(
        medication_administration_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="181220002",
        display="Entire oral cavity",
        created_by="u-test",
    )

    route_coding = MedicationAdministrationDosageRouteCoding(
        medication_administration_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="260548002",
        display="Oral",
        created_by="u-test",
    )

    method_coding = MedicationAdministrationDosageMethodCoding(
        medication_administration_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="738995006",
        display="Swallow",
        created_by="u-test",
    )

    m = _medication_administration(
        status=MedicationAdministrationStatus.completed,
        category_text="Inpatient",
        category_codings=[cat_coding],
        medication_codings=[med_coding],
        context_reference="Encounter/20001",
        context_type="Encounter",
        context_id=20001,
        request_reference="MedicationRequest/90001",
        request_type="MedicationRequest",
        request_id=90001,
        instantiates=["http://example.org/protocol/amoxicillin-protocol"],
        identifiers=[ident],
        part_of=[part_of],
        status_reasons=[status_reason],
        supporting_informations=[supp_info],
        performers=[performer],
        reason_codes=[reason_code],
        reason_references=[reason_ref],
        devices=[device],
        notes=[note],
        event_history=[event_hist],
        dosage_text="Take 500mg oral capsule by mouth with water",
        dosage_site_text="Oral cavity",
        dosage_site_codings=[site_coding],
        dosage_route_text="Oral",
        dosage_route_codings=[route_coding],
        dosage_method_text="Swallow",
        dosage_method_codings=[method_coding],
        dosage_dose_value=500.0,
        dosage_dose_unit="mg",
        dosage_dose_system="http://unitsofmeasure.org",
        dosage_dose_code="mg",
        dosage_rate_quantity_value=50.0,
        dosage_rate_quantity_unit="mg/h",
        dosage_rate_quantity_system="http://unitsofmeasure.org",
        dosage_rate_quantity_code="mg/h",
    )

    fhir = to_fhir_medication_administration(m)
    assert_valid(medication_administration_pb2.MedicationAdministration, fhir)

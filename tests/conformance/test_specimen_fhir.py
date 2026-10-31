"""FHIR R4 conformance for `to_fhir_specimen()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.specimen import to_fhir_specimen
from app.models.enums import IdentifierUse, OrganizationReferenceType, ServiceRequestReferenceType
from app.models.specimen import (
    SpecimenAccessionIdentifierTypeCoding,
    SpecimenAdditiveReferenceType,
    SpecimenCollectionBodySiteCoding,
    SpecimenCollectionFastingStatusCoding,
    SpecimenCollectionMethodCoding,
    SpecimenCollectorReferenceType,
    SpecimenCondition,
    SpecimenConditionCoding,
    SpecimenContainer,
    SpecimenContainerAdditiveCoding,
    SpecimenContainerIdentifier,
    SpecimenContainerIdentifierTypeCoding,
    SpecimenContainerTypeCoding,
    SpecimenIdentifier,
    SpecimenIdentifierTypeCoding,
    SpecimenModel,
    SpecimenNote,
    SpecimenNoteAuthorReferenceType,
    SpecimenParent,
    SpecimenParentReferenceType,
    SpecimenProcessing,
    SpecimenProcessingAdditive,
    SpecimenProcessingProcedureCoding,
    SpecimenQuantityComparator as SpecimenQuantityComparatorModel,
    SpecimenRequest,
    SpecimenStatus,
    SpecimenSubjectReferenceType,
    SpecimenTypeCoding,
)

from .support import assert_valid

specimen_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.specimen_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "accession_identifier_type_codings",
    "type_codings",
    "parents",
    "requests",
    "collection_method_codings",
    "collection_body_site_codings",
    "collection_fasting_status_codings",
    "processings",
    "containers",
    "conditions",
    "notes",
)


def _specimen(**overrides) -> SpecimenModel:
    fields = {
        "id": 1,
        "specimen_id": 310001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    s = SpecimenModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(s, attr, None) is None:
            setattr(s, attr, [])
    return s


def test_minimal_specimen_conforms():
    s = _specimen()
    out = to_fhir_specimen(s)
    assert out["resourceType"] == "Specimen"
    assert out["id"] == "310001"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_status():
    for status_val in [
        SpecimenStatus.available,
        SpecimenStatus.unavailable,
        SpecimenStatus.unsatisfactory,
        SpecimenStatus.entered_in_error,
    ]:
        s = _specimen(status=status_val)
        out = to_fhir_specimen(s)
        assert out["status"] == status_val.value
        assert_valid(specimen_pb2.Specimen, out)


def test_specimen_type():
    s = _specimen(type_text="Venous blood")
    s.type_codings = [
        SpecimenTypeCoding(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="122555007",
            display="Venous blood specimen",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_specimen(s)
    assert out["type"]["text"] == "Venous blood"
    assert out["type"]["coding"][0]["code"] == "122555007"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_subject():
    for ref_type, display in [
        (SpecimenSubjectReferenceType.Patient, "Patient Doe"),
        (SpecimenSubjectReferenceType.Group, "Group A"),
        (SpecimenSubjectReferenceType.Device, "Centrifuge"),
        (SpecimenSubjectReferenceType.Substance, "Chemical"),
        (SpecimenSubjectReferenceType.Location, "Room 101"),
    ]:
        s = _specimen(
            subject_reference=f"{ref_type.value}/10001",
            subject_type=ref_type,
            subject_id=10001,
            subject_display=display,
        )
        out = to_fhir_specimen(s)
        assert out["subject"]["reference"] == f"{ref_type.value}/10001"
        assert out["subject"]["display"] == display
        assert_valid(specimen_pb2.Specimen, out)


def test_specimen_identifiers_and_accession():
    s = _specimen(
        accession_identifier_use=IdentifierUse.official,
        accession_identifier_system="http://lab.example.org/accession",
        accession_identifier_value="ACC-2026-001",
        accession_identifier_type_text="Accession ID",
        accession_identifier_period_start=D,
        accession_identifier_assigner_reference="Organization/190001",
        accession_identifier_assigner_type=OrganizationReferenceType.Organization,
        accession_identifier_assigner_id=190001,
        accession_identifier_assigner_display="Central Lab",
    )
    s.accession_identifier_type_codings = [
        SpecimenAccessionIdentifierTypeCoding(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="ACSN",
            display="Accession ID",
            created_by="u-test",
            created_at=D,
        )
    ]
    ident = SpecimenIdentifier(
        id=1,
        specimen_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.usual,
        system="http://lab.example.org/specimens",
        value="SPEC-001",
        type_text="Specimen Identifier",
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Central Lab",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        SpecimenIdentifierTypeCoding(
            id=1,
            specimen_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
            created_at=D,
        )
    ]
    s.identifiers = [ident]

    out = to_fhir_specimen(s)
    assert out["accessionIdentifier"]["value"] == "ACC-2026-001"
    assert out["accessionIdentifier"]["type"]["coding"][0]["code"] == "ACSN"
    assert out["identifier"][0]["value"] == "SPEC-001"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_parent_and_request():
    s = _specimen()
    s.parents = [
        SpecimenParent(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            reference_reference="Specimen/310000",
            reference_type=SpecimenParentReferenceType.Specimen,
            reference_id=310000,
            reference_display="Parent Specimen",
            created_by="u-test",
            created_at=D,
        )
    ]
    s.requests = [
        SpecimenRequest(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            reference_reference="ServiceRequest/80001",
            reference_type=ServiceRequestReferenceType.ServiceRequest,
            reference_id=80001,
            reference_display="Lab Order",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_specimen(s)
    assert out["parent"][0]["reference"] == "Specimen/310000"
    assert out["request"][0]["reference"] == "ServiceRequest/80001"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_received_time():
    s = _specimen(received_time=D)
    out = to_fhir_specimen(s)
    assert "2026-01-01" in out["receivedTime"]
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_collection_full():
    s = _specimen(
        collection_collector_reference="Practitioner/30001",
        collection_collector_type=SpecimenCollectorReferenceType.Practitioner,
        collection_collector_id=30001,
        collection_collector_display="Dr. Alice",
        collection_collected_date_time=D,
        collection_duration_value=15.0,
        collection_duration_comparator=SpecimenQuantityComparatorModel.le,
        collection_duration_unit="min",
        collection_duration_system="http://unitsofmeasure.org",
        collection_duration_code="min",
        collection_quantity_value=10.0,
        collection_quantity_unit="mL",
        collection_quantity_system="http://unitsofmeasure.org",
        collection_quantity_code="mL",
        collection_method_text="Venipuncture",
        collection_body_site_text="Right antecubital fossa",
        collection_fasting_status_text="Fasting 12 hours",
    )
    s.collection_method_codings = [
        SpecimenCollectionMethodCoding(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="28520004",
            display="Venipuncture",
            created_by="u-test",
            created_at=D,
        )
    ]
    s.collection_body_site_codings = [
        SpecimenCollectionBodySiteCoding(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="368208006",
            display="Left arm structure",
            created_by="u-test",
            created_at=D,
        )
    ]
    s.collection_fasting_status_codings = [
        SpecimenCollectionFastingStatusCoding(
            id=1,
            specimen_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0255",
            code="F",
            display="Patient was fasting prior to the procedure.",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_specimen(s)
    col = out["collection"]
    assert col["collector"]["reference"] == "Practitioner/30001"
    assert col["duration"]["comparator"] == "<="
    assert col["duration"]["value"] == 15.0
    assert col["quantity"]["value"] == 10.0
    assert col["method"]["coding"][0]["code"] == "28520004"
    assert col["bodySite"]["coding"][0]["code"] == "368208006"
    assert col["fastingStatusCodeableConcept"]["coding"][0]["code"] == "F"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_collection_period_and_fasting_duration():
    s = _specimen(
        collection_collected_period_start=D,
        collection_collected_period_end=D + dt.timedelta(hours=1),
        collection_fasting_status_duration_value=12.0,
        collection_fasting_status_duration_comparator=SpecimenQuantityComparatorModel.ge,
        collection_fasting_status_duration_unit="h",
        collection_fasting_status_duration_system="http://unitsofmeasure.org",
        collection_fasting_status_duration_code="h",
    )
    out = to_fhir_specimen(s)
    col = out["collection"]
    assert "start" in col["collectedPeriod"]
    assert col["fastingStatusDuration"]["value"] == 12.0
    assert col["fastingStatusDuration"]["comparator"] == ">="
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_processing():
    proc = SpecimenProcessing(
        id=1,
        specimen_pk=1,
        tenant_id="org-test",
        description="Centrifugation",
        procedure_text="Centrifugation",
        time_date_time=D,
        created_by="u-test",
        created_at=D,
    )
    proc.procedure_codings = [
        SpecimenProcessingProcedureCoding(
            id=1,
            specimen_processing_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="84918000",
            display="Centrifugation",
            created_by="u-test",
            created_at=D,
        )
    ]
    proc.additives = [
        SpecimenProcessingAdditive(
            id=1,
            specimen_processing_id=1,
            tenant_id="org-test",
            reference_reference="Substance/5001",
            reference_type=SpecimenAdditiveReferenceType.Substance,
            reference_id=5001,
            reference_display="Heparin",
            created_by="u-test",
            created_at=D,
        )
    ]
    s = _specimen()
    s.processings = [proc]
    out = to_fhir_specimen(s)
    assert out["processing"][0]["description"] == "Centrifugation"
    assert out["processing"][0]["procedure"]["coding"][0]["code"] == "84918000"
    assert out["processing"][0]["additive"][0]["reference"] == "Substance/5001"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_container():
    cont = SpecimenContainer(
        id=1,
        specimen_pk=1,
        tenant_id="org-test",
        description="Red top tube",
        type_text="Blood tube",
        capacity_value=10.0,
        capacity_unit="mL",
        capacity_system="http://unitsofmeasure.org",
        capacity_code="mL",
        specimen_quantity_value=8.0,
        specimen_quantity_unit="mL",
        specimen_quantity_system="http://unitsofmeasure.org",
        specimen_quantity_code="mL",
        additive_codeable_concept_text="EDTA",
        additive_reference_reference="Substance/5002",
        additive_reference_type=SpecimenAdditiveReferenceType.Substance,
        additive_reference_id=5002,
        additive_reference_display="EDTA solution",
        created_by="u-test",
        created_at=D,
    )
    c_ident = SpecimenContainerIdentifier(
        id=1,
        specimen_container_id=1,
        tenant_id="org-test",
        value="CONT-001",
        system="http://lab.example.org/containers",
        created_by="u-test",
        created_at=D,
    )
    c_ident.type_codings = []
    cont.identifiers = [c_ident]
    cont.type_codings = [
        SpecimenContainerTypeCoding(
            id=1,
            specimen_container_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="706053007",
            display="General specimen container",
            created_by="u-test",
            created_at=D,
        )
    ]
    cont.additive_codings = [
        SpecimenContainerAdditiveCoding(
            id=1,
            specimen_container_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0371",
            code="EDTK",
            display="Potassium/K EDTA",
            created_by="u-test",
            created_at=D,
        )
    ]
    s = _specimen()
    s.containers = [cont]
    out = to_fhir_specimen(s)
    c_out = out["container"][0]
    assert c_out["identifier"][0]["value"] == "CONT-001"
    assert c_out["capacity"]["value"] == 10.0
    assert c_out["specimenQuantity"]["value"] == 8.0
    assert c_out["additiveCodeableConcept"]["coding"][0]["code"] == "EDTK"
    assert c_out["additiveReference"]["reference"] == "Substance/5002"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_condition():
    cond = SpecimenCondition(
        id=1,
        specimen_pk=1,
        tenant_id="org-test",
        text="Frozen",
        created_by="u-test",
        created_at=D,
    )
    cond.codings = [
        SpecimenConditionCoding(
            id=1,
            specimen_condition_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0493",
            code="FROZ",
            display="Frozen",
            created_by="u-test",
            created_at=D,
        )
    ]
    s = _specimen()
    s.conditions = [cond]
    out = to_fhir_specimen(s)
    assert out["condition"][0]["text"] == "Frozen"
    assert out["condition"][0]["coding"][0]["code"] == "FROZ"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_notes():
    note1 = SpecimenNote(
        id=1,
        specimen_pk=1,
        tenant_id="org-test",
        author_string="Lab Technician",
        time=D,
        text="Hemolyzed sample, results may be affected.",
        created_by="u-test",
        created_at=D,
    )
    note2 = SpecimenNote(
        id=2,
        specimen_pk=1,
        tenant_id="org-test",
        author_reference="Practitioner/30001",
        author_type=SpecimenNoteAuthorReferenceType.Practitioner,
        author_id=30001,
        author_display="Dr. Alice",
        time=D,
        text="Clinical correlation required.",
        created_by="u-test",
        created_at=D,
    )
    s = _specimen()
    s.notes = [note1, note2]
    out = to_fhir_specimen(s)
    assert len(out["note"]) == 2
    assert out["note"][0]["authorString"] == "Lab Technician"
    assert out["note"][1]["authorReference"]["reference"] == "Practitioner/30001"
    assert_valid(specimen_pb2.Specimen, out)


def test_specimen_all_elements_combined():
    s = _specimen(
        status=SpecimenStatus.available,
        type_text="Venous blood",
        subject_reference="Patient/10001",
        subject_type=SpecimenSubjectReferenceType.Patient,
        subject_id=10001,
        subject_display="Jane Doe",
        received_time=D,
        collection_collected_date_time=D,
        collection_quantity_value=5.0,
        collection_quantity_unit="mL",
    )
    out = to_fhir_specimen(s)
    assert out["status"] == "available"
    assert out["subject"]["reference"] == "Patient/10001"
    assert_valid(specimen_pb2.Specimen, out)

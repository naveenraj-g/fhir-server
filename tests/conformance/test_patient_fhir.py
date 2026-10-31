"""FHIR R4 conformance for `to_fhir_patient()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.patient import to_fhir_patient
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.patient import (
    PatientAddress,
    PatientCommunication,
    PatientCommunicationLanguageCoding,
    PatientContact,
    PatientContactRelationship,
    PatientContactRelationshipCoding,
    PatientContactTelecom,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientIdentifierTypeCoding,
    PatientLink,
    PatientMaritalStatusCoding,
    PatientModel,
    PatientName,
    PatientPhoto,
    PatientTelecom,
)
from app.models.patient.enums import (
    PatientGeneralPractitionerReferenceType,
    PatientLinkOtherType,
    PatientLinkType,
)
from app.schemas.enums import (
    AddressType,
    AddressUse,
    AdministrativeGender,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
)

from .support import assert_valid

patient_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.patient_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "names",
    "telecoms",
    "addresses",
    "photos",
    "marital_status_codings",
    "contacts",
    "communications",
    "general_practitioners",
    "links",
)


def _patient(**overrides) -> PatientModel:
    fields = {
        "id": 1,
        "patient_id": 10001,
        "tenant_id": "org-test",
        "user_id": "u-test",
        "active": True,
        "gender": AdministrativeGender.female,
        "birth_date": dt.date(1990, 7, 22),
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    p = PatientModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(p, attr, None) is None:
            setattr(p, attr, [])
    return p


def test_minimal_patient_conforms():
    p = _patient()
    out = to_fhir_patient(p)
    assert out["resourceType"] == "Patient"
    assert out["id"] == "10001"
    assert out["active"] is True
    assert out["gender"] == "female"
    assert out["birthDate"] == "1990-07-22"
    assert_valid(patient_pb2.Patient, out)


def test_deceased_boolean_and_datetime():
    p_bool = _patient(deceased_boolean=True)
    assert_valid(patient_pb2.Patient, to_fhir_patient(p_bool))

    p_dt = _patient(deceased_date_time=D)
    out_dt = to_fhir_patient(p_dt)
    assert out_dt["deceasedDateTime"] == D.isoformat()
    assert_valid(patient_pb2.Patient, out_dt)


def test_multiple_birth():
    p_bool = _patient(multiple_birth_boolean=True)
    assert_valid(patient_pb2.Patient, to_fhir_patient(p_bool))

    p_int = _patient(multiple_birth_integer=2)
    out_int = to_fhir_patient(p_int)
    assert out_int["multipleBirthInteger"] == 2
    assert_valid(patient_pb2.Patient, out_int)


def test_marital_status():
    p = _patient(marital_status_text="Never Married")
    coding = PatientMaritalStatusCoding(
        id=1,
        patient_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
        code="S",
        display="Never Married",
        created_by="u-test",
        created_at=D,
    )
    p.marital_status_codings = [coding]
    out = to_fhir_patient(p)
    assert out["maritalStatus"]["text"] == "Never Married"
    assert out["maritalStatus"]["coding"][0]["code"] == "S"
    assert_valid(patient_pb2.Patient, out)


def test_managing_organization():
    p = _patient(
        managing_organization_reference="Organization/190001",
        managing_organization_type=OrganizationReferenceType.Organization,
        managing_organization_id=190001,
        managing_organization_display="Sunrise Medical Center",
    )
    out = to_fhir_patient(p)
    assert out["managingOrganization"]["reference"] == "Organization/190001"
    assert out["managingOrganization"]["display"] == "Sunrise Medical Center"
    assert_valid(patient_pb2.Patient, out)


def test_names():
    p = _patient()
    p.names = [
        PatientName(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            use=HumanNameUse.official,
            text="Emily Rose Carter",
            family="Carter",
            given=["Emily", "Rose"],
            prefix=["Dr."],
            period_start=D,
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["name"]) == 1
    assert out["name"][0]["family"] == "Carter"
    assert out["name"][0]["given"] == ["Emily", "Rose"]
    assert_valid(patient_pb2.Patient, out)


def test_identifiers():
    p = _patient()
    ident = PatientIdentifier(
        id=1,
        patient_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.com/mrn",
        value="MRN-12345",
        type_text="Medical Record Number",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        PatientIdentifierTypeCoding(
            id=1,
            patient_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical record number",
            created_by="u-test",
            created_at=D,
        )
    ]
    p.identifiers = [ident]
    out = to_fhir_patient(p)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "MRN-12345"
    assert_valid(patient_pb2.Patient, out)


def test_telecoms():
    p = _patient()
    p.telecoms = [
        PatientTelecom(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            system=ContactPointSystem.phone,
            value="+1-555-123-4567",
            use=ContactPointUse.mobile,
            rank=1,
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["telecom"]) == 1
    assert out["telecom"][0]["value"] == "+1-555-123-4567"
    assert_valid(patient_pb2.Patient, out)


def test_addresses():
    p = _patient()
    p.addresses = [
        PatientAddress(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            use=AddressUse.home,
            type=AddressType.physical,
            line=["123 Main St", "Apt 4B"],
            city="Boston",
            state="MA",
            postal_code="02115",
            country="US",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["address"]) == 1
    assert out["address"][0]["city"] == "Boston"
    assert_valid(patient_pb2.Patient, out)


def test_photos():
    p = _patient()
    p.photos = [
        PatientPhoto(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            content_type="image/jpeg",
            url="https://example.com/photo.jpg",
            title="Profile photo",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["photo"]) == 1
    assert out["photo"][0]["url"] == "https://example.com/photo.jpg"
    assert_valid(patient_pb2.Patient, out)


def test_communication():
    p = _patient()
    comm = PatientCommunication(
        id=1,
        patient_pk=1,
        tenant_id="org-test",
        language_text="English",
        preferred=True,
        created_by="u-test",
        created_at=D,
    )
    comm.language_codings = [
        PatientCommunicationLanguageCoding(
            id=1,
            patient_communication_id=1,
            tenant_id="org-test",
            system="urn:ietf:bcp:47",
            code="en",
            display="English",
            created_by="u-test",
            created_at=D,
        )
    ]
    p.communications = [comm]
    out = to_fhir_patient(p)
    assert len(out["communication"]) == 1
    assert out["communication"][0]["preferred"] is True
    assert_valid(patient_pb2.Patient, out)


def test_general_practitioner():
    p = _patient()
    p.general_practitioners = [
        PatientGeneralPractitioner(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            reference_reference="Practitioner/30001",
            reference_type=PatientGeneralPractitionerReferenceType.Practitioner,
            reference_id=30001,
            reference_display="Dr. Alice Smith",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["generalPractitioner"]) == 1
    assert out["generalPractitioner"][0]["reference"] == "Practitioner/30001"
    assert_valid(patient_pb2.Patient, out)


def test_link():
    p = _patient()
    p.links = [
        PatientLink(
            id=1,
            patient_pk=1,
            tenant_id="org-test",
            other_reference="Patient/10002",
            other_type=PatientLinkOtherType.Patient,
            other_id=10002,
            other_display="Old Patient Record",
            type=PatientLinkType.replaces,
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_patient(p)
    assert len(out["link"]) == 1
    assert out["link"][0]["other"]["reference"] == "Patient/10002"
    assert out["link"][0]["type"] == "replaces"
    assert_valid(patient_pb2.Patient, out)


def test_contacts():
    p = _patient()
    contact = PatientContact(
        id=1,
        patient_pk=1,
        tenant_id="org-test",
        gender=AdministrativeGender.male,
        name_use=HumanNameUse.official,
        name_family="Carter",
        name_given=["Michael"],
        city="Boston",
        country="US",
        organization_reference="Organization/190001",
        created_by="u-test",
        created_at=D,
    )
    rel = PatientContactRelationship(
        id=1,
        contact_id=1,
        tenant_id="org-test",
        text="Next-of-Kin",
        created_by="u-test",
        created_at=D,
    )
    rel.codings = [
        PatientContactRelationshipCoding(
            id=1,
            relationship_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0131",
            code="N",
            display="Next-of-Kin",
            created_by="u-test",
            created_at=D,
        )
    ]
    contact.relationships = [rel]
    contact.telecoms = [
        PatientContactTelecom(
            id=1,
            contact_id=1,
            tenant_id="org-test",
            system=ContactPointSystem.phone,
            value="+1-555-987-6543",
            use=ContactPointUse.home,
            created_by="u-test",
            created_at=D,
        )
    ]
    p.contacts = [contact]
    out = to_fhir_patient(p)
    assert len(out["contact"]) == 1
    assert out["contact"][0]["name"]["family"] == "Carter"
    assert out["contact"][0]["relationship"][0]["coding"][0]["code"] == "N"
    assert out["contact"][0]["telecom"][0]["value"] == "+1-555-987-6543"
    assert_valid(patient_pb2.Patient, out)

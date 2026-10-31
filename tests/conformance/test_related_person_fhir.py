"""FHIR R4 conformance for `to_fhir_related_person()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.related_person import to_fhir_related_person
from app.models.enums import IdentifierUse
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonCommunication,
    RelatedPersonCommunicationLanguageCoding,
    RelatedPersonIdentifier,
    RelatedPersonIdentifierTypeCoding,
    RelatedPersonModel,
    RelatedPersonName,
    RelatedPersonPatientReferenceType,
    RelatedPersonPhoto,
    RelatedPersonRelationship,
    RelatedPersonRelationshipCoding,
    RelatedPersonTelecom,
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

related_person_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.related_person_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "relationships",
    "names",
    "telecoms",
    "addresses",
    "photos",
    "communications",
)


def _related_person(**overrides) -> RelatedPersonModel:
    fields = {
        "id": 1,
        "related_person_id": 300001,
        "tenant_id": "org-test",
        "active": True,
        "patient_reference": "Patient/10001",
        "patient_type": RelatedPersonPatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "Jane Doe",
        "gender": AdministrativeGender.female,
        "birth_date": dt.date(1980, 5, 21),
        "period_start": D,
        "period_end": D + dt.timedelta(days=365),
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = RelatedPersonModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_related_person_minimal_conformance():
    m = _related_person()
    fhir = to_fhir_related_person(m)
    assert_valid(related_person_pb2.RelatedPerson, fhir)


def test_related_person_full_conformance():
    id_coding = RelatedPersonIdentifierTypeCoding(
        related_person_identifier_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="MR",
        display="Medical Record Number",
        created_by="u-test",
    )
    identifier = RelatedPersonIdentifier(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="urn:oid:1.2.3.4",
        value="RP12345",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type="Organization",
        assigner_id=190001,
        assigner_display="Good Health Clinic",
        created_by="u-test",
    )
    identifier.type_codings = [id_coding]

    rel_coding = RelatedPersonRelationshipCoding(
        related_person_relationship_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
        code="MTH",
        display="Mother",
        created_by="u-test",
    )
    relationship = RelatedPersonRelationship(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        text="Mother",
        created_by="u-test",
    )
    relationship.codings = [rel_coding]

    name = RelatedPersonName(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        use=HumanNameUse.official,
        family="Smith",
        given=["Alice"],
        prefix=["Dr."],
        suffix=["MD"],
        text="Dr. Alice Smith",
        created_by="u-test",
    )

    telecom = RelatedPersonTelecom(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        system=ContactPointSystem.phone,
        value="555-0100",
        use=ContactPointUse.home,
        rank=1,
        created_by="u-test",
    )

    address = RelatedPersonAddress(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        use=AddressUse.home,
        type=AddressType.postal,
        line=["534 Erewhon St"],
        city="Pleasantville",
        state="Vic",
        postal_code="3999",
        country="AU",
        created_by="u-test",
    )

    photo = RelatedPersonPhoto(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        content_type="image/jpeg",
        url="http://example.org/photo.jpg",
        title="Photo",
        created_by="u-test",
    )

    lang_coding = RelatedPersonCommunicationLanguageCoding(
        related_person_communication_id=1,
        tenant_id="org-test",
        system="urn:ietf:bcp:47",
        code="en",
        display="English",
        created_by="u-test",
    )
    communication = RelatedPersonCommunication(
        id=1,
        related_person_pk=1,
        tenant_id="org-test",
        language_text="English",
        preferred=True,
        created_by="u-test",
    )
    communication.language_codings = [lang_coding]

    m = _related_person(
        identifiers=[identifier],
        relationships=[relationship],
        names=[name],
        telecoms=[telecom],
        addresses=[address],
        photos=[photo],
        communications=[communication],
    )

    fhir = to_fhir_related_person(m)
    assert_valid(related_person_pb2.RelatedPerson, fhir)

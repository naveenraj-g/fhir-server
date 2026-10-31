"""FHIR R4 conformance for `to_fhir_group()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.group import to_fhir_group
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.group import (
    GroupCharacteristic,
    GroupCharacteristicCodeCoding,
    GroupCharacteristicValueCoding,
    GroupCodeCoding,
    GroupIdentifier,
    GroupIdentifierTypeCoding,
    GroupManagingEntityReferenceType,
    GroupMember,
    GroupMemberEntityReferenceType,
    GroupModel,
    GroupType,
)

from .support import assert_valid

group_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.group_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "code_codings",
    "characteristics",
    "members",
)


def _group(**overrides) -> GroupModel:
    fields = {
        "id": 1,
        "group_id": 430001,
        "tenant_id": "org-test",
        "type": GroupType.person,
        "actual": True,
        "active": True,
        "name": "Test Group",
        "quantity": 1,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = GroupModel(**fields)
    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_group_minimal_conformance():
    m = _group()
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_types_conformance():
    for g_type in GroupType:
        m = _group(type=g_type)
        fhir = to_fhir_group(m)
        assert_valid(group_pb2.Group, fhir)


def test_group_identifiers_conformance():
    ident = GroupIdentifier(
        group_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="National Group Registry",
        system="http://example.org/groups",
        value="GRP-12345",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="National Registry",
        created_by="u-test",
    )
    ident.type_codings = [
        GroupIdentifierTypeCoding(
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="TAX",
            display="Tax ID",
            user_selected=True,
            created_by="u-test",
        )
    ]
    m = _group(identifiers=[ident])
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_code_conformance():
    m = _group(code_text="Support group")
    m.code_codings = [
        GroupCodeCoding(
            group_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="394582007",
            display="Community health",
            user_selected=True,
            created_by="u-test",
        )
    ]
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_managing_entity_conformance():
    m = _group(
        managing_entity_reference="Organization/190001",
        managing_entity_type=GroupManagingEntityReferenceType.Organization,
        managing_entity_id=190001,
        managing_entity_display="Managing Hospital",
    )
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_characteristics_conformance():
    # 1. valueBoolean
    c1 = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Smoker",
        exclude=False,
        value_boolean=True,
        period_start=D,
        period_end=D + dt.timedelta(days=30),
        created_by="u-test",
    )
    c1.code_codings = [
        GroupCharacteristicCodeCoding(
            characteristic_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="77176002",
            display="Smoker",
            created_by="u-test",
        )
    ]
    c1.value_codeable_concept_codings = []

    # 2. valueCodeableConcept
    c2 = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Diagnosis",
        exclude=False,
        value_codeable_concept_text="Diabetes mellitus",
        created_by="u-test",
    )
    c2.code_codings = []
    c2.value_codeable_concept_codings = [
        GroupCharacteristicValueCoding(
            characteristic_id=2,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="73211009",
            display="Diabetes mellitus",
            created_by="u-test",
        )
    ]

    # 3. valueQuantity
    c3 = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Age",
        exclude=False,
        value_quantity={"value": 18, "unit": "years", "system": "http://unitsofmeasure.org", "code": "a"},
        created_by="u-test",
    )
    c3.code_codings = []
    c3.value_codeable_concept_codings = []

    # 4. valueRange
    c4 = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Age Range",
        exclude=True,
        value_range={"low": {"value": 0, "unit": "years"}, "high": {"value": 17, "unit": "years"}},
        created_by="u-test",
    )
    c4.code_codings = []
    c4.value_codeable_concept_codings = []

    # 5. valueReference
    c5 = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Location",
        exclude=False,
        value_reference_reference="Location/230001",
        value_reference_type="Location",
        value_reference_id=230001,
        value_reference_display="Main Clinic",
        created_by="u-test",
    )
    c5.code_codings = []
    c5.value_codeable_concept_codings = []

    m = _group(characteristics=[c1, c2, c3, c4, c5])
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_members_conformance():
    mem1 = GroupMember(
        group_pk=1,
        tenant_id="org-test",
        entity_reference="Patient/10001",
        entity_type=GroupMemberEntityReferenceType.Patient,
        entity_id=10001,
        entity_display="John Doe",
        period_start=D,
        period_end=D + dt.timedelta(days=180),
        inactive=False,
        created_by="u-test",
    )
    mem2 = GroupMember(
        group_pk=1,
        tenant_id="org-test",
        entity_reference="Practitioner/30001",
        entity_type=GroupMemberEntityReferenceType.Practitioner,
        entity_id=30001,
        entity_display="Dr. Smith",
        inactive=True,
        created_by="u-test",
    )
    m = _group(members=[mem1, mem2])
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)


def test_group_full_conformance():
    ident = GroupIdentifier(
        group_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Registry",
        system="http://example.org/groups",
        value="GRP-999",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Registry Org",
        created_by="u-test",
    )
    ident.type_codings = []

    mem = GroupMember(
        group_pk=1,
        tenant_id="org-test",
        entity_reference="Patient/10001",
        entity_type=GroupMemberEntityReferenceType.Patient,
        entity_id=10001,
        entity_display="John Doe",
        inactive=False,
        created_by="u-test",
    )

    char = GroupCharacteristic(
        group_pk=1,
        tenant_id="org-test",
        code_text="Condition",
        exclude=False,
        value_boolean=True,
        created_by="u-test",
    )
    char.code_codings = []
    char.value_codeable_concept_codings = []

    m = _group(
        code_text="Support group",
        managing_entity_reference="Organization/190001",
        managing_entity_type=GroupManagingEntityReferenceType.Organization,
        managing_entity_id=190001,
        managing_entity_display="Managing Org",
        identifiers=[ident],
        characteristics=[char],
        members=[mem],
    )
    m.code_codings = []
    fhir = to_fhir_group(m)
    assert_valid(group_pb2.Group, fhir)

"""FHIR R4 conformance for `to_fhir_flag()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.flag import to_fhir_flag
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.flag import (
    FlagAuthorReferenceType,
    FlagCategory,
    FlagCategoryCoding,
    FlagCodeCoding,
    FlagEncounterReferenceType,
    FlagIdentifier,
    FlagIdentifierTypeCoding,
    FlagModel,
    FlagStatus,
    FlagSubjectReferenceType,
)

from .support import assert_valid

flag_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.flag_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "categories",
    "code_codings",
)


def _flag(**overrides) -> FlagModel:
    fields = {
        "id": 1,
        "flag_id": 450001,
        "tenant_id": "org-test",
        "status": FlagStatus.active,
        "code_text": "Infection control precaution",
        "subject_reference": "Patient/10001",
        "subject_type": FlagSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "period_start": D,
        "period_end": D + dt.timedelta(days=365),
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = FlagModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_flag_minimal_conformance():
    code_coding = FlagCodeCoding(
        flag_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="399166001",
        display="Infection control precaution",
        created_by="u-test",
    )
    m = _flag(code_codings=[code_coding])
    fhir = to_fhir_flag(m)
    assert_valid(flag_pb2.Flag, fhir)


def test_flag_full_conformance():
    id_coding = FlagIdentifierTypeCoding(
        flag_identifier_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="FILL",
        display="Filler Identifier",
        created_by="u-test",
    )
    identifier = FlagIdentifier(
        id=1,
        flag_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="urn:oid:1.2.3.4",
        value="FLAG12345",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Good Health Clinic",
        created_by="u-test",
    )
    identifier.type_codings = [id_coding]

    cat_coding = FlagCategoryCoding(
        flag_category_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/flag-category",
        code="clinical",
        display="Clinical",
        created_by="u-test",
    )
    category = FlagCategory(
        id=1,
        flag_pk=1,
        tenant_id="org-test",
        text="Clinical",
        created_by="u-test",
    )
    category.codings = [cat_coding]

    code_coding = FlagCodeCoding(
        flag_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="399166001",
        display="Infection control precaution",
        created_by="u-test",
    )

    m = _flag(
        encounter_reference="Encounter/20001",
        encounter_type=FlagEncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Inpatient Encounter",
        author_reference="Practitioner/30001",
        author_type=FlagAuthorReferenceType.Practitioner,
        author_id=30001,
        author_display="Dr. Smith",
        identifiers=[identifier],
        categories=[category],
        code_codings=[code_coding],
    )

    fhir = to_fhir_flag(m)
    assert_valid(flag_pb2.Flag, fhir)

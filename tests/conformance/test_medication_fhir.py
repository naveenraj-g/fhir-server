"""FHIR R4 conformance for `to_fhir_medication()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication import to_fhir_medication
from app.models.enums import IdentifierUse
from app.models.medication import (
    MedicationCodeCoding,
    MedicationFormCoding,
    MedicationIdentifier,
    MedicationIdentifierAssignerReferenceType,
    MedicationIdentifierTypeCoding,
    MedicationIngredient,
    MedicationIngredientItemCoding,
    MedicationIngredientItemReferenceType,
    MedicationManufacturerReferenceType,
    MedicationModel,
    MedicationQuantityComparator,
    MedicationStatus,
)

from .support import assert_valid

medication_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "code_codings",
    "form_codings",
    "ingredients",
)


def _medication(**overrides) -> MedicationModel:
    fields = {
        "id": 1,
        "medication_id": 250001,
        "tenant_id": "org-test",
        "status": MedicationStatus.active,
        "code_text": "Amoxicillin 500mg capsule",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MedicationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_medication_minimal_conformance():
    m = _medication()
    m.code_codings = [
        MedicationCodeCoding(
            medication_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin 500mg capsule",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_medication(m)
    assert_valid(medication_pb2.Medication, fhir)


def test_medication_full_conformance():
    ident = MedicationIdentifier(
        medication_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="National Drug Code",
        system="http://hl7.org/fhir/sid/ndc",
        value="0006-0543-31",
        created_by="u-test",
        assigner_reference="Organization/190001",
        assigner_type=MedicationIdentifierAssignerReferenceType.Organization,
        assigner_id=190001,
        assigner_display="FDA",
    )
    ident.type_codings = [
        MedicationIdentifierTypeCoding(
            medication_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="NDC",
            display="National Drug Code",
            created_by="u-test",
        )
    ]

    code_coding = MedicationCodeCoding(
        medication_pk=1,
        tenant_id="org-test",
        system="http://www.nlm.nih.gov/research/umls/rxnorm",
        code="308182",
        display="Amoxicillin 500 MG Oral Capsule",
        created_by="u-test",
    )

    form_coding = MedicationFormCoding(
        medication_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="385055001",
        display="Oral Capsule",
        created_by="u-test",
    )

    ing = MedicationIngredient(
        medication_pk=1,
        tenant_id="org-test",
        item_codeable_concept_text="Amoxicillin",
        item_reference="Medication/250002",
        item_type=MedicationIngredientItemReferenceType.Medication,
        item_id=250002,
        item_display="Amoxicillin Pure",
        is_active=True,
        strength_numerator_value=500.0,
        strength_numerator_unit="mg",
        strength_numerator_system="http://unitsofmeasure.org",
        strength_numerator_code="mg",
        strength_denominator_value=1.0,
        strength_denominator_unit="TAB",
        strength_denominator_system="http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
        strength_denominator_code="TAB",
        created_by="u-test",
    )
    ing.item_codings = [
        MedicationIngredientItemCoding(
            medication_ingredient_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="372687004",
            display="Amoxicillin",
            created_by="u-test",
        )
    ]

    m = _medication(
        status=MedicationStatus.active,
        code_text="Amoxicillin 500mg capsule",
        manufacturer_reference="Organization/190001",
        manufacturer_type=MedicationManufacturerReferenceType.Organization,
        manufacturer_id=190001,
        manufacturer_display="Pharma Corp",
        form_text="Oral Capsule",
        amount_numerator_value=500.0,
        amount_numerator_unit="mg",
        amount_numerator_system="http://unitsofmeasure.org",
        amount_numerator_code="mg",
        amount_denominator_value=1.0,
        amount_denominator_unit="TAB",
        amount_denominator_system="http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
        amount_denominator_code="TAB",
        batch_lot_number="LOT-2026-X",
        batch_expiration_date=D,
        identifiers=[ident],
        code_codings=[code_coding],
        form_codings=[form_coding],
        ingredients=[ing],
    )

    fhir = to_fhir_medication(m)
    assert_valid(medication_pb2.Medication, fhir)

"""FHIR R4 conformance for `to_fhir_specimen_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.specimen_definition import to_fhir_specimen_definition
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.specimen_definition import (
    SpecimenDefinitionAdditiveReferenceType,
    SpecimenDefinitionCollection,
    SpecimenDefinitionCollectionCoding,
    SpecimenDefinitionContainerAdditive,
    SpecimenDefinitionContainerAdditiveCoding,
    SpecimenDefinitionContainerCapCoding,
    SpecimenDefinitionContainerMaterialCoding,
    SpecimenDefinitionContainerTypeCoding,
    SpecimenDefinitionHandlingTempQualCoding,
    SpecimenDefinitionIdentifierTypeCoding,
    SpecimenDefinitionModel,
    SpecimenDefinitionPatientPreparation,
    SpecimenDefinitionPatientPreparationCoding,
    SpecimenDefinitionPreference,
    SpecimenDefinitionQuantityComparator,
    SpecimenDefinitionTypeCollectedCoding,
    SpecimenDefinitionTypeTested,
    SpecimenDefinitionTypeTestedHandling,
    SpecimenDefinitionTypeTestedRejectionCriterion,
    SpecimenDefinitionTypeTestedRejectionCriterionCoding,
    SpecimenDefinitionTypeTestedTypeCoding,
)

from .support import assert_valid

specimen_definition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.specimen_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifier_type_codings",
    "type_collected_codings",
    "patient_preparations",
    "collections",
    "types_tested",
)


def _specimen_definition(**overrides) -> SpecimenDefinitionModel:
    fields = {
        "id": 1,
        "specimen_definition_id": 550001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = SpecimenDefinitionModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_specimen_definition_conforms():
    m = _specimen_definition()
    resource = to_fhir_specimen_definition(m)
    assert_valid(specimen_definition_pb2.SpecimenDefinition, resource)


def test_full_specimen_definition_conforms():
    id_coding = SpecimenDefinitionIdentifierTypeCoding(
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="FILL",
        display="Filler Identifier",
    )
    tc_coding = SpecimenDefinitionTypeCollectedCoding(
        system="http://snomed.info/sct",
        code="122555007",
        display="Venous blood specimen",
    )

    pp = SpecimenDefinitionPatientPreparation(text="12h fasting")
    pp.codings = [
        SpecimenDefinitionPatientPreparationCoding(
            system="http://snomed.info/sct",
            code="726054005",
            display="Fasting",
        )
    ]

    col = SpecimenDefinitionCollection(text="Venipuncture")
    col.codings = [
        SpecimenDefinitionCollectionCoding(
            system="http://snomed.info/sct",
            code="28520004",
            display="Venipuncture",
        )
    ]

    tt = SpecimenDefinitionTypeTested(
        is_derived=True,
        type_text="Serum",
        preference=SpecimenDefinitionPreference.preferred,
        requirement="Fasting required",
        retention_time_value=24,
        retention_time_comparator=SpecimenDefinitionQuantityComparator.le,
        retention_time_unit="h",
        retention_time_system="http://unitsofmeasure.org",
        retention_time_code="h",
        container_description="SST tube",
        container_preparation="Invert gently 5 times",
        container_material_text="Plastic",
        container_type_text="Vacuum tube",
        container_cap_text="Red",
        container_capacity_value=5.0,
        container_capacity_unit="mL",
        container_capacity_system="http://unitsofmeasure.org",
        container_capacity_code="mL",
        container_minimum_volume_quantity_value=1.0,
        container_minimum_volume_quantity_comparator=SpecimenDefinitionQuantityComparator.ge,
        container_minimum_volume_quantity_unit="mL",
        container_minimum_volume_quantity_system="http://unitsofmeasure.org",
        container_minimum_volume_quantity_code="mL",
    )
    tt.type_codings = [
        SpecimenDefinitionTypeTestedTypeCoding(
            system="http://snomed.info/sct",
            code="119364003",
            display="Serum specimen",
        )
    ]
    tt.container_material_codings = [
        SpecimenDefinitionContainerMaterialCoding(
            system="http://snomed.info/sct",
            code="61088005",
            display="Plastic",
        )
    ]
    tt.container_type_codings = [
        SpecimenDefinitionContainerTypeCoding(
            system="http://snomed.info/sct",
            code="706053007",
            display="General specimen container",
        )
    ]
    tt.container_cap_codings = [
        SpecimenDefinitionContainerCapCoding(
            system="http://terminology.hl7.org/CodeSystem/container-cap",
            code="red",
            display="Red Cap",
        )
    ]

    ad = SpecimenDefinitionContainerAdditive(
        additive_codeable_concept_text="Heparin",
        additive_reference_reference="Substance/10001",
        additive_reference_type=SpecimenDefinitionAdditiveReferenceType.Substance,
        additive_reference_id=10001,
        additive_reference_display="Lithium Heparin",
    )
    ad.additive_codings = [
        SpecimenDefinitionContainerAdditiveCoding(
            system="http://snomed.info/sct",
            code="88480006",
            display="Lithium heparin",
        )
    ]
    tt.container_additives = [ad]

    rc = SpecimenDefinitionTypeTestedRejectionCriterion(text="Hemolyzed specimen")
    rc.codings = [
        SpecimenDefinitionTypeTestedRejectionCriterionCoding(
            system="http://terminology.hl7.org/CodeSystem/rejection-criteria",
            code="hemolyzed",
            display="Hemolyzed",
        )
    ]
    tt.rejection_criteria = [rc]

    h = SpecimenDefinitionTypeTestedHandling(
        temperature_qualifier_text="Refrigerated",
        temperature_range_low_value=2.0,
        temperature_range_low_unit="degC",
        temperature_range_low_system="http://unitsofmeasure.org",
        temperature_range_low_code="Cel",
        temperature_range_high_value=8.0,
        temperature_range_high_unit="degC",
        temperature_range_high_system="http://unitsofmeasure.org",
        temperature_range_high_code="Cel",
        max_duration_value=48,
        max_duration_comparator=SpecimenDefinitionQuantityComparator.le,
        max_duration_unit="h",
        max_duration_system="http://unitsofmeasure.org",
        max_duration_code="h",
        instruction="Keep cold until analysis",
    )
    h.temperature_qualifier_codings = [
        SpecimenDefinitionHandlingTempQualCoding(
            system="http://terminology.hl7.org/CodeSystem/handling-condition",
            code="refrigerated",
            display="Refrigerated",
        )
    ]
    tt.handlings = [h]

    m = _specimen_definition(
        identifier_use=IdentifierUse.official,
        identifier_system="http://example.org/specimen-definitions",
        identifier_value="SERUM-001",
        identifier_period_start=D,
        identifier_period_end=D,
        identifier_assigner_reference="Organization/190001",
        identifier_assigner_type=OrganizationReferenceType.Organization,
        identifier_assigner_id=190001,
        identifier_assigner_display="Acme Pathology",
        identifier_type_text="Catalog ID",
        identifier_type_codings=[id_coding],
        type_collected_text="Venous blood",
        type_collected_codings=[tc_coding],
        patient_preparations=[pp],
        time_aspect="morning, fasting",
        collections=[col],
        types_tested=[tt],
    )

    resource = to_fhir_specimen_definition(m)
    assert_valid(specimen_definition_pb2.SpecimenDefinition, resource)


def test_specimen_definition_minimum_volume_string_conforms():
    tt = SpecimenDefinitionTypeTested(
        preference=SpecimenDefinitionPreference.alternate,
        container_minimum_volume_string="At least 2-3 drops",
    )
    m = _specimen_definition(types_tested=[tt])
    resource = to_fhir_specimen_definition(m)
    assert_valid(specimen_definition_pb2.SpecimenDefinition, resource)

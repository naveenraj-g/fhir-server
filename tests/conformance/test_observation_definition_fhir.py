"""FHIR R4 conformance for `to_fhir_observation_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.observation_definition import (
    to_fhir_observation_definition,
)
from app.models.enums import IdentifierUse
from app.models.observation_definition import (
    ObservationDefinitionAssignerReferenceType,
    ObservationDefinitionCategory,
    ObservationDefinitionCategoryCoding,
    ObservationDefinitionCodeCoding,
    ObservationDefinitionGender,
    ObservationDefinitionIdentifier,
    ObservationDefinitionIdentifierTypeCoding,
    ObservationDefinitionMethodCoding,
    ObservationDefinitionModel,
    ObservationDefinitionPermittedDataType,
    ObservationDefinitionQualifiedInterval,
    ObservationDefinitionQualifiedIntervalAppliesTo,
    ObservationDefinitionQualifiedIntervalAppliesToCoding,
    ObservationDefinitionQualifiedIntervalCategory,
    ObservationDefinitionQualifiedIntervalContextCoding,
    ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding,
    ObservationDefinitionQuantitativeDetailsUnitCoding,
    ObservationDefinitionValueSetReferenceType,
)

from .support import assert_valid

observation_definition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.observation_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "categories",
    "code_codings",
    "method_codings",
    "quantitative_details_customary_unit_codings",
    "quantitative_details_unit_codings",
    "qualified_intervals",
)


def _observation_definition(**overrides) -> ObservationDefinitionModel:
    fields = {
        "id": 1,
        "observation_definition_id": 400001,
        "tenant_id": "org-test",
        "code_text": "Glucose in Blood",
        "multiple_results_allowed": False,
        "preferred_report_name": "Blood Glucose",
        "permitted_data_type": [ObservationDefinitionPermittedDataType.Quantity],
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    od = ObservationDefinitionModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(od, attr, None) is None:
            setattr(od, attr, [])
    # Add a default code coding if none provided
    if not od.code_codings:
        od.code_codings = [
            ObservationDefinitionCodeCoding(
                id=1,
                observation_definition_pk=1,
                tenant_id="org-test",
                system="http://loinc.org",
                code="15074-8",
                display="Glucose [Moles/volume] in Blood",
                created_by="u-test",
            )
        ]
    return od


def test_minimal_observation_definition_conforms():
    od = _observation_definition()
    out = to_fhir_observation_definition(od)
    assert out["resourceType"] == "ObservationDefinition"
    assert out["id"] == "400001"
    assert out["code"]["text"] == "Glucose in Blood"
    assert out["code"]["coding"][0]["code"] == "15074-8"
    assert out["preferredReportName"] == "Blood Glucose"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_identifiers_conforms():
    ident = ObservationDefinitionIdentifier(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Definition ID",
        system="http://example.org/obs-def",
        value="OD-999",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=ObservationDefinitionAssignerReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        ObservationDefinitionIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    od = _observation_definition(identifiers=[ident])
    out = to_fhir_observation_definition(od)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "OD-999"
    assert out["identifier"][0]["use"] == "official"
    assert out["identifier"][0]["assigner"]["reference"] == "Organization/190001"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_category_conforms():
    cat = ObservationDefinitionCategory(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        text="Laboratory",
        created_by="u-test",
    )
    cat.codings = [
        ObservationDefinitionCategoryCoding(
            id=1,
            category_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/observation-category",
            code="laboratory",
            display="Laboratory",
            created_by="u-test",
        )
    ]
    od = _observation_definition(categories=[cat])
    out = to_fhir_observation_definition(od)
    assert len(out["category"]) == 1
    assert out["category"][0]["text"] == "Laboratory"
    assert out["category"][0]["coding"][0]["code"] == "laboratory"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_method_conforms():
    m = ObservationDefinitionMethodCoding(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="258026004",
        display="Enzyme analysis",
        created_by="u-test",
    )
    od = _observation_definition(method_text="Enzyme analysis", method_codings=[m])
    out = to_fhir_observation_definition(od)
    assert out["method"]["text"] == "Enzyme analysis"
    assert out["method"]["coding"][0]["code"] == "258026004"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_quantitative_details_conforms():
    cu_coding = ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        system="http://unitsofmeasure.org",
        code="mg/dL",
        display="mg/dL",
        created_by="u-test",
    )
    u_coding = ObservationDefinitionQuantitativeDetailsUnitCoding(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        system="http://unitsofmeasure.org",
        code="mmol/L",
        display="mmol/L",
        created_by="u-test",
    )
    od = _observation_definition(
        quantitative_details_customary_unit_text="mg/dL",
        quantitative_details_customary_unit_codings=[cu_coding],
        quantitative_details_unit_text="mmol/L",
        quantitative_details_unit_codings=[u_coding],
        quantitative_details_conversion_factor=0.0555,
        quantitative_details_decimal_precision=1,
    )
    out = to_fhir_observation_definition(od)
    assert "quantitativeDetails" in out
    qd = out["quantitativeDetails"]
    assert qd["conversionFactor"] == 0.0555
    assert qd["decimalPrecision"] == 1
    assert qd["unit"]["coding"][0]["code"] == "mmol/L"
    assert qd["customaryUnit"]["coding"][0]["code"] == "mg/dL"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_qualified_intervals_conforms():
    qi = ObservationDefinitionQualifiedInterval(
        id=1,
        observation_definition_pk=1,
        tenant_id="org-test",
        category=ObservationDefinitionQualifiedIntervalCategory.reference,
        range_low_value=3.9,
        range_low_unit="mmol/L",
        range_low_system="http://unitsofmeasure.org",
        range_low_code="mmol/L",
        range_high_value=5.6,
        range_high_unit="mmol/L",
        range_high_system="http://unitsofmeasure.org",
        range_high_code="mmol/L",
        context_text="Fasting",
        gender=ObservationDefinitionGender.male,
        age_low_value=18,
        age_low_unit="a",
        age_low_system="http://unitsofmeasure.org",
        age_low_code="a",
        age_high_value=65,
        age_high_unit="a",
        age_high_system="http://unitsofmeasure.org",
        age_high_code="a",
        condition="Fasting for at least 8 hours",
        created_by="u-test",
    )
    ctx_coding = ObservationDefinitionQualifiedIntervalContextCoding(
        id=1,
        qualified_interval_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/referencerange-meaning",
        code="normal",
        display="Normal Range",
        created_by="u-test",
    )
    qi.context_codings = [ctx_coding]

    applies = ObservationDefinitionQualifiedIntervalAppliesTo(
        id=1,
        qualified_interval_id=1,
        tenant_id="org-test",
        text="Adults",
        created_by="u-test",
    )
    applies.codings = [
        ObservationDefinitionQualifiedIntervalAppliesToCoding(
            id=1,
            applies_to_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="133936004",
            display="Adult",
            created_by="u-test",
        )
    ]
    qi.applies_tos = [applies]

    od = _observation_definition(qualified_intervals=[qi])
    out = to_fhir_observation_definition(od)
    assert len(out["qualifiedInterval"]) == 1
    q_out = out["qualifiedInterval"][0]
    assert q_out["category"] == "reference"
    assert q_out["gender"] == "male"
    assert q_out["range"]["low"]["value"] == 3.9
    assert q_out["range"]["high"]["value"] == 5.6
    assert q_out["age"]["low"]["value"] == 18
    assert q_out["age"]["high"]["value"] == 65
    assert q_out["condition"] == "Fasting for at least 8 hours"
    assert len(q_out["appliesTo"]) == 1
    assert q_out["appliesTo"][0]["coding"][0]["code"] == "133936004"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_value_sets_conforms():
    od = _observation_definition(
        valid_coded_value_set_reference="ValueSet/1",
        valid_coded_value_set_type=ObservationDefinitionValueSetReferenceType.ValueSet,
        valid_coded_value_set_id=1,
        valid_coded_value_set_display="Valid Results",
        normal_coded_value_set_reference="ValueSet/2",
        normal_coded_value_set_type=ObservationDefinitionValueSetReferenceType.ValueSet,
        normal_coded_value_set_id=2,
        normal_coded_value_set_display="Normal Results",
        abnormal_coded_value_set_reference="ValueSet/3",
        abnormal_coded_value_set_type=ObservationDefinitionValueSetReferenceType.ValueSet,
        abnormal_coded_value_set_id=3,
        abnormal_coded_value_set_display="Abnormal Results",
        critical_coded_value_set_reference="ValueSet/4",
        critical_coded_value_set_type=ObservationDefinitionValueSetReferenceType.ValueSet,
        critical_coded_value_set_id=4,
        critical_coded_value_set_display="Critical Results",
    )
    out = to_fhir_observation_definition(od)
    assert out["validCodedValueSet"]["reference"] == "ValueSet/1"
    assert out["normalCodedValueSet"]["reference"] == "ValueSet/2"
    assert out["abnormalCodedValueSet"]["reference"] == "ValueSet/3"
    assert out["criticalCodedValueSet"]["reference"] == "ValueSet/4"
    assert_valid(observation_definition_pb2.ObservationDefinition, out)


def test_observation_definition_extension_conforms():
    ext = [
        {
            "url": "http://example.org/fhir/StructureDefinition/obs-def-lab",
            "valueString": "Clinical Chemistry",
        }
    ]
    od = _observation_definition(extension=ext)
    out = to_fhir_observation_definition(od)
    assert out["extension"] == ext
    assert_valid(observation_definition_pb2.ObservationDefinition, out)

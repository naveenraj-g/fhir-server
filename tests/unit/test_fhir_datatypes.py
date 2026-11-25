"""The generated FHIR datatype models (app/schemas/fhir_datatypes/).

They are generated from HL7's own R4 schema (scripts/generate_fhir_datatypes.py) and shared by
every resource's request/response schema, so what matters here is that every model builds the JSON
schema MCP reads, real-shaped documents validate, and invalid ones are rejected."""

import pytest
from pydantic import BaseModel, ValidationError

import app.schemas.fhir_datatypes as dt

MODELS = [
    getattr(dt, name)
    for name in dt.__all__
    if isinstance(getattr(dt, name), type) and issubclass(getattr(dt, name), BaseModel)
]


def _properties(schema: dict) -> dict:
    """The property map of a model's JSON schema (a recursive model comes back as a $ref)."""
    if "properties" in schema:
        return schema["properties"]
    return schema["$defs"][schema["$ref"].rsplit("/", 1)[-1]]["properties"]


def test_every_r4_datatype_is_present():
    expected = {
        # primitive
        *[
            "Base64Binary",
            "Boolean",
            "Canonical",
            "Code",
            "Date",
            "DateTime",
            "Decimal",
            "Id",
            "Instant",
            "Integer",
            "Markdown",
            "Oid",
            "PositiveInt",
            "String",
            "Time",
            "UnsignedInt",
            "Uri",
            "Url",
            "Uuid",
            "Xhtml",
        ],
        # general-purpose
        *[
            "Address",
            "Age",
            "Annotation",
            "Attachment",
            "CodeableConcept",
            "Coding",
            "ContactPoint",
            "Count",
            "Distance",
            "Duration",
            "HumanName",
            "Identifier",
            "Money",
            "MoneyQuantity",
            "Period",
            "Quantity",
            "Range",
            "Ratio",
            "Reference",
            "SampledData",
            "Signature",
            "SimpleQuantity",
            "Timing",
        ],
        # metadata
        *[
            "ContactDetail",
            "Contributor",
            "DataRequirement",
            "Expression",
            "ParameterDefinition",
            "RelatedArtifact",
            "TriggerDefinition",
            "UsageContext",
        ],
        # special purpose
        *[
            "Dosage",
            "ElementDefinition",
            "Extension",
            "MarketingStatus",
            "Meta",
            "Narrative",
            "Population",
            "ProdCharacteristic",
            "ProductShelfLife",
            "SubstanceAmount",
        ],
        "Element",
        "BackboneElement",
    }
    assert expected <= set(dt.__all__)


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
def test_every_model_builds_a_json_schema_with_descriptions(model):
    props = _properties(model.model_json_schema())
    assert props
    described = [p for p in props.values() if p.get("description")]
    assert described, f"{model.__name__} has no property descriptions"


def test_valid_documents():
    dt.Identifier(
        system="urn:x",
        value="1",
        type={"coding": [{"system": "http://s", "code": "c"}], "text": "t"},
        assigner={"reference": "Organization/1"},
    )
    dt.Dosage(
        sequence=1,
        timing={
            "repeat": {
                "frequency": 2,
                "period": 1,
                "periodUnit": "d",
                "boundsPeriod": {"start": "2026-01-01"},
            }
        },
        doseAndRate=[{"doseQuantity": {"value": 5, "unit": "mg"}}],
    )
    dt.ElementDefinition(
        path="Patient.name",
        min=0,
        max="*",
        type=[{"code": "HumanName"}],
        binding={"strength": "required", "valueSet": "http://vs"},
    )
    dt.Address(use="home", line=["1 Main"], city="X", period={"start": "2020"})
    dt.Meta(versionId="1", lastUpdated="2026-01-01T00:00:00Z", tag=[{"code": "x"}])
    dt.Signature(
        type=[{"code": "1.2.840.10065.1.12.1.1"}],
        when="2026-01-01T00:00:00Z",
        who={"reference": "Practitioner/1"},
    )
    dt.UsageContext(code={"code": "age"}, valueRange={"low": {"value": 1}})
    dt.Age(value=3, unit="a")
    dt.SimpleQuantity(value=1)
    dt.Money(value=1.2, currency="USD")


def test_extension_keeps_primitives_typed_and_complex_values_as_objects():
    ext = dt.Extension(
        url="http://x", valueInteger=3, valueString="s", valueQuantity={"value": 1}
    )
    assert ext.valueInteger == 3 and isinstance(ext.valueInteger, int)
    assert ext.valueQuantity == {"value": 1}


@pytest.mark.parametrize(
    "build",
    [
        lambda: dt.Quantity(comparator="~"),
        lambda: dt.Address(use="nope"),
        lambda: dt.Extension(),  # url is 1..1
        lambda: dt.Annotation(),  # text is 1..1
        lambda: dt.Period(start="yesterday"),
        lambda: dt.Timing(repeat={"count": 0}),  # positiveInt
        lambda: dt.Identifier(value=5),
        lambda: dt.Coding(code=["a"]),
    ],
    ids=[
        "comparator",
        "address-use",
        "extension-url",
        "annotation-text",
        "period-date",
        "positive-int",
        "identifier-value",
        "coding-code",
    ],
)
def test_invalid_documents_are_rejected(build):
    with pytest.raises(ValidationError):
        build()


def test_unknown_elements_are_ignored_not_lost_to_an_error():
    """The raw body is what gets stored; the model must not reject an element it does not declare."""
    assert dt.Coding(code="x", futureElement=1).code == "x"


def test_schema_size_stays_small_enough_for_mcp():
    """Extension.value[x] once pulled every datatype into every schema (123 KB for a Coding)."""
    import json

    assert len(json.dumps(dt.Coding.model_json_schema())) < 40_000

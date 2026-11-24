from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# permittedDataType (the required binding of ObservationDefinition.permittedDataType).
PermittedDataTypeCode = Literal[
    "Quantity",
    "CodeableConcept",
    "string",
    "boolean",
    "integer",
    "Range",
    "Ratio",
    "SampledData",
    "time",
    "dateTime",
    "Period",
]

_EXAMPLE = {
    "resourceType": "ObservationDefinition",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/observation-definition-id",
            "value": "OD-1",
        }
    ],
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                }
            ]
        }
    ],
    "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
    "permittedDataType": ["Quantity"],
    "multipleResultsAllowed": False,
    "preferredReportName": "Hemoglobin",
    "quantitativeDetails": {
        "unit": {"coding": [{"system": "http://unitsofmeasure.org", "code": "g/dL"}]},
        "decimalPrecision": 1,
    },
    "qualifiedInterval": [
        {
            "category": "reference",
            "range": {
                "low": {"value": 12, "unit": "g/dL"},
                "high": {"value": 16, "unit": "g/dL"},
            },
            "gender": "female",
        }
    ],
}


class _ObservationDefinitionFields(FhirInputModel):
    """Every writable ObservationDefinition element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/observationdefinition.html). Create and patch accept exactly
    the same fields. R4 requires `code`; the native validator checks it, and the finer R4
    rules are only enforced by the `java_validator` backend.

    The validated body is stored whole (ObservationDefinitionModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the observation_definition_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from
    the verified JWT (actor.org_id / actor.sub), never the body. There is no user_id.

    R4 defines no search parameter for this resource, so nothing here is indexed."""

    resourceType: Literal["ObservationDefinition"] | None = Field(
        None, description="Optional; if supplied it must be 'ObservationDefinition'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business identifier for this ObservationDefinition instance."
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Category of observation."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Type of observation (code / type) - required by R4."
    )
    permittedDataType: list[PermittedDataTypeCode] | None = Field(
        None,
        description="Quantity | CodeableConcept | string | boolean | integer | Range | Ratio | SampledData | time | dateTime | Period.",
    )
    multipleResultsAllowed: bool | None = Field(
        None, description="Multiple results allowed."
    )
    method: FhirCodeableConceptInput | None = Field(
        None, description="Method used to produce the observation."
    )
    preferredReportName: str | None = Field(None, description="Preferred report name.")
    quantitativeDetails: dict | None = Field(
        None,
        description="Characteristics of quantitative results: {customaryUnit, unit, conversionFactor, decimalPrecision}.",
    )
    qualifiedInterval: list[dict] | None = Field(
        None,
        description="Qualified range for continuous and ordinal observation results: [{category, range, context, appliesTo, gender, age, gestationalAge, condition}].",
    )
    validCodedValueSet: FhirReferenceInput | None = Field(
        None,
        description="Value set of valid coded values for the observations conforming to this ObservationDefinition - Reference(ValueSet).",
    )
    normalCodedValueSet: FhirReferenceInput | None = Field(
        None, description="Value set of normal coded values - Reference(ValueSet)."
    )
    abnormalCodedValueSet: FhirReferenceInput | None = Field(
        None, description="Value set of abnormal coded values - Reference(ValueSet)."
    )
    criticalCodedValueSet: FhirReferenceInput | None = Field(
        None, description="Value set of critical coded values - Reference(ValueSet)."
    )


class ObservationDefinitionCreateSchema(_ObservationDefinitionFields):
    """POST body - a FHIR R4 ObservationDefinition resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ObservationDefinitionPatchSchema(_ObservationDefinitionFields):
    """PATCH body - a partial FHIR R4 ObservationDefinition (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "preferredReportName": "Haemoglobin",
                "multipleResultsAllowed": True,
            }
        }
    }

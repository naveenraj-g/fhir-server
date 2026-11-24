from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
)

_EXAMPLE = {
    "resourceType": "SpecimenDefinition",
    "identifier": {
        "system": "https://fhir-server.dev/fhir/identifier-system/specimen-definition-id",
        "value": "SD-1",
    },
    "typeCollected": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
                "code": "BLD",
                "display": "Whole blood",
            }
        ]
    },
    "patientPreparation": [{"text": "Fasting for 8 hours"}],
    "timeAspect": "Morning",
    "collection": [{"text": "Venipuncture"}],
    "typeTested": [
        {
            "isDerived": False,
            "type": {"text": "Whole blood"},
            "preference": "preferred",
            "container": {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
                            "code": "SPECIMEN",
                        }
                    ]
                },
                "capacity": {"value": 5, "unit": "mL"},
            },
            "retentionTime": {"value": 7, "unit": "d"},
        }
    ],
}


class _SpecimenDefinitionFields(FhirInputModel):
    """Every writable SpecimenDefinition element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/specimendefinition.html). Create and patch accept exactly the
    same fields. R4 has no required top-level element (each `typeTested` needs its
    `preference`, which only the `java_validator` backend enforces).

    The validated body is stored whole (SpecimenDefinitionModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the specimen_definition_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["SpecimenDefinition"] | None = Field(
        None, description="Optional; if supplied it must be 'SpecimenDefinition'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: FhirIdentifierInput | None = Field(
        None,
        description="Business identifier of a kind of specimen (a single Identifier). Searched by `identifier`.",
    )
    typeCollected: FhirCodeableConceptInput | None = Field(
        None, description="Kind of material to collect. Searched by `type`."
    )
    patientPreparation: list[FhirCodeableConceptInput] | None = Field(
        None, description="Patient preparation for collection."
    )
    timeAspect: str | None = Field(None, description="Time aspect for collection.")
    collection: list[FhirCodeableConceptInput] | None = Field(
        None, description="Specimen collection procedure."
    )
    typeTested: list[dict] | None = Field(
        None,
        description="Specimen in container intended for testing by lab: [{isDerived, type, preference, container, requirement, retentionTime, rejectionCriterion, handling}]. The `container.type` of every entry is searched by `container`.",
    )


class SpecimenDefinitionCreateSchema(_SpecimenDefinitionFields):
    """POST body - a FHIR R4 SpecimenDefinition resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class SpecimenDefinitionPatchSchema(_SpecimenDefinitionFields):
    """PATCH body - a partial FHIR R4 SpecimenDefinition (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {"example": {"timeAspect": "Afternoon"}},
    }

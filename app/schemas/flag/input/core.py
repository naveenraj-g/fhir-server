from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# FlagStatus (the required binding of Flag.status).
StatusCode = Literal["active", "inactive", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "Flag",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/flag-id",
            "value": "F-1",
        }
    ],
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                    "code": "safety",
                    "display": "Safety",
                }
            ]
        }
    ],
    "code": {"text": "Patient has a latex allergy"},
    "subject": {"reference": "Patient/10001"},
    "period": {"start": "2026-01-15"},
    "encounter": {"reference": "Encounter/20001"},
    "author": {"reference": "Practitioner/30001"},
}


class _FlagFields(FhirInputModel):
    """Every writable Flag element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/flag.html). Create and patch accept exactly the same fields. R4
    requires `status`, `code` and `subject`; the native validator checks `code` and `subject`
    (a missing primitive `status` is only rejected by the `java_validator` backend).

    The validated body is stored whole (FlagModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the flag_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Flag"] | None = Field(
        None, description="Optional; if supplied it must be 'Flag'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business identifier. Searched by `identifier`."
    )
    status: StatusCode | None = Field(
        None, description="active | inactive | entered-in-error (required by R4)."
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Clinical, administrative, etc. (R4 defines no search parameter for it).",
    )
    code: FhirCodeableConceptInput | None = Field(
        None,
        description="Coded or textual message to display to user (required by R4; no search parameter).",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who/What is flag about - Reference(Patient | Location | Group | Organization | Practitioner | PlanDefinition | Medication | Procedure) (required by R4). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period when flag is active. Searched by `date`."
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Alert relevant during encounter - Reference(Encounter). Searched by `encounter`.",
    )
    author: FhirReferenceInput | None = Field(
        None,
        description="Flag creator - Reference(Device | Organization | Patient | Practitioner | PractitionerRole). Searched by `author`.",
    )


class FlagCreateSchema(_FlagFields):
    """POST body - a FHIR R4 Flag resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class FlagPatchSchema(_FlagFields):
    """PATCH body - a partial FHIR R4 Flag (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces
    the stored value wholesale - a list (even `[]`) replaces every existing entry, an object
    replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "inactive",
                "period": {"start": "2026-01-15", "end": "2026-06-30"},
            }
        }
    }

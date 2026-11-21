from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

StatusCode = Literal["completed", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "ImmunizationEvaluation",
    "identifier": [
        {"system": "https://fhir-server.dev/fhir/identifier-system/immunization-evaluation-id", "value": "IE-1001"}
    ],
    "status": "completed",
    "patient": {"reference": "Patient/10001"},
    "date": "2023-01-15T09:30:00Z",
    "authority": {"reference": "Organization/190001"},
    "targetDisease": {"coding": [{"system": "http://snomed.info/sct", "code": "6142004", "display": "Influenza"}]},
    "immunizationEvent": {"reference": "Immunization/330001"},
    "doseStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
                "code": "valid",
                "display": "Valid",
            }
        ]
    },
    "doseStatusReason": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason", "code": "agedoses"}]}
    ],
    "description": "Evaluated against the seasonal flu schedule",
    "series": "Seasonal",
    "doseNumberPositiveInt": 1,
    "seriesDosesPositiveInt": 1,
}


class _ImmunizationEvaluationFields(FhirInputModel):
    """Every writable ImmunizationEvaluation element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/immunizationevaluation.html). Create and patch accept
    exactly the same fields. R4 requires `status`, `patient`, `targetDisease`,
    `immunizationEvent` and `doseStatus`; that is enforced by base R4 validation of the
    stored document (the `java_validator` backend — the native structural check has no
    cardinality minimums), not by this model. A PATCH may omit them: it is merged onto the
    current resource before validating.

    The validated body is stored whole (ImmunizationEvaluationModel.content), so any valid
    R4 element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the immunization_evaluation_id
    sequence) and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["ImmunizationEvaluation"] | None = Field(
        None, description="Optional; if supplied it must be 'ImmunizationEvaluation'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="Business identifier.")
    status: StatusCode | None = Field(None, description="completed | entered-in-error (required by R4).")
    patient: FhirReferenceInput | None = Field(
        None,
        description="Who this evaluation is for — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    date: str | None = Field(None, description="Date the evaluation was performed (a FHIR dateTime).")
    authority: FhirReferenceInput | None = Field(
        None,
        description="Who is responsible for publishing the recommendations — Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    targetDisease: FhirCodeableConceptInput | None = Field(None, description="Evaluation target disease (required by R4).")
    immunizationEvent: FhirReferenceInput | None = Field(
        None,
        description="Immunization being evaluated — Reference(Immunization) (required by R4). A relative 'Immunization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    doseStatus: FhirCodeableConceptInput | None = Field(None, description="Status of the dose relative to published recommendations (required by R4).")
    doseStatusReason: list[FhirCodeableConceptInput] | None = Field(None, description="Reason for the dose status.")
    description: str | None = Field(None, description="Evaluation notes.")
    series: str | None = Field(None, description="Name of the vaccine series.")
    doseNumberPositiveInt: int | None = Field(None, description="Dose number within the series (a positiveInt). One of the doseNumber[x] choices.")
    doseNumberString: str | None = Field(None, description="Dose number within the series (a string). One of the doseNumber[x] choices.")
    seriesDosesPositiveInt: int | None = Field(None, description="Recommended number of doses for immunity (a positiveInt). One of the seriesDoses[x] choices.")
    seriesDosesString: str | None = Field(None, description="Recommended number of doses for immunity (a string). One of the seriesDoses[x] choices.")


class ImmunizationEvaluationCreateSchema(_ImmunizationEvaluationFields):
    """POST body — a FHIR R4 ImmunizationEvaluation resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ImmunizationEvaluationPatchSchema(_ImmunizationEvaluationFields):
    """PATCH body — a partial FHIR R4 ImmunizationEvaluation (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `doseStatus` replaces
    the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "entered-in-error",
                "description": "Evaluated against the wrong schedule.",
            }
        }
    }

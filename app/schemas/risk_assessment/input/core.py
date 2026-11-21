from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# ObservationStatus (the required binding of RiskAssessment.status).
StatusCode = Literal[
    "registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"
]

_EXAMPLE = {
    "resourceType": "RiskAssessment",
    "identifier": [
        {"system": "https://fhir-server.dev/fhir/identifier-system/risk-assessment-id", "value": "RA-1001"}
    ],
    "status": "final",
    "method": {"coding": [{"system": "http://snomed.info/sct", "code": "225338004", "display": "Risk assessment"}]},
    "code": {"coding": [{"system": "http://snomed.info/sct", "code": "709510001", "display": "Assessment of risk for cardiovascular disease"}]},
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "occurrenceDateTime": "2023-01-15T09:30:00Z",
    "condition": {"reference": "Condition/120001"},
    "performer": {"reference": "Practitioner/30001"},
    "reasonCode": [{"text": "Family history of heart disease"}],
    "prediction": [
        {
            "outcome": {"coding": [{"system": "http://snomed.info/sct", "code": "54329005", "display": "Acute myocardial infarction"}]},
            "probabilityDecimal": 12.5,
            "qualitativeRisk": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/risk-probability", "code": "moderate", "display": "moderate likelihood"}]
            },
            "relativeRisk": 1.4,
            "whenRange": {"low": {"value": 40, "unit": "yr", "system": "http://unitsofmeasure.org", "code": "a"}, "high": {"value": 50, "unit": "yr", "system": "http://unitsofmeasure.org", "code": "a"}},
            "rationale": "Based on lipid panel and blood pressure.",
        }
    ],
    "mitigation": "Statin therapy and lifestyle changes.",
    "note": [{"text": "Reassess in 12 months."}],
}


class RiskAssessmentQuantityInput(FhirInputModel):
    """Quantity — a bound of a Range (for a probability, a percentage: unit `%`)."""

    value: float | int | None = Field(None, description="Numerical value (with implicit precision).")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form (usually http://unitsofmeasure.org).")
    code: str | None = Field(None, description="Coded form of the unit.")


class RiskAssessmentRangeInput(FhirInputModel):
    """Range — a low and a high Quantity."""

    low: RiskAssessmentQuantityInput | None = Field(None, description="Low limit.")
    high: RiskAssessmentQuantityInput | None = Field(None, description="High limit.")


class RiskAssessmentAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made (a FHIR dateTime).")
    text: str | None = Field(None, description="The annotation text, as markdown (required by R4).")


class RiskAssessmentPredictionInput(FhirInputModel):
    """RiskAssessment.prediction — an outcome and the likelihood of it."""

    outcome: FhirCodeableConceptInput | None = Field(None, description="Possible outcome for the subject.")
    probabilityDecimal: float | int | None = Field(None, description="Likelihood of specified outcome (a decimal, a percentage <= 100 — rule ras-2). One of the probability[x] choices.")
    probabilityRange: RiskAssessmentRangeInput | None = Field(None, description="Likelihood of specified outcome (a Range whose bounds are percentages — rule ras-1). One of the probability[x] choices.")
    qualitativeRisk: FhirCodeableConceptInput | None = Field(None, description="Likelihood of specified outcome as a qualitative value.")
    relativeRisk: float | int | None = Field(None, description="Relative likelihood.")
    whenPeriod: FhirPeriodInput | None = Field(None, description="Timeframe or age range (a Period). One of the when[x] choices.")
    whenRange: RiskAssessmentRangeInput | None = Field(None, description="Timeframe or age range (a Range). One of the when[x] choices.")
    rationale: str | None = Field(None, description="Explanation of prediction.")


class _RiskAssessmentFields(FhirInputModel):
    """Every writable RiskAssessment element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/riskassessment.html). Create and patch accept exactly the same
    fields. R4 requires `status` and `subject`, and rules ras-1 / ras-2 constrain a probability
    to a percentage <= 100; that is enforced by base R4 validation of the stored document (the
    `java_validator` backend — the native structural check has no cardinality minimums or
    invariants), not by this model. A PATCH may omit them: it is merged onto the current
    resource before validating.

    The validated body is stored whole (RiskAssessmentModel.content), so any valid R4 element
    is kept — including ones this model does not declare. Server-managed elements are ignored
    if sent: `id` (assigned from the risk_assessment_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["RiskAssessment"] | None = Field(None, description="Optional; if supplied it must be 'RiskAssessment'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="Unique identifier for the assessment.")
    basedOn: FhirReferenceInput | None = Field(None, description="Request fulfilled by this assessment — Reference(Any).")
    parent: FhirReferenceInput | None = Field(None, description="Part of this occurrence — Reference(Any).")
    status: StatusCode | None = Field(None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown (required by R4).")
    method: FhirCodeableConceptInput | None = Field(None, description="Evaluation mechanism.")
    code: FhirCodeableConceptInput | None = Field(None, description="Type of assessment.")
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who/what does assessment apply to — Reference(Patient | Group) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Where was assessment performed? — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    occurrenceDateTime: str | None = Field(None, description="When was assessment made? (a FHIR dateTime). One of the occurrence[x] choices; the only one `date` searches.")
    occurrencePeriod: FhirPeriodInput | None = Field(None, description="When was assessment made? (a Period). One of the occurrence[x] choices.")
    condition: FhirReferenceInput | None = Field(None, description="Condition assessed — Reference(Condition). A relative reference must exist in the caller's org (422 otherwise).")
    performer: FhirReferenceInput | None = Field(
        None,
        description="Who did assessment? — Reference(Practitioner | PractitionerRole | Device). A relative Practitioner or PractitionerRole must exist in the caller's org (422 otherwise).",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(None, description="Why the assessment was necessary?")
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why the assessment was necessary? — Reference(Condition | Observation | DiagnosticReport | DocumentReference). A relative Condition or DiagnosticReport must exist in the caller's org (422 otherwise).",
    )
    basis: list[FhirReferenceInput] | None = Field(None, description="Information used in assessment — Reference(Any).")
    prediction: list[RiskAssessmentPredictionInput] | None = Field(None, description="Outcome predicted.")
    mitigation: str | None = Field(None, description="How to reduce risk.")
    note: list[RiskAssessmentAnnotationInput] | None = Field(None, description="Comments on the risk assessment.")


class RiskAssessmentCreateSchema(_RiskAssessmentFields):
    """POST body — a FHIR R4 RiskAssessment resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class RiskAssessmentPatchSchema(_RiskAssessmentFields):
    """PATCH body — a partial FHIR R4 RiskAssessment (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale — a list (even `[]`) replaces every existing
    entry, an object such as `subject` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "amended",
                "mitigation": "Statin therapy, lifestyle changes and a blood-pressure check.",
            }
        }
    }

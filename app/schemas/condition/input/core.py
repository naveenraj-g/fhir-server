from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

_EXAMPLE = {
    "resourceType": "Condition",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/condition-id", "value": "C-1001"}],
    "clinicalStatus": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
    },
    "verificationStatus": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
    },
    "category": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}]}
    ],
    "severity": {"coding": [{"system": "http://snomed.info/sct", "code": "24484000", "display": "Severe"}]},
    "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003", "display": "Hypertension"}]},
    "bodySite": [{"coding": [{"system": "http://snomed.info/sct", "code": "368208006", "display": "Left upper arm"}]}],
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "onsetDateTime": "2023-01-15T09:30:00Z",
    "recordedDate": "2023-01-15T10:00:00Z",
    "recorder": {"reference": "Practitioner/30001"},
    "asserter": {"reference": "Patient/10001"},
    "stage": [{"summary": {"coding": [{"system": "http://snomed.info/sct", "code": "14803004", "display": "Temporary"}]}}],
    "evidence": [
        {
            "code": [{"coding": [{"system": "http://snomed.info/sct", "code": "29857009", "display": "Chest pain"}]}],
            "detail": [{"reference": "Observation/160001"}],
        }
    ],
    "note": [{"text": "Blood pressure poorly controlled.", "time": "2023-01-15T10:05:00Z"}],
}


class ConditionAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made (a FHIR dateTime).")
    text: str | None = Field(None, description="The annotation text, as markdown (required by R4).")


class ConditionQuantityInput(FhirInputModel):
    """Age (onsetAge / abatementAge) — a Quantity with a time unit."""

    value: float | int | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form (usually http://unitsofmeasure.org).")
    code: str | None = Field(None, description="Coded form of the unit.")


class ConditionRangeInput(FhirInputModel):
    """Range (onsetRange / abatementRange) — a low and a high Quantity."""

    low: ConditionQuantityInput | None = Field(None, description="Low limit.")
    high: ConditionQuantityInput | None = Field(None, description="High limit.")


class ConditionStageInput(FhirInputModel):
    """Condition.stage — stage/grade, usually assessed formally."""

    summary: FhirCodeableConceptInput | None = Field(None, description="Simple summary (disease specific).")
    assessment: list[FhirReferenceInput] | None = Field(None, description="Formal record of assessment — Reference(ClinicalImpression | DiagnosticReport | Observation).")
    type: FhirCodeableConceptInput | None = Field(None, description="Kind of staging, such as pathological or clinical staging.")


class ConditionEvidenceInput(FhirInputModel):
    """Condition.evidence — supporting evidence / manifestations that are the basis of the condition."""

    code: list[FhirCodeableConceptInput] | None = Field(None, description="Manifestation/symptom.")
    detail: list[FhirReferenceInput] | None = Field(None, description="Supporting information found elsewhere — Reference(Any).")


class _ConditionFields(FhirInputModel):
    """Every writable Condition element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/condition.html). Create and patch accept
    exactly the same fields. R4 requires `subject` (and rules con-3/con-4/con-5
    tie `clinicalStatus` to `verificationStatus`, `category` and `abatement[x]`);
    that is enforced by base R4 validation of the stored document (the
    `java_validator` backend — the native structural check has no cardinality
    minimums or invariants), not by this model. A PATCH may omit them: it is
    merged onto the current resource before validating.

    The validated body is stored whole (ConditionModel.content), so any valid R4
    element is kept — including ones this model does not declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    condition_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Condition"] | None = Field(None, description="Optional; if supplied it must be 'Condition'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="External Ids for this condition.")
    clinicalStatus: FhirCodeableConceptInput | None = Field(None, description="active | recurrence | relapse | inactive | remission | resolved (system http://terminology.hl7.org/CodeSystem/condition-clinical).")
    verificationStatus: FhirCodeableConceptInput | None = Field(None, description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error (system http://terminology.hl7.org/CodeSystem/condition-ver-status).")
    category: list[FhirCodeableConceptInput] | None = Field(None, description="problem-list-item | encounter-diagnosis (extensible binding).")
    severity: FhirCodeableConceptInput | None = Field(None, description="Subjective severity of condition.")
    code: FhirCodeableConceptInput | None = Field(None, description="Identification of the condition, problem or diagnosis.")
    bodySite: list[FhirCodeableConceptInput] | None = Field(None, description="Anatomical location, if relevant.")
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who has the condition — Reference(Patient | Group) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Encounter created as part of — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    onsetDateTime: str | None = Field(None, description="Estimated or actual date, date-time, or age (a FHIR dateTime). One of the onset[x] choices.")
    onsetAge: ConditionQuantityInput | None = Field(None, description="Estimated or actual age (an Age). One of the onset[x] choices.")
    onsetPeriod: FhirPeriodInput | None = Field(None, description="Estimated or actual period (a Period). One of the onset[x] choices.")
    onsetRange: ConditionRangeInput | None = Field(None, description="Estimated or actual age range (a Range). One of the onset[x] choices.")
    onsetString: str | None = Field(None, description="Estimated or actual onset as text. One of the onset[x] choices.")
    abatementDateTime: str | None = Field(None, description="When in resolution/remission (a FHIR dateTime). One of the abatement[x] choices.")
    abatementAge: ConditionQuantityInput | None = Field(None, description="When in resolution/remission (an Age). One of the abatement[x] choices.")
    abatementPeriod: FhirPeriodInput | None = Field(None, description="When in resolution/remission (a Period). One of the abatement[x] choices.")
    abatementRange: ConditionRangeInput | None = Field(None, description="When in resolution/remission (a Range). One of the abatement[x] choices.")
    abatementString: str | None = Field(None, description="When in resolution/remission, as text. One of the abatement[x] choices.")
    recordedDate: str | None = Field(None, description="Date record was first recorded (a FHIR dateTime).")
    recorder: FhirReferenceInput | None = Field(None, description="Who recorded the condition — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise).")
    asserter: FhirReferenceInput | None = Field(None, description="Person who asserts this condition — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise).")
    stage: list[ConditionStageInput] | None = Field(None, description="Stage/grade, usually assessed formally.")
    evidence: list[ConditionEvidenceInput] | None = Field(None, description="Supporting evidence.")
    note: list[ConditionAnnotationInput] | None = Field(None, description="Additional information about the Condition.")


class ConditionCreateSchema(_ConditionFields):
    """POST body — a FHIR R4 Condition resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ConditionPatchSchema(_ConditionFields):
    """PATCH body — a partial FHIR R4 Condition (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `clinicalStatus` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "resolved"}]
                },
                "abatementDateTime": "2024-05-01",
            }
        }
    }

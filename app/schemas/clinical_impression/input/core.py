from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# ClinicalImpressionStatus (the required binding of ClinicalImpression.status).
StatusCode = Literal["in-progress", "completed", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "ClinicalImpression",
    "identifier": [
        {"system": "https://fhir-server.dev/fhir/identifier-system/clinical-impression-id", "value": "CI-1001"}
    ],
    "status": "completed",
    "code": {"text": "Initial assessment"},
    "description": "Assessment of the patient's chest pain.",
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "date": "2023-01-15T10:00:00Z",
    "assessor": {"reference": "Practitioner/30001"},
    "problem": [{"reference": "Condition/120001"}],
    "investigation": [
        {
            "code": {"text": "Initial examination"},
            "item": [{"reference": "DiagnosticReport/110001"}],
        }
    ],
    "summary": "Stable angina suspected; stress test arranged.",
    "finding": [
        {
            "itemCodeableConcept": {
                "coding": [{"system": "http://snomed.info/sct", "code": "194828000", "display": "Angina"}]
            },
            "basis": "Exercise ECG and history.",
        }
    ],
    "prognosisCodeableConcept": [{"text": "Good"}],
    "note": [{"text": "Review in 2 weeks."}],
}


class ClinicalImpressionAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made (a FHIR dateTime).")
    text: str | None = Field(None, description="The annotation text, as markdown (required by R4).")


class ClinicalImpressionInvestigationInput(FhirInputModel):
    """ClinicalImpression.investigation — one set of investigations that were part of the assessment."""

    code: FhirCodeableConceptInput | None = Field(None, description="A name/code for the set (required by R4).")
    item: list[FhirReferenceInput] | None = Field(
        None,
        description="Record of a specific investigation — Reference(Observation | QuestionnaireResponse | FamilyMemberHistory | DiagnosticReport | RiskAssessment | ImagingStudy | Media). A relative RiskAssessment, FamilyMemberHistory or DiagnosticReport must exist in the caller's org (422 otherwise). Searched by `investigation`.",
    )


class ClinicalImpressionFindingInput(FhirInputModel):
    """ClinicalImpression.finding — a possible diagnosis or other finding."""

    itemCodeableConcept: FhirCodeableConceptInput | None = Field(None, description="What was found. Searched by `finding-code`.")
    itemReference: FhirReferenceInput | None = Field(
        None,
        description="What was found — Reference(Condition | Observation | Media). A relative Condition must exist in the caller's org (422 otherwise). Searched by `finding-ref`.",
    )
    basis: str | None = Field(None, description="Which investigations support the finding.")


class _ClinicalImpressionFields(FhirInputModel):
    """Every writable ClinicalImpression element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/clinicalimpression.html). Create and patch accept exactly the
    same fields. R4 requires `status` and `subject` (and `investigation.code`); that is enforced
    by base R4 validation of the stored document (the `java_validator` backend — the native
    structural check has no cardinality minimums or invariants), not by this model. A PATCH may
    omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (ClinicalImpressionModel.content), so any valid R4 element
    is kept — including ones this model does not declare. Server-managed elements are ignored
    if sent: `id` (assigned from the clinical_impression_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["ClinicalImpression"] | None = Field(None, description="Optional; if supplied it must be 'ClinicalImpression'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="Business identifier.")
    status: StatusCode | None = Field(None, description="in-progress | completed | entered-in-error (required by R4).")
    statusReason: FhirCodeableConceptInput | None = Field(None, description="Reason for current status.")
    code: FhirCodeableConceptInput | None = Field(None, description="Kind of assessment performed.")
    description: str | None = Field(None, description="Why/how the assessment was performed.")
    subject: FhirReferenceInput | None = Field(
        None,
        description="Patient or group assessed — Reference(Patient | Group) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Encounter created as part of — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    effectiveDateTime: str | None = Field(None, description="Time of assessment (a FHIR dateTime). One of the effective[x] choices.")
    effectivePeriod: FhirPeriodInput | None = Field(None, description="Time of assessment (a Period). One of the effective[x] choices.")
    date: str | None = Field(None, description="When the assessment was documented (a FHIR dateTime). Searched by `date`.")
    assessor: FhirReferenceInput | None = Field(
        None,
        description="The clinician performing the assessment — Reference(Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).",
    )
    previous: FhirReferenceInput | None = Field(None, description="Reference to last assessment — Reference(ClinicalImpression). A relative reference must exist in the caller's org (422 otherwise).")
    problem: list[FhirReferenceInput] | None = Field(
        None,
        description="Relevant impressions of patient state — Reference(Condition | AllergyIntolerance). A relative reference must exist in the caller's org (422 otherwise).",
    )
    investigation: list[ClinicalImpressionInvestigationInput] | None = Field(None, description="One or more sets of investigations (signs, symptoms, etc.).")
    protocol: list[str] | None = Field(None, description="Clinical Protocol followed (URIs).")
    summary: str | None = Field(None, description="Summary of the assessment.")
    finding: list[ClinicalImpressionFindingInput] | None = Field(None, description="Possible or likely findings and diagnoses.")
    prognosisCodeableConcept: list[FhirCodeableConceptInput] | None = Field(None, description="Estimate of likely outcome.")
    prognosisReference: list[FhirReferenceInput] | None = Field(None, description="RiskAssessment expressing likely outcome — Reference(RiskAssessment). A relative reference must exist in the caller's org (422 otherwise).")
    supportingInfo: list[FhirReferenceInput] | None = Field(None, description="Information supporting the clinical impression — Reference(Any). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).")
    note: list[ClinicalImpressionAnnotationInput] | None = Field(None, description="Comments made about the ClinicalImpression.")


class ClinicalImpressionCreateSchema(_ClinicalImpressionFields):
    """POST body — a FHIR R4 ClinicalImpression resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ClinicalImpressionPatchSchema(_ClinicalImpressionFields):
    """PATCH body — a partial FHIR R4 ClinicalImpression (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale — a list (even `[]`) replaces every existing
    entry, an object such as `subject` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "summary": "Stable angina confirmed after stress test.",
            }
        }
    }

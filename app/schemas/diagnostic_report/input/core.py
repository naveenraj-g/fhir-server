from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

StatusCode = Literal[
    "registered", "partial", "preliminary", "final", "amended", "corrected", "appended", "cancelled",
    "entered-in-error", "unknown",
]

_EXAMPLE = {
    "resourceType": "DiagnosticReport",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/report-id", "value": "DR-1001"}],
    "basedOn": [{"reference": "ServiceRequest/80001"}],
    "status": "final",
    "category": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB", "display": "Laboratory"}]}
    ],
    "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2", "display": "CBC panel - Blood by Automated count"}]},
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "issued": "2023-01-15T12:00:00Z",
    "performer": [{"reference": "Practitioner/30001"}],
    "resultsInterpreter": [{"reference": "Practitioner/30001"}],
    "specimen": [{"reference": "Specimen/310001"}],
    "result": [{"reference": "Observation/160001"}],
    "conclusion": "Normal blood count.",
    "conclusionCode": [{"coding": [{"system": "http://snomed.info/sct", "code": "17621005", "display": "Normal"}]}],
}


class DiagnosticReportMediaInput(FhirInputModel):
    """DiagnosticReport.media — a key image associated with the report."""

    comment: str | None = Field(None, description="Comment about the image (e.g. explanation).")
    link: FhirReferenceInput | None = Field(None, description="Reference to the image source — Reference(Media) (required by R4).")


class _DiagnosticReportFields(FhirInputModel):
    """Every writable DiagnosticReport element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/diagnosticreport.html). Create and patch accept
    exactly the same fields. R4 requires `status` and `code`; that is enforced by
    base R4 validation of the stored document (the `java_validator` backend — the
    native structural check has no cardinality minimums), not by this model. A
    PATCH may omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (DiagnosticReportModel.content), so any valid
    R4 element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the diagnostic_report_id
    sequence) and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["DiagnosticReport"] | None = Field(None, description="Optional; if supplied it must be 'DiagnosticReport'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="Business identifier for report.")
    basedOn: list[FhirReferenceInput] | None = Field(None, description="What was requested — Reference(CarePlan | ImmunizationRecommendation | MedicationRequest | NutritionOrder | ServiceRequest).")
    status: StatusCode | None = Field(None, description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown (required by R4).")
    category: list[FhirCodeableConceptInput] | None = Field(None, description="Service category.")
    code: FhirCodeableConceptInput | None = Field(None, description="Name/Code for this diagnostic report (required by R4).")
    subject: FhirReferenceInput | None = Field(
        None,
        description="The subject of the report — Reference(Patient | Group | Device | Location). A relative 'Patient/<id>' or 'Location/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Health care event when test ordered — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    effectiveDateTime: str | None = Field(None, description="Clinically relevant time/time-period for report (a FHIR dateTime). One of the effective[x] choices.")
    effectivePeriod: FhirPeriodInput | None = Field(None, description="Clinically relevant time/time-period for report (a Period). One of the effective[x] choices.")
    issued: str | None = Field(None, description="DateTime this version was made (a FHIR instant).")
    performer: list[FhirReferenceInput] | None = Field(None, description="Responsible Diagnostic Service — Reference(Practitioner | PractitionerRole | Organization | CareTeam). A relative Practitioner, PractitionerRole or Organization must exist in the caller's org (422 otherwise).")
    resultsInterpreter: list[FhirReferenceInput] | None = Field(None, description="Primary result interpreter — Reference(Practitioner | PractitionerRole | Organization | CareTeam). A relative Practitioner, PractitionerRole or Organization must exist in the caller's org (422 otherwise).")
    specimen: list[FhirReferenceInput] | None = Field(None, description="Specimens this report is based on — Reference(Specimen).")
    result: list[FhirReferenceInput] | None = Field(None, description="Observations — Reference(Observation).")
    imagingStudy: list[FhirReferenceInput] | None = Field(None, description="Reference to full details of imaging associated with the diagnostic report — Reference(ImagingStudy).")
    media: list[DiagnosticReportMediaInput] | None = Field(None, description="Key images associated with this report.")
    conclusion: str | None = Field(None, description="Clinical conclusion (interpretation) of test results.")
    conclusionCode: list[FhirCodeableConceptInput] | None = Field(None, description="Codes for the clinical conclusion of test results.")
    presentedForm: list[FhirAttachmentInput] | None = Field(None, description="Entire report as issued.")


class DiagnosticReportCreateSchema(_DiagnosticReportFields):
    """POST body — a FHIR R4 DiagnosticReport resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class DiagnosticReportPatchSchema(_DiagnosticReportFields):
    """PATCH body — a partial FHIR R4 DiagnosticReport (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `code` replaces
    the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "amended",
                "conclusion": "Corrected: borderline anaemia.",
            }
        }
    }

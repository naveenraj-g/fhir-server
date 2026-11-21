from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# ObservationStatus (the required binding of DetectedIssue.status).
StatusCode = Literal[
    "registered",
    "preliminary",
    "final",
    "amended",
    "corrected",
    "cancelled",
    "entered-in-error",
    "unknown",
]
# DetectedIssueSeverity (the required binding of DetectedIssue.severity).
SeverityCode = Literal["high", "moderate", "low"]

_EXAMPLE = {
    "resourceType": "DetectedIssue",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/detected-issue-id",
            "value": "DI-1001",
        }
    ],
    "status": "final",
    "code": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "DUPTHPY",
                "display": "Duplicate therapy alert",
            }
        ]
    },
    "severity": "high",
    "patient": {"reference": "Patient/10001"},
    "identifiedDateTime": "2023-01-15T09:30:00Z",
    "author": {"reference": "Practitioner/30001"},
    "implicated": [{"reference": "Condition/120001"}],
    "evidence": [
        {
            "code": [{"text": "Two active statin prescriptions"}],
            "detail": [{"reference": "DiagnosticReport/110001"}],
        }
    ],
    "detail": "The patient is prescribed two drugs of the same class.",
    "reference": "http://example.org/protocols/duplicate-therapy",
    "mitigation": [
        {
            "action": {"text": "Stopped the older prescription"},
            "date": "2023-01-16T08:00:00Z",
            "author": {"reference": "Practitioner/30001"},
        }
    ],
}


class DetectedIssueEvidenceInput(FhirInputModel):
    """DetectedIssue.evidence — supporting evidence or manifestations."""

    code: list[FhirCodeableConceptInput] | None = Field(
        None, description="Manifestation."
    )
    detail: list[FhirReferenceInput] | None = Field(
        None,
        description="Supporting information — Reference(Any). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )


class DetectedIssueMitigationInput(FhirInputModel):
    """DetectedIssue.mitigation — a step taken to address the issue."""

    action: FhirCodeableConceptInput | None = Field(
        None, description="What mitigation? (required by R4)."
    )
    date: str | None = Field(None, description="Date committed (a FHIR dateTime).")
    author: FhirReferenceInput | None = Field(
        None,
        description="Who is committing? — Reference(Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).",
    )


class _DetectedIssueFields(FhirInputModel):
    """Every writable DetectedIssue element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/detectedissue.html). Create and patch accept exactly the same
    fields. R4 requires `status` (and `mitigation.action`); that is enforced by base R4
    validation of the stored document (the `java_validator` backend — the native structural
    check has no cardinality minimums or invariants), not by this model. A PATCH may omit it:
    it is merged onto the current resource before validating.

    The validated body is stored whole (DetectedIssueModel.content), so any valid R4 element
    is kept — including ones this model does not declare. Server-managed elements are ignored
    if sent: `id` (assigned from the detected_issue_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["DetectedIssue"] | None = Field(
        None, description="Optional; if supplied it must be 'DetectedIssue'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Unique id for the detected issue."
    )
    status: StatusCode | None = Field(
        None,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown (required by R4).",
    )
    code: FhirCodeableConceptInput | None = Field(
        None,
        description="Issue category, e.g. drug-drug, duplicate therapy. Searched by `code`.",
    )
    severity: SeverityCode | None = Field(None, description="high | moderate | low.")
    patient: FhirReferenceInput | None = Field(
        None,
        description="Associated patient — Reference(Patient). A relative reference must exist in the caller's org (422 otherwise).",
    )
    identifiedDateTime: str | None = Field(
        None,
        description="When identified (a FHIR dateTime). One of the identified[x] choices.",
    )
    identifiedPeriod: FhirPeriodInput | None = Field(
        None,
        description="When identified (a Period). One of the identified[x] choices.",
    )
    author: FhirReferenceInput | None = Field(
        None,
        description="The provider or device that identified the issue — Reference(Practitioner | PractitionerRole | Device). A relative Practitioner or PractitionerRole must exist in the caller's org (422 otherwise).",
    )
    implicated: list[FhirReferenceInput] | None = Field(
        None,
        description="Problem resource — Reference(Any). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )
    evidence: list[DetectedIssueEvidenceInput] | None = Field(
        None, description="Supporting evidence."
    )
    detail: str | None = Field(None, description="Description and context.")
    reference: str | None = Field(None, description="Authority for the issue (a URI).")
    mitigation: list[DetectedIssueMitigationInput] | None = Field(
        None, description="Step taken to address."
    )


class DetectedIssueCreateSchema(_DetectedIssueFields):
    """POST body — a FHIR R4 DetectedIssue resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class DetectedIssuePatchSchema(_DetectedIssueFields):
    """PATCH body — a partial FHIR R4 DetectedIssue (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale — a list (even `[]`) replaces every existing
    entry, an object such as `patient` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "amended",
                "severity": "moderate",
            }
        }
    }

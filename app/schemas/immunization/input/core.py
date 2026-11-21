from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

StatusCode = Literal["completed", "entered-in-error", "not-done"]

_EXAMPLE = {
    "resourceType": "Immunization",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/immunization-id",
            "value": "IM-1001",
        }
    ],
    "status": "completed",
    "vaccineCode": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/sid/cvx",
                "code": "140",
                "display": "Influenza, seasonal, injectable, preservative free",
            }
        ]
    },
    "patient": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "occurrenceDateTime": "2023-01-15T09:30:00Z",
    "recorded": "2023-01-15T10:00:00Z",
    "primarySource": True,
    "location": {"reference": "Location/230001"},
    "manufacturer": {"reference": "Organization/190001"},
    "lotNumber": "AAJN11K",
    "expirationDate": "2025-02-15",
    "site": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                "code": "LA",
                "display": "left arm",
            }
        ]
    },
    "route": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                "code": "IM",
                "display": "Injection, intramuscular",
            }
        ]
    },
    "doseQuantity": {"value": 5, "system": "http://unitsofmeasure.org", "code": "mg"},
    "performer": [
        {
            "function": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                        "code": "AP",
                    }
                ]
            },
            "actor": {"reference": "Practitioner/30001"},
        }
    ],
    "note": [{"text": "Notes on adminstration of vaccine"}],
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "429060002"}]}
    ],
    "isSubpotent": False,
    "protocolApplied": [
        {
            "series": "2-dose",
            "targetDisease": [
                {"coding": [{"system": "http://snomed.info/sct", "code": "40468003"}]}
            ],
            "doseNumberPositiveInt": 1,
        }
    ],
}


class ImmunizationAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(
        None, description="When the annotation was made (a FHIR dateTime)."
    )
    text: str | None = Field(
        None, description="The annotation text, as markdown (required by R4)."
    )


class ImmunizationQuantityInput(FhirInputModel):
    """SimpleQuantity (doseQuantity) — a Quantity with no comparator."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class ImmunizationPerformerInput(FhirInputModel):
    """Immunization.performer — who did what."""

    function: FhirCodeableConceptInput | None = Field(
        None,
        description="What type of performance was done (Ordering Provider, Administering Provider...).",
    )
    actor: FhirReferenceInput | None = Field(
        None,
        description="Individual or organization who was performing — Reference(Practitioner | PractitionerRole | Organization) (required by R4). A relative reference must exist in the caller's org (422 otherwise).",
    )


class ImmunizationEducationInput(FhirInputModel):
    """Immunization.education — educational material presented to the patient."""

    documentType: str | None = Field(
        None,
        description="Educational material document identifier (one of documentType or reference is required by R4).",
    )
    reference: str | None = Field(
        None, description="Educational material reference pointer (a URI)."
    )
    publicationDate: str | None = Field(
        None, description="Educational material publication date (a FHIR dateTime)."
    )
    presentationDate: str | None = Field(
        None, description="Educational material presentation date (a FHIR dateTime)."
    )


class ImmunizationReactionInput(FhirInputModel):
    """Immunization.reaction — details of a reaction that follows immunization."""

    date: str | None = Field(
        None, description="When the reaction started (a FHIR dateTime)."
    )
    detail: FhirReferenceInput | None = Field(
        None,
        description="Additional information on the reaction — Reference(Observation).",
    )
    reported: bool | None = Field(
        None, description="Indicates a self-reported reaction."
    )


class ImmunizationProtocolAppliedInput(FhirInputModel):
    """Immunization.protocolApplied — the protocol the provider followed."""

    series: str | None = Field(None, description="Name of the vaccine series.")
    authority: FhirReferenceInput | None = Field(
        None,
        description="Who is responsible for publishing the recommendations — Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    targetDisease: list[FhirCodeableConceptInput] | None = Field(
        None, description="Vaccine preventable disease being targeted."
    )
    doseNumberPositiveInt: int | None = Field(
        None,
        description="Dose number within the series (a positiveInt). One of the doseNumber[x] choices (required by R4).",
    )
    doseNumberString: str | None = Field(
        None,
        description="Dose number within the series (a string). One of the doseNumber[x] choices.",
    )
    seriesDosesPositiveInt: int | None = Field(
        None,
        description="Recommended number of doses for immunity (a positiveInt). One of the seriesDoses[x] choices.",
    )
    seriesDosesString: str | None = Field(
        None,
        description="Recommended number of doses for immunity (a string). One of the seriesDoses[x] choices.",
    )


class _ImmunizationFields(FhirInputModel):
    """Every writable Immunization element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/immunization.html). Create and patch accept
    exactly the same fields. R4 requires `status`, `vaccineCode`, `patient` and
    one of `occurrenceDateTime`/`occurrenceString`; that is enforced by base R4
    validation of the stored document (the `java_validator` backend — the native
    structural check has no cardinality minimums), not by this model. A PATCH may
    omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (ImmunizationModel.content), so any valid
    R4 element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the immunization_id
    sequence) and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["Immunization"] | None = Field(
        None, description="Optional; if supplied it must be 'Immunization'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    status: StatusCode | None = Field(
        None, description="completed | entered-in-error | not-done (required by R4)."
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason not done."
    )
    vaccineCode: FhirCodeableConceptInput | None = Field(
        None, description="Vaccine product administered (required by R4)."
    )
    patient: FhirReferenceInput | None = Field(
        None,
        description="Who was immunized — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter immunization was part of — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).",
    )
    occurrenceDateTime: str | None = Field(
        None,
        description="Vaccine administration date (a FHIR dateTime). One of the occurrence[x] choices (required by R4).",
    )
    occurrenceString: str | None = Field(
        None,
        description="Vaccine administration date (a string). One of the occurrence[x] choices.",
    )
    recorded: str | None = Field(
        None,
        description="When the immunization was first captured in the subject's record (a FHIR dateTime).",
    )
    primarySource: bool | None = Field(
        None,
        description="Indicates the context the data was recorded in (true = the immunization was reported by the provider who administered it).",
    )
    reportOrigin: FhirCodeableConceptInput | None = Field(
        None, description="Indicates the source of a secondarily reported record."
    )
    location: FhirReferenceInput | None = Field(
        None,
        description="Where the immunization occurred — Reference(Location). A relative reference must exist in the caller's org (422 otherwise).",
    )
    manufacturer: FhirReferenceInput | None = Field(
        None,
        description="Vaccine manufacturer — Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    lotNumber: str | None = Field(None, description="Vaccine lot number.")
    expirationDate: str | None = Field(
        None, description="Vaccine expiration date (a FHIR date)."
    )
    site: FhirCodeableConceptInput | None = Field(
        None, description="Body site vaccine was administered."
    )
    route: FhirCodeableConceptInput | None = Field(
        None, description="How the vaccine entered the body."
    )
    doseQuantity: ImmunizationQuantityInput | None = Field(
        None, description="Amount of vaccine administered."
    )
    performer: list[ImmunizationPerformerInput] | None = Field(
        None, description="Who performed the event."
    )
    note: list[ImmunizationAnnotationInput] | None = Field(
        None, description="Additional immunization notes."
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Why the immunization occurred."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why the immunization occurred — Reference(Condition | Observation | DiagnosticReport). A relative Condition or DiagnosticReport must exist in the caller's org (422 otherwise).",
    )
    isSubpotent: bool | None = Field(
        None, description="Dose potency (true = the dose was subpotent)."
    )
    subpotentReason: list[FhirCodeableConceptInput] | None = Field(
        None, description="Reason for being subpotent."
    )
    education: list[ImmunizationEducationInput] | None = Field(
        None, description="Educational material presented to the patient."
    )
    programEligibility: list[FhirCodeableConceptInput] | None = Field(
        None, description="Patient eligibility for a vaccination program."
    )
    fundingSource: FhirCodeableConceptInput | None = Field(
        None, description="Funding source for the vaccine."
    )
    reaction: list[ImmunizationReactionInput] | None = Field(
        None, description="Details of a reaction that follows immunization."
    )
    protocolApplied: list[ImmunizationProtocolAppliedInput] | None = Field(
        None, description="Protocol followed by the provider."
    )


class ImmunizationCreateSchema(_ImmunizationFields):
    """POST body — a FHIR R4 Immunization resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ImmunizationPatchSchema(_ImmunizationFields):
    """PATCH body — a partial FHIR R4 Immunization (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `vaccineCode`
    replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "entered-in-error",
                "note": [{"text": "Recorded against the wrong patient."}],
            }
        }
    }

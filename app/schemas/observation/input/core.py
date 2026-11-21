from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# ObservationStatus (the required binding of Observation.status).
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

_EXAMPLE = {
    "resourceType": "Observation",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/observation-id",
            "value": "OBS-1001",
        }
    ],
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "issued": "2023-01-15T09:35:00Z",
    "performer": [{"reference": "Practitioner/30001"}],
    "interpretation": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                }
            ]
        }
    ],
    "component": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure",
                    }
                ]
            },
            "valueQuantity": {
                "value": 142,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            },
        },
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8462-4",
                        "display": "Diastolic blood pressure",
                    }
                ]
            },
            "valueQuantity": {
                "value": 91,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            },
        },
    ],
}


class ObservationQuantityInput(FhirInputModel):
    """Quantity — a measured amount (also the SimpleQuantity bounds of a Range or a reference range)."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="< | <= | >= | > — how to understand the value."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class ObservationRangeInput(FhirInputModel):
    """Range — a low and a high Quantity."""

    low: ObservationQuantityInput | None = Field(None, description="Low limit.")
    high: ObservationQuantityInput | None = Field(None, description="High limit.")


class ObservationRatioInput(FhirInputModel):
    """Ratio — a numerator and a denominator Quantity."""

    numerator: ObservationQuantityInput | None = Field(
        None, description="Numerator value."
    )
    denominator: ObservationQuantityInput | None = Field(
        None, description="Denominator value."
    )


class ObservationAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
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


class ObservationReferenceRangeInput(FhirInputModel):
    """Observation.referenceRange — provides guide for interpretation (also on a component)."""

    low: ObservationQuantityInput | None = Field(
        None, description="Low Range, if relevant."
    )
    high: ObservationQuantityInput | None = Field(
        None, description="High Range, if relevant."
    )
    type: FhirCodeableConceptInput | None = Field(
        None, description="Reference range qualifier (normal, therapeutic, ...)."
    )
    appliesTo: list[FhirCodeableConceptInput] | None = Field(
        None, description="Reference range population."
    )
    age: ObservationRangeInput | None = Field(
        None, description="Applicable age range, if relevant."
    )
    text: str | None = Field(
        None, description="Text based reference range in an observation."
    )


class ObservationComponentInput(FhirInputModel):
    """Observation.component — a component result, e.g. systolic and diastolic blood pressure."""

    code: FhirCodeableConceptInput | None = Field(
        None,
        description="Type of component observation (code / type) (required by R4).",
    )
    valueQuantity: ObservationQuantityInput | None = Field(
        None,
        description="Actual component result (a Quantity). One of the value[x] choices.",
    )
    valueCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Actual component result (a CodeableConcept). One of the value[x] choices.",
    )
    valueString: str | None = Field(
        None,
        description="Actual component result (a string). One of the value[x] choices.",
    )
    valueBoolean: bool | None = Field(
        None,
        description="Actual component result (a boolean). One of the value[x] choices.",
    )
    valueInteger: int | None = Field(
        None,
        description="Actual component result (an integer). One of the value[x] choices.",
    )
    valueRange: ObservationRangeInput | None = Field(
        None,
        description="Actual component result (a Range). One of the value[x] choices.",
    )
    valueRatio: ObservationRatioInput | None = Field(
        None,
        description="Actual component result (a Ratio). One of the value[x] choices.",
    )
    valueSampledData: dict | None = Field(
        None,
        description="Actual component result (SampledData). One of the value[x] choices.",
    )
    valueTime: str | None = Field(
        None,
        description="Actual component result (a time). One of the value[x] choices.",
    )
    valueDateTime: str | None = Field(
        None,
        description="Actual component result (a dateTime). One of the value[x] choices.",
    )
    valuePeriod: FhirPeriodInput | None = Field(
        None,
        description="Actual component result (a Period). One of the value[x] choices.",
    )
    dataAbsentReason: FhirCodeableConceptInput | None = Field(
        None, description="Why the component result is missing."
    )
    interpretation: list[FhirCodeableConceptInput] | None = Field(
        None, description="High, low, normal, etc."
    )
    referenceRange: list[ObservationReferenceRangeInput] | None = Field(
        None, description="Provides guide for interpretation of component result."
    )


class _ObservationFields(FhirInputModel):
    """Every writable Observation element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/observation.html). Create and patch accept exactly the same
    fields. R4 requires `status` and `code` (and each component's `code`) and rules obs-3, obs-6
    and obs-7; that is enforced by base R4 validation of the stored document (the `java_validator`
    backend — the native structural check has no cardinality minimums or invariants), not by this
    model. A PATCH may omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (ObservationModel.content), so any valid R4 element is kept
    — including ones this model does not declare. Server-managed elements are ignored if sent: `id`
    (assigned from the observation_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["Observation"] | None = Field(
        None, description="Optional; if supplied it must be 'Observation'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business Identifier for observation."
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Fulfills plan, proposal or order — Reference(CarePlan | DeviceRequest | ImmunizationRecommendation | MedicationRequest | NutritionOrder | ServiceRequest). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Part of referenced event — Reference(MedicationAdministration | MedicationDispense | MedicationStatement | Procedure | Immunization | ImagingStudy). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )
    status: StatusCode | None = Field(
        None,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown (required by R4).",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Classification of type of observation."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Type of observation (code / type) (required by R4)."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who and/or what the observation is about — Reference(Patient | Group | Device | Location). A relative Patient, Group or Location must exist in the caller's org (422 otherwise).",
    )
    focus: list[FhirReferenceInput] | None = Field(
        None,
        description="What the observation is about, when it is not about the subject of record — Reference(Any). Stored as sent.",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Healthcare event during which this observation is made — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).",
    )
    effectiveDateTime: str | None = Field(
        None,
        description="Clinically relevant time/time-period for observation (a dateTime). One of the effective[x] choices.",
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="Clinically relevant time/time-period for observation (a Period). One of the effective[x] choices.",
    )
    effectiveTiming: dict | None = Field(
        None,
        description="Clinically relevant time/time-period for observation (a Timing). One of the effective[x] choices.",
    )
    effectiveInstant: str | None = Field(
        None,
        description="Clinically relevant time/time-period for observation (an instant). One of the effective[x] choices.",
    )
    issued: str | None = Field(
        None, description="Date/Time this version was made available (an instant)."
    )
    performer: list[FhirReferenceInput] | None = Field(
        None,
        description="Who is responsible for the observation — Reference(Practitioner | PractitionerRole | Organization | CareTeam | Patient | RelatedPerson). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )
    valueQuantity: ObservationQuantityInput | None = Field(
        None, description="Actual result (a Quantity). One of the value[x] choices."
    )
    valueCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Actual result (a CodeableConcept). One of the value[x] choices.",
    )
    valueString: str | None = Field(
        None, description="Actual result (a string). One of the value[x] choices."
    )
    valueBoolean: bool | None = Field(
        None, description="Actual result (a boolean). One of the value[x] choices."
    )
    valueInteger: int | None = Field(
        None, description="Actual result (an integer). One of the value[x] choices."
    )
    valueRange: ObservationRangeInput | None = Field(
        None, description="Actual result (a Range). One of the value[x] choices."
    )
    valueRatio: ObservationRatioInput | None = Field(
        None, description="Actual result (a Ratio). One of the value[x] choices."
    )
    valueSampledData: dict | None = Field(
        None, description="Actual result (SampledData). One of the value[x] choices."
    )
    valueTime: str | None = Field(
        None, description="Actual result (a time). One of the value[x] choices."
    )
    valueDateTime: str | None = Field(
        None, description="Actual result (a dateTime). One of the value[x] choices."
    )
    valuePeriod: FhirPeriodInput | None = Field(
        None, description="Actual result (a Period). One of the value[x] choices."
    )
    dataAbsentReason: FhirCodeableConceptInput | None = Field(
        None, description="Why the result is missing."
    )
    interpretation: list[FhirCodeableConceptInput] | None = Field(
        None, description="High, low, normal, etc."
    )
    note: list[ObservationAnnotationInput] | None = Field(
        None, description="Comments about the observation."
    )
    bodySite: FhirCodeableConceptInput | None = Field(
        None, description="Observed body part."
    )
    method: FhirCodeableConceptInput | None = Field(
        None, description="How it was done."
    )
    specimen: FhirReferenceInput | None = Field(
        None,
        description="Specimen used for this observation — Reference(Specimen). A relative reference must exist in the caller's org (422 otherwise).",
    )
    device: FhirReferenceInput | None = Field(
        None,
        description="(Measurement) Device — Reference(Device | DeviceMetric). Stored as sent.",
    )
    referenceRange: list[ObservationReferenceRangeInput] | None = Field(
        None, description="Provides guide for interpretation."
    )
    hasMember: list[FhirReferenceInput] | None = Field(
        None,
        description="Related resource that belongs to the Observation group — Reference(Observation | QuestionnaireResponse | MolecularSequence). A relative Observation or QuestionnaireResponse must exist in the caller's org (422 otherwise).",
    )
    derivedFrom: list[FhirReferenceInput] | None = Field(
        None,
        description="Related measurements the observation is made from — Reference(DocumentReference | ImagingStudy | Media | QuestionnaireResponse | Observation | MolecularSequence). A relative reference to a resource this server holds must exist in the caller's org (422 otherwise).",
    )
    component: list[ObservationComponentInput] | None = Field(
        None, description="Component results."
    )


class ObservationCreateSchema(_ObservationFields):
    """POST body — a FHIR R4 Observation resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ObservationPatchSchema(_ObservationFields):
    """PATCH body — a partial FHIR R4 Observation (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale — a list (even `[]`) replaces every existing
    entry, an object such as `subject` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "amended",
                "valueQuantity": {
                    "value": 120,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]",
                },
            }
        }
    }

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

TypeCode = Literal["allergy", "intolerance"]
CategoryCode = Literal["food", "medication", "environment", "biologic"]
CriticalityCode = Literal["low", "high", "unable-to-assess"]
SeverityCode = Literal["mild", "moderate", "severe"]

_EXAMPLE = {
    "resourceType": "AllergyIntolerance",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/allergy-id", "value": "AI-1001"}],
    "clinicalStatus": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
    },
    "verificationStatus": {
        "coding": [
            {"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": "confirmed"}
        ]
    },
    "type": "allergy",
    "category": ["food"],
    "criticality": "high",
    "code": {"coding": [{"system": "http://snomed.info/sct", "code": "227493005", "display": "Cashew nuts"}]},
    "patient": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "onsetDateTime": "2023-01-15T09:30:00Z",
    "recordedDate": "2023-01-15T10:00:00Z",
    "recorder": {"reference": "Practitioner/30001"},
    "asserter": {"reference": "Patient/10001"},
    "lastOccurrence": "2023-06-01T12:00:00Z",
    "note": [{"text": "Severe urticaria after cashew ingestion.", "time": "2023-01-15T10:05:00Z"}],
    "reaction": [
        {
            "substance": {"coding": [{"system": "http://snomed.info/sct", "code": "227493005"}]},
            "manifestation": [{"coding": [{"system": "http://snomed.info/sct", "code": "64305001", "display": "Urticaria"}]}],
            "description": "Severe hives on face and neck",
            "onset": "2023-01-15T09:40:00Z",
            "severity": "severe",
            "exposureRoute": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]},
        }
    ],
}


class AllergyIntoleranceAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made (a FHIR dateTime).")
    text: str | None = Field(None, description="The annotation text, as markdown (required by R4).")


class AllergyIntoleranceQuantityInput(FhirInputModel):
    """Age (onsetAge) — a Quantity with a time unit."""

    value: float | int | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form (usually http://unitsofmeasure.org).")
    code: str | None = Field(None, description="Coded form of the unit.")


class AllergyIntoleranceRangeInput(FhirInputModel):
    """Range (onsetRange) — a low and a high Quantity."""

    low: AllergyIntoleranceQuantityInput | None = Field(None, description="Low limit.")
    high: AllergyIntoleranceQuantityInput | None = Field(None, description="High limit.")


class AllergyIntoleranceReactionInput(FhirInputModel):
    """AllergyIntolerance.reaction — an adverse reaction event linked to exposure to the substance."""

    substance: FhirCodeableConceptInput | None = Field(None, description="Specific substance or pharmaceutical product considered to be responsible for the event.")
    manifestation: list[FhirCodeableConceptInput] | None = Field(None, description="Clinical symptoms/signs associated with the event (required by R4, at least one).")
    description: str | None = Field(None, description="Description of the event as a whole.")
    onset: str | None = Field(None, description="Date(/time) when manifestations showed (a FHIR dateTime).")
    severity: SeverityCode | None = Field(None, description="mild | moderate | severe (of event as a whole).")
    exposureRoute: FhirCodeableConceptInput | None = Field(None, description="How the subject was exposed to the substance.")
    note: list[AllergyIntoleranceAnnotationInput] | None = Field(None, description="Text about event not captured in other fields.")


class _AllergyIntoleranceFields(FhirInputModel):
    """Every writable AllergyIntolerance element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/allergyintolerance.html). Create and patch
    accept exactly the same fields. R4 requires `patient` (and rules ait-1/ait-2
    tie `clinicalStatus` to `verificationStatus`); that is enforced by base R4
    validation of the stored document (the `java_validator` backend — the native
    structural check has no cardinality minimums or invariants), not by this
    model. A PATCH may omit them: it is merged onto the current resource before
    validating.

    The validated body is stored whole (AllergyIntoleranceModel.content), so any
    valid R4 element is kept — including ones this model does not declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    allergy_intolerance_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["AllergyIntolerance"] | None = Field(None, description="Optional; if supplied it must be 'AllergyIntolerance'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="External ids for this item.")
    clinicalStatus: FhirCodeableConceptInput | None = Field(None, description="active | inactive | resolved (CodeableConcept; system http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical).")
    verificationStatus: FhirCodeableConceptInput | None = Field(None, description="unconfirmed | confirmed | refuted | entered-in-error (CodeableConcept; system http://terminology.hl7.org/CodeSystem/allergyintolerance-verification).")
    type: TypeCode | None = Field(None, description="allergy | intolerance - Underlying mechanism (if known).")
    category: list[CategoryCode] | None = Field(None, description="food | medication | environment | biologic.")
    criticality: CriticalityCode | None = Field(None, description="low | high | unable-to-assess - Estimate of the potential clinical harm, or seriousness, of the reaction to the identified substance.")
    code: FhirCodeableConceptInput | None = Field(None, description="Code that identifies the allergy or intolerance (substance, condition, or negation).")
    patient: FhirReferenceInput | None = Field(
        None,
        description="Who the sensitivity is for — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Encounter when the allergy or intolerance was asserted — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    onsetDateTime: str | None = Field(None, description="When allergy or intolerance was identified (a FHIR dateTime). One of the onset[x] choices.")
    onsetAge: AllergyIntoleranceQuantityInput | None = Field(None, description="When allergy or intolerance was identified (an Age). One of the onset[x] choices.")
    onsetPeriod: FhirPeriodInput | None = Field(None, description="When allergy or intolerance was identified (a Period). One of the onset[x] choices.")
    onsetRange: AllergyIntoleranceRangeInput | None = Field(None, description="When allergy or intolerance was identified (a Range). One of the onset[x] choices.")
    onsetString: str | None = Field(None, description="When allergy or intolerance was identified (text). One of the onset[x] choices.")
    recordedDate: str | None = Field(None, description="Date first version of the resource instance was recorded (a FHIR dateTime).")
    recorder: FhirReferenceInput | None = Field(None, description="Who recorded the sensitivity — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise).")
    asserter: FhirReferenceInput | None = Field(None, description="Source of the information about the allergy — Reference(Patient | RelatedPerson | Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).")
    lastOccurrence: str | None = Field(None, description="Date(/time) of last known occurrence of a reaction (a FHIR dateTime).")
    note: list[AllergyIntoleranceAnnotationInput] | None = Field(None, description="Additional text not captured in other fields.")
    reaction: list[AllergyIntoleranceReactionInput] | None = Field(None, description="Adverse Reaction Events linked to exposure to substance.")


class AllergyIntoleranceCreateSchema(_AllergyIntoleranceFields):
    """POST body — a FHIR R4 AllergyIntolerance resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class AllergyIntolerancePatchSchema(_AllergyIntoleranceFields):
    """PATCH body — a partial FHIR R4 AllergyIntolerance (merge-patch semantics
    on top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `clinicalStatus` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "criticality": "low",
                "clinicalStatus": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "resolved"}
                    ]
                },
            }
        }
    }

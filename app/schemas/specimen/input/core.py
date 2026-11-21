from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# SpecimenStatus (the required binding of Specimen.status).
StatusCode = Literal["available", "unavailable", "unsatisfactory", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "Specimen",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/specimen-id",
            "value": "SP-1001",
        }
    ],
    "accessionIdentifier": {
        "system": "http://lab.example.org/accessions",
        "value": "ACC-2023-0001",
    },
    "status": "available",
    "type": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
                "code": "BLD",
                "display": "Whole blood",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "receivedTime": "2023-01-15T11:00:00Z",
    "collection": {
        "collector": {"reference": "Practitioner/30001"},
        "collectedDateTime": "2023-01-15T09:30:00Z",
        "quantity": {
            "value": 6,
            "unit": "mL",
            "system": "http://unitsofmeasure.org",
            "code": "mL",
        },
        "bodySite": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "368208006",
                    "display": "Left upper arm structure",
                }
            ]
        },
    },
    "container": [
        {
            "identifier": [{"system": "urn:containers", "value": "C-1"}],
            "type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "434746001",
                        "display": "Specimen vial",
                    }
                ]
            },
            "capacity": {
                "value": 10,
                "unit": "mL",
                "system": "http://unitsofmeasure.org",
                "code": "mL",
            },
        }
    ],
    "note": [{"text": "Fasting sample."}],
}


class SpecimenQuantityInput(FhirInputModel):
    """Quantity (SimpleQuantity / Duration) — a measured amount."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class SpecimenAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise).",
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


class SpecimenCollectionInput(FhirInputModel):
    """Specimen.collection — collection details."""

    collector: FhirReferenceInput | None = Field(
        None,
        description="Who collected the specimen — Reference(Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise). Searched by `collector`.",
    )
    collectedDateTime: str | None = Field(
        None,
        description="Collection time (a FHIR dateTime). One of the collected[x] choices; searched by `collected`.",
    )
    collectedPeriod: FhirPeriodInput | None = Field(
        None,
        description="Collection time (a Period). One of the collected[x] choices; searched by `collected`.",
    )
    duration: SpecimenQuantityInput | None = Field(
        None, description="How long it took to collect specimen (a Duration)."
    )
    quantity: SpecimenQuantityInput | None = Field(
        None, description="The quantity of specimen collected."
    )
    method: FhirCodeableConceptInput | None = Field(
        None, description="Technique used to perform collection."
    )
    bodySite: FhirCodeableConceptInput | None = Field(
        None, description="Anatomical collection site. Searched by `bodysite`."
    )
    fastingStatusCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Whether or how long patient abstained from food and/or drink (a CodeableConcept). One of the fastingStatus[x] choices.",
    )
    fastingStatusDuration: SpecimenQuantityInput | None = Field(
        None,
        description="Whether or how long patient abstained from food and/or drink (a Duration). One of the fastingStatus[x] choices.",
    )


class SpecimenProcessingInput(FhirInputModel):
    """Specimen.processing — processing and processing step details."""

    description: str | None = Field(
        None, description="Textual description of procedure."
    )
    procedure: FhirCodeableConceptInput | None = Field(
        None, description="Indicates the treatment step applied to the specimen."
    )
    additive: list[FhirReferenceInput] | None = Field(
        None,
        description="Material used in the processing step — Reference(Substance). Stored as sent.",
    )
    timeDateTime: str | None = Field(
        None,
        description="Date and time of specimen processing (a dateTime). One of the time[x] choices.",
    )
    timePeriod: FhirPeriodInput | None = Field(
        None,
        description="Date and time of specimen processing (a Period). One of the time[x] choices.",
    )


class SpecimenContainerInput(FhirInputModel):
    """Specimen.container — direct container of specimen (tube/slide, etc.)."""

    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Id for the container. Searched by `container-id`."
    )
    description: str | None = Field(
        None, description="Textual description of the container."
    )
    type: FhirCodeableConceptInput | None = Field(
        None,
        description="Kind of container directly associated with specimen. Searched by `container`.",
    )
    capacity: SpecimenQuantityInput | None = Field(
        None, description="Container volume or size."
    )
    specimenQuantity: SpecimenQuantityInput | None = Field(
        None, description="Quantity of specimen within container."
    )
    additiveCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Additive associated with container (a CodeableConcept). One of the additive[x] choices.",
    )
    additiveReference: FhirReferenceInput | None = Field(
        None,
        description="Additive associated with container (Reference(Substance)). One of the additive[x] choices; stored as sent.",
    )


class _SpecimenFields(FhirInputModel):
    """Every writable Specimen element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/specimen.html). Create and patch accept exactly the same
    fields. R4 requires nothing beyond the types (every Specimen element is optional), so any
    well-formed document is valid.

    The validated body is stored whole (SpecimenModel.content), so any valid R4 element is kept —
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the specimen_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Specimen"] | None = Field(
        None, description="Optional; if supplied it must be 'Specimen'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Identifier."
    )
    accessionIdentifier: FhirIdentifierInput | None = Field(
        None, description="Identifier assigned by the lab. Searched by `accession`."
    )
    status: StatusCode | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: FhirCodeableConceptInput | None = Field(
        None, description="Kind of material that forms the specimen."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Where the specimen came from — Reference(Patient | Group | Device | Substance | Location). A relative Patient or Location must exist in the caller's org (422 otherwise).",
    )
    receivedTime: str | None = Field(
        None,
        description="The time when specimen was received for processing (a FHIR dateTime).",
    )
    parent: list[FhirReferenceInput] | None = Field(
        None,
        description="Specimen from which this specimen originated — Reference(Specimen). A relative reference must exist in the caller's org (422 otherwise).",
    )
    request: list[FhirReferenceInput] | None = Field(
        None,
        description="Why the specimen was collected — Reference(ServiceRequest). Stored as sent.",
    )
    collection: SpecimenCollectionInput | None = Field(
        None, description="Collection details."
    )
    processing: list[SpecimenProcessingInput] | None = Field(
        None, description="Processing and processing step details."
    )
    container: list[SpecimenContainerInput] | None = Field(
        None, description="Direct container of specimen (tube/slide, etc.)."
    )
    condition: list[FhirCodeableConceptInput] | None = Field(
        None, description="State of the specimen."
    )
    note: list[SpecimenAnnotationInput] | None = Field(None, description="Comments.")


class SpecimenCreateSchema(_SpecimenFields):
    """POST body — a FHIR R4 Specimen resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class SpecimenPatchSchema(_SpecimenFields):
    """PATCH body — a partial FHIR R4 Specimen (merge-patch semantics on top-level elements).
    Only supplied elements are written; omitted ones are left untouched. A supplied element
    replaces the stored value wholesale — a list (even `[]`) replaces every existing entry, an
    object such as `collection` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "unsatisfactory",
                "condition": [{"text": "Hemolyzed"}],
            }
        }
    }

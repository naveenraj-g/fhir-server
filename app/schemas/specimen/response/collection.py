from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRPeriod, FHIRReference
from app.schemas.questionnaire.response import FHIRQuantity

from .codeable_concept import PlainSpecimenCodeableConcept
from .reference import PlainSpecimenReference


class FHIRSpecimenCollection(BaseModel):
    """FHIR representation of Specimen.collection."""

    collector: FHIRReference | None = Field(None, description="Who collected the specimen.")
    collectedDateTime: str | None = Field(None, description="The time when specimen was collected.")
    collectedPeriod: FHIRPeriod | None = Field(None, description="The period of collection.")
    duration: FHIRQuantity | None = Field(None, description="The duration of collection.")
    quantity: FHIRQuantity | None = Field(None, description="The quantity of specimen collected.")
    method: FHIRCodeableConcept | None = Field(None, description="Technique used to perform collection.")
    bodySite: FHIRCodeableConcept | None = Field(None, description="Anatomical collection site.")
    fastingStatusCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Whether or how long patient abstained from food and/or drink."
    )
    fastingStatusDuration: FHIRQuantity | None = Field(
        None, description="How long patient abstained from food and/or drink."
    )


class PlainSpecimenCollection(BaseModel):
    """Plain response representation of Specimen.collection."""

    model_config = ConfigDict(extra="allow")

    collector: PlainSpecimenReference | None = Field(None, description="Who collected the specimen.")
    collected_date_time: str | None = Field(None, description="The time when specimen was collected.")
    collected_period_start: str | None = Field(None, description="Start of collection period.")
    collected_period_end: str | None = Field(None, description="End of collection period.")
    duration_value: float | None = Field(None, description="Duration value.")
    duration_comparator: str | None = Field(None, description="Duration comparator.")
    duration_unit: str | None = Field(None, description="Duration unit.")
    duration_system: str | None = Field(None, description="Duration system.")
    duration_code: str | None = Field(None, description="Duration code.")
    quantity_value: float | None = Field(None, description="Quantity value.")
    quantity_unit: str | None = Field(None, description="Quantity unit.")
    quantity_system: str | None = Field(None, description="Quantity system.")
    quantity_code: str | None = Field(None, description="Quantity code.")
    method: PlainSpecimenCodeableConcept | None = Field(None, description="Technique used to perform collection.")
    body_site: PlainSpecimenCodeableConcept | None = Field(None, description="Anatomical collection site.")
    fasting_status_codeable_concept: PlainSpecimenCodeableConcept | None = Field(
        None, description="Fasting status concept."
    )
    fasting_status_duration_value: float | None = Field(None, description="Fasting duration value.")
    fasting_status_duration_comparator: str | None = Field(None, description="Fasting duration comparator.")
    fasting_status_duration_unit: str | None = Field(None, description="Fasting duration unit.")
    fasting_status_duration_system: str | None = Field(None, description="Fasting duration system.")
    fasting_status_duration_code: str | None = Field(None, description="Fasting duration code.")

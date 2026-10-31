from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import SpecimenQuantityComparator

from .codeable_concept import SpecimenCodeableConceptInput
from .reference import SpecimenCollectorInput


class SpecimenCollectionInput(BaseModel):
    """Specimen.collection (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    collector: SpecimenCollectorInput | None = Field(
        None, description="Who collected the specimen (Reference(Practitioner | PractitionerRole))."
    )
    collected_date_time: datetime | None = Field(
        None, description="The time when specimen was collected."
    )
    collected_period_start: datetime | None = Field(
        None, description="Start of collection period."
    )
    collected_period_end: datetime | None = Field(
        None, description="End of collection period."
    )
    duration_value: float | None = Field(
        None, description="Numerical value of duration (Duration.value)."
    )
    duration_comparator: SpecimenQuantityComparator | None = Field(
        None, description="< | <= | >= | >"
    )
    duration_unit: str | None = Field(
        None, description="Unit representation of duration."
    )
    duration_system: str | None = Field(
        None, description="System that defines coded unit of duration."
    )
    duration_code: str | None = Field(
        None, description="Coded form of the unit of duration."
    )
    quantity_value: float | None = Field(
        None, description="The quantity of specimen collected."
    )
    quantity_unit: str | None = Field(
        None, description="Unit representation of quantity."
    )
    quantity_system: str | None = Field(
        None, description="System that defines coded unit of quantity."
    )
    quantity_code: str | None = Field(
        None, description="Coded form of the unit of quantity."
    )
    method: SpecimenCodeableConceptInput | None = Field(
        None, description="Technique used to perform collection."
    )
    body_site: SpecimenCodeableConceptInput | None = Field(
        None, description="Anatomical collection site."
    )
    fasting_status_codeable_concept: SpecimenCodeableConceptInput | None = Field(
        None, description="Whether or how long patient abstained from food and/or drink."
    )
    fasting_status_duration_value: float | None = Field(
        None, description="Numerical duration of fasting."
    )
    fasting_status_duration_comparator: SpecimenQuantityComparator | None = Field(
        None, description="< | <= | >= | >"
    )
    fasting_status_duration_unit: str | None = Field(
        None, description="Unit of fasting duration."
    )
    fasting_status_duration_system: str | None = Field(
        None, description="System for fasting duration unit."
    )
    fasting_status_duration_code: str | None = Field(
        None, description="Coded form of fasting duration unit."
    )

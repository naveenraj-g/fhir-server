from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.allergy_intolerance.response.codeable_concept import (
    PlainAllergyIntoleranceCodeableConcept,
)
from app.schemas.allergy_intolerance.response.identifier import (
    PlainAllergyIntoleranceIdentifier,
)
from app.schemas.allergy_intolerance.response.note import (
    PlainAllergyIntoleranceNote,
)
from app.schemas.allergy_intolerance.response.reaction import (
    FHIRAllergyIntoleranceReaction,
    PlainAllergyIntoleranceReaction,
)
from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)


class FHIRAllergyIntoleranceSchema(BaseModel):
    """FHIR R4 AllergyIntolerance resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["AllergyIntolerance"] = "AllergyIntolerance"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    clinicalStatus: FHIRCodeableConcept | None = None
    verificationStatus: FHIRCodeableConcept | None = None
    type: str | None = None
    category: list[str] | None = None
    criticality: str | None = None
    code: FHIRCodeableConcept | None = None
    patient: FHIRReference
    encounter: FHIRReference | None = None
    onsetDateTime: str | None = None
    onsetAge: dict[str, Any] | None = None
    onsetPeriod: FHIRPeriod | None = None
    onsetRange: dict[str, Any] | None = None
    onsetString: str | None = None
    recordedDate: str | None = None
    recorder: FHIRReference | None = None
    asserter: FHIRReference | None = None
    lastOccurrence: str | None = None
    note: list[dict[str, Any]] | None = None
    reaction: list[FHIRAllergyIntoleranceReaction] | None = None
    extension: list[dict[str, Any]] | None = None


class PlainAllergyIntoleranceResponse(BaseModel):
    """Plain snake_case response schema for AllergyIntolerance."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Public sequence AllergyIntolerance ID.")
    clinical_status: PlainAllergyIntoleranceCodeableConcept | None = Field(
        None, description="Clinical status of the allergy or intolerance."
    )
    verification_status: PlainAllergyIntoleranceCodeableConcept | None = Field(
        None, description="Verification status."
    )
    type: str | None = Field(
        None, description="allergy | intolerance."
    )
    category: list[str] | None = Field(
        None, description="food | medication | environment | biologic."
    )
    criticality: str | None = Field(
        None, description="low | high | unable-to-assess."
    )
    code: PlainAllergyIntoleranceCodeableConcept | None = Field(
        None, description="Code that identifies the allergy or intolerance."
    )
    patient: str = Field(..., description="Who the sensitivity is for.")
    patient_display: str | None = Field(
        None, description="Display text for patient."
    )
    patient_identifier_use: str | None = None
    patient_identifier_type_system: str | None = None
    patient_identifier_type_version: str | None = None
    patient_identifier_type_code: str | None = None
    patient_identifier_type_display: str | None = None
    patient_identifier_type_user_selected: bool | None = None
    patient_identifier_type_text: str | None = None
    patient_identifier_system: str | None = None
    patient_identifier_value: str | None = None
    patient_identifier_period_start: str | None = None
    patient_identifier_period_end: str | None = None

    encounter: str | None = Field(
        None, description="Encounter when allergy or intolerance was asserted."
    )
    encounter_display: str | None = Field(
        None, description="Display text for encounter."
    )
    encounter_identifier_use: str | None = None
    encounter_identifier_type_system: str | None = None
    encounter_identifier_type_version: str | None = None
    encounter_identifier_type_code: str | None = None
    encounter_identifier_type_display: str | None = None
    encounter_identifier_type_user_selected: bool | None = None
    encounter_identifier_type_text: str | None = None
    encounter_identifier_system: str | None = None
    encounter_identifier_value: str | None = None
    encounter_identifier_period_start: str | None = None
    encounter_identifier_period_end: str | None = None

    onset_date_time: datetime | None = Field(
        None, description="When allergy or intolerance was identified (dateTime)."
    )
    onset_age: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Age)."
    )
    onset_period_start: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period start)."
    )
    onset_period_end: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period end)."
    )
    onset_range: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Range)."
    )
    onset_string: str | None = Field(
        None, description="When allergy or intolerance was identified (string)."
    )
    recorded_date: datetime | None = Field(
        None, description="Date first version of the resource was recorded."
    )
    recorder: str | None = Field(
        None, description="Who recorded the sensitivity."
    )
    recorder_display: str | None = Field(
        None, description="Display text for recorder."
    )
    recorder_identifier_use: str | None = None
    recorder_identifier_type_system: str | None = None
    recorder_identifier_type_version: str | None = None
    recorder_identifier_type_code: str | None = None
    recorder_identifier_type_display: str | None = None
    recorder_identifier_type_user_selected: bool | None = None
    recorder_identifier_type_text: str | None = None
    recorder_identifier_system: str | None = None
    recorder_identifier_value: str | None = None
    recorder_identifier_period_start: str | None = None
    recorder_identifier_period_end: str | None = None

    asserter: str | None = Field(
        None, description="Source of the information about the allergy."
    )
    asserter_display: str | None = Field(
        None, description="Display text for asserter."
    )
    asserter_identifier_use: str | None = None
    asserter_identifier_type_system: str | None = None
    asserter_identifier_type_version: str | None = None
    asserter_identifier_type_code: str | None = None
    asserter_identifier_type_display: str | None = None
    asserter_identifier_type_user_selected: bool | None = None
    asserter_identifier_type_text: str | None = None
    asserter_identifier_system: str | None = None
    asserter_identifier_value: str | None = None
    asserter_identifier_period_start: str | None = None
    asserter_identifier_period_end: str | None = None

    last_occurrence: datetime | None = Field(
        None, description="Date(/time) of last known occurrence of a reaction."
    )
    note: list[PlainAllergyIntoleranceNote] | None = Field(
        None, description="Additional text not captured in other fields."
    )
    reaction: list[PlainAllergyIntoleranceReaction] | None = Field(
        None, description="Adverse Reaction Events linked to issue."
    )
    identifier: list[PlainAllergyIntoleranceIdentifier] | None = Field(
        None, description="External ids for this item."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Extensions."
    )
    created_at: datetime | None = Field(
        None, description="Timestamp of resource creation."
    )
    updated_at: datetime | None = Field(
        None, description="Timestamp of resource update."
    )


class PaginatedAllergyIntoleranceResponse(BaseModel):
    """Paginated response for plain AllergyIntolerance listing."""

    model_config = ConfigDict(extra="ignore")

    total: int
    limit: int
    offset: int
    data: list[PlainAllergyIntoleranceResponse]


class FHIRAllergyIntoleranceBundleEntry(BaseModel):
    """Single entry in FHIR AllergyIntolerance searchset bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRAllergyIntoleranceSchema


class FHIRAllergyIntoleranceBundle(BaseModel):
    """FHIR searchset Bundle for AllergyIntolerance resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRAllergyIntoleranceBundleEntry] = []

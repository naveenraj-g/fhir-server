from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRPeriod
from app.schemas.family_member_history.response.codeable_concept import (
    PlainFamilyMemberHistoryCodeableConcept,
)
from app.schemas.family_member_history.response.note import (
    PlainFamilyMemberHistoryNote,
)


class FHIRFamilyMemberHistoryCondition(BaseModel):
    """FHIR BackboneElement condition for FamilyMemberHistory."""

    model_config = ConfigDict(extra="allow")

    code: FHIRCodeableConcept
    outcome: FHIRCodeableConcept | None = None
    contributedToDeath: bool | None = None
    onsetAge: dict[str, Any] | None = None
    onsetRange: dict[str, Any] | None = None
    onsetPeriod: FHIRPeriod | None = None
    onsetString: str | None = None
    note: list[dict[str, Any]] | None = None


class PlainFamilyMemberHistoryCondition(BaseModel):
    """Plain snake_case shape for FamilyMemberHistory.condition."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal database ID.")
    code: PlainFamilyMemberHistoryCodeableConcept = Field(
        ..., description="Condition suffered by relation."
    )
    outcome: PlainFamilyMemberHistoryCodeableConcept | None = None
    contributed_to_death: bool | None = None

    onset_age_value: float | None = None
    onset_age_comparator: str | None = None
    onset_age_unit: str | None = None
    onset_age_system: str | None = None
    onset_age_code: str | None = None

    onset_range_low_value: float | None = None
    onset_range_low_unit: str | None = None
    onset_range_low_system: str | None = None
    onset_range_low_code: str | None = None
    onset_range_high_value: float | None = None
    onset_range_high_unit: str | None = None
    onset_range_high_system: str | None = None
    onset_range_high_code: str | None = None

    onset_period_start: datetime | None = None
    onset_period_end: datetime | None = None
    onset_string: str | None = None

    note: list[PlainFamilyMemberHistoryNote] | None = None

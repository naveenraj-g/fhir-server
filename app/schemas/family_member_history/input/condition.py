from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import FamilyMemberHistoryQuantityComparator
from app.schemas.family_member_history.input.codeable_concept import (
    FamilyMemberHistoryCodeableConceptInput,
)
from app.schemas.family_member_history.input.note import (
    FamilyMemberHistoryNoteInput,
)


class FamilyMemberHistoryConditionInput(BaseModel):
    """FamilyMemberHistory.condition (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    code: FamilyMemberHistoryCodeableConceptInput = Field(
        ..., description="Condition suffered by relation (e.g. SNOMED CT code)."
    )
    outcome: FamilyMemberHistoryCodeableConceptInput | None = Field(
        None, description="deceased | permanent disability | etc."
    )
    contributed_to_death: bool | None = Field(
        None, description="Whether the condition contributed to death."
    )

    # onset[x] (0..1 choice: Age | Range | Period | string)
    onset_age_value: float | None = Field(None, description="onset[x]: Age — numeric value.")
    onset_age_comparator: FamilyMemberHistoryQuantityComparator | None = Field(
        None, description="onset[x]: Age — < | <= | >= | >."
    )
    onset_age_unit: str | None = Field(None, description="onset[x]: Age — unit string.")
    onset_age_system: str | None = Field(None, description="onset[x]: Age — system URI.")
    onset_age_code: str | None = Field(None, description="onset[x]: Age — unit code.")

    onset_range_low_value: float | None = Field(None, description="onset[x]: Range — low value.")
    onset_range_low_unit: str | None = Field(None, description="onset[x]: Range — low unit.")
    onset_range_low_system: str | None = Field(None, description="onset[x]: Range — low system.")
    onset_range_low_code: str | None = Field(None, description="onset[x]: Range — low code.")
    onset_range_high_value: float | None = Field(None, description="onset[x]: Range — high value.")
    onset_range_high_unit: str | None = Field(None, description="onset[x]: Range — high unit.")
    onset_range_high_system: str | None = Field(None, description="onset[x]: Range — high system.")
    onset_range_high_code: str | None = Field(None, description="onset[x]: Range — high code.")

    onset_period_start: datetime | None = Field(None, description="onset[x]: Period — start.")
    onset_period_end: datetime | None = Field(None, description="onset[x]: Period — end.")
    onset_string: str | None = Field(None, description="onset[x]: string — free-text onset.")

    note: list[FamilyMemberHistoryNoteInput] | None = Field(
        None, description="Extra information about condition."
    )

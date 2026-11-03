from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput
from app.schemas.enums import MeasureReportQuantityComparator


class MeasureReportGroupStratifierStratumComponentInput(BaseModel):
    """MeasureReport.group.stratifier.stratum.component input."""

    model_config = ConfigDict(extra="forbid")

    code_text: str | None = Field(
        None, description="What stratifier component of the group."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coding for component code."
    )
    value_text: str | None = Field(
        None, description="The stratum component value."
    )
    value_coding: list[CodingInput] | None = Field(
        None, description="Coding for component value."
    )


class MeasureReportGroupStratifierStratumPopulationInput(BaseModel):
    """MeasureReport.group.stratifier.stratum.population input."""

    model_config = ConfigDict(extra="forbid")

    code_text: str | None = Field(
        None, description="Initial-population | numerator | denominator | etc."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coding for population code."
    )
    count: int | None = Field(
        None, description="Size of the stratum population."
    )
    subject_results: str | None = Field(
        None, description="Reference to List of subject results."
    )
    subject_results_display: str | None = Field(
        None, description="Display for subject results reference."
    )

    # Fallback identifier for subject_results
    subject_results_identifier_use: IdentifierUse | None = Field(None)
    subject_results_identifier_type_system: str | None = Field(None)
    subject_results_identifier_type_version: str | None = Field(None)
    subject_results_identifier_type_code: str | None = Field(None)
    subject_results_identifier_type_display: str | None = Field(None)
    subject_results_identifier_type_user_selected: bool | None = Field(None)
    subject_results_identifier_type_text: str | None = Field(None)
    subject_results_identifier_system: str | None = Field(None)
    subject_results_identifier_value: str | None = Field(None)
    subject_results_identifier_period_start: datetime | None = Field(None)
    subject_results_identifier_period_end: datetime | None = Field(None)


class MeasureReportGroupStratifierStratumInput(BaseModel):
    """MeasureReport.group.stratifier.stratum input."""

    model_config = ConfigDict(extra="forbid")

    value_text: str | None = Field(
        None, description="The stratum value, e.g. male."
    )
    value_coding: list[CodingInput] | None = Field(
        None, description="Coding for stratum value."
    )
    component: list[MeasureReportGroupStratifierStratumComponentInput] | None = Field(
        None, description="Stratifier component values."
    )
    population: list[MeasureReportGroupStratifierStratumPopulationInput] | None = (
        Field(None, description="Stratum populations.")
    )
    measure_score_value: float | None = Field(
        None, description="What score this stratum achieved."
    )
    measure_score_comparator: MeasureReportQuantityComparator | None = Field(
        None, description="< | <= | >= | >"
    )
    measure_score_unit: str | None = Field(
        None, description="Unit representation."
    )
    measure_score_system: str | None = Field(
        None, description="System that defines coded unit."
    )
    measure_score_code: str | None = Field(
        None, description="Coded form of the unit."
    )


class MeasureReportGroupStratifierCodeInput(BaseModel):
    """MeasureReport.group.stratifier.code input (0..* CodeableConcept)."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(
        None, description="What stratifier factor of the group."
    )
    coding: list[CodingInput] | None = Field(
        None, description="Coding for stratifier code."
    )


class MeasureReportGroupStratifierInput(BaseModel):
    """MeasureReport.group.stratifier input."""

    model_config = ConfigDict(extra="forbid")

    code: list[MeasureReportGroupStratifierCodeInput] | None = Field(
        None, description="What stratifier factor of the group (0..*)."
    )
    stratum: list[MeasureReportGroupStratifierStratumInput] | None = Field(
        None, description="Stratum results, one for each unique value."
    )


class MeasureReportGroupPopulationInput(BaseModel):
    """MeasureReport.group.population input."""

    model_config = ConfigDict(extra="forbid")

    code_text: str | None = Field(
        None, description="Initial-population | numerator | denominator | etc."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coding for population code."
    )
    count: int | None = Field(
        None, description="Size of the population."
    )
    subject_results: str | None = Field(
        None, description="Reference to List of subject results."
    )
    subject_results_display: str | None = Field(
        None, description="Display for subject results reference."
    )

    # Fallback identifier for subject_results
    subject_results_identifier_use: IdentifierUse | None = Field(None)
    subject_results_identifier_type_system: str | None = Field(None)
    subject_results_identifier_type_version: str | None = Field(None)
    subject_results_identifier_type_code: str | None = Field(None)
    subject_results_identifier_type_display: str | None = Field(None)
    subject_results_identifier_type_user_selected: bool | None = Field(None)
    subject_results_identifier_type_text: str | None = Field(None)
    subject_results_identifier_system: str | None = Field(None)
    subject_results_identifier_value: str | None = Field(None)
    subject_results_identifier_period_start: datetime | None = Field(None)
    subject_results_identifier_period_end: datetime | None = Field(None)


class MeasureReportGroupInput(BaseModel):
    """MeasureReport.group input."""

    model_config = ConfigDict(extra="forbid")

    code_text: str | None = Field(
        None, description="Meaning of the group."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coding for group code."
    )
    population: list[MeasureReportGroupPopulationInput] | None = Field(
        None, description="The populations in the group."
    )
    measure_score_value: float | None = Field(
        None, description="What score this group achieved."
    )
    measure_score_comparator: MeasureReportQuantityComparator | None = Field(
        None, description="< | <= | >= | >"
    )
    measure_score_unit: str | None = Field(
        None, description="Unit representation."
    )
    measure_score_system: str | None = Field(
        None, description="System that defines coded unit."
    )
    measure_score_code: str | None = Field(
        None, description="Coded form of the unit."
    )
    stratifier: list[MeasureReportGroupStratifierInput] | None = Field(
        None, description="Stratification results."
    )

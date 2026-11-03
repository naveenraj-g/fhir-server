from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput
from app.schemas.enums import (
    MeasureReportStatus,
    MeasureReportType,
)
from app.schemas.measure_report.input.group import MeasureReportGroupInput
from app.schemas.measure_report.input.identifier import MeasureReportIdentifierInput


class MeasureReportEvaluatedResourceInput(BaseModel):
    """MeasureReport.evaluatedResource (0..* Reference(Resource)) input."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="Literal reference, Relative, internal or absolute URL."
    )
    display: str | None = Field(
        None, description="Text alternative for the resource."
    )

    # Fallback identifier for evaluated resource
    reference_identifier_use: IdentifierUse | None = Field(None)
    reference_identifier_type_system: str | None = Field(None)
    reference_identifier_type_version: str | None = Field(None)
    reference_identifier_type_code: str | None = Field(None)
    reference_identifier_type_display: str | None = Field(None)
    reference_identifier_type_user_selected: bool | None = Field(None)
    reference_identifier_type_text: str | None = Field(None)
    reference_identifier_system: str | None = Field(None)
    reference_identifier_value: str | None = Field(None)
    reference_identifier_period_start: datetime | None = Field(None)
    reference_identifier_period_end: datetime | None = Field(None)


class MeasureReportCreateSchema(BaseModel):
    """Payload to create a new MeasureReport resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "complete",
                "type": "summary",
                "measure": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
                "date": "2026-11-03T11:00:00Z",
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-01-31T23:59:59Z",
                "group": [
                    {
                        "population": [
                            {
                                "code_text": "Initial Population",
                                "count": 100,
                            },
                            {
                                "code_text": "Numerator",
                                "count": 80,
                            },
                            {
                                "code_text": "Denominator",
                                "count": 100,
                            },
                        ],
                        "measure_score_value": 0.8,
                    }
                ],
            }
        },
    )

    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information."
    )
    identifier: list[MeasureReportIdentifierInput] | None = Field(
        None, description="Additional identifier for the MeasureReport."
    )
    status: MeasureReportStatus = Field(
        ..., description="complete | pending | error."
    )
    type: MeasureReportType = Field(
        ..., description="individual | subject-list | summary | data-collection."
    )
    measure: str = Field(
        ..., description="What measure was calculated (canonical URL)."
    )
    subject: str | None = Field(
        None, description="What individual(s) the report is for (e.g. Patient/10001)."
    )
    subject_display: str | None = Field(
        None, description="Display text for subject."
    )

    # Fallback identifier for subject
    subject_identifier_use: IdentifierUse | None = Field(None)
    subject_identifier_type_system: str | None = Field(None)
    subject_identifier_type_version: str | None = Field(None)
    subject_identifier_type_code: str | None = Field(None)
    subject_identifier_type_display: str | None = Field(None)
    subject_identifier_type_user_selected: bool | None = Field(None)
    subject_identifier_type_text: str | None = Field(None)
    subject_identifier_system: str | None = Field(None)
    subject_identifier_value: str | None = Field(None)
    subject_identifier_period_start: datetime | None = Field(None)
    subject_identifier_period_end: datetime | None = Field(None)

    date: datetime | None = Field(
        None, description="When the report was generated."
    )
    reporter: str | None = Field(
        None, description="Who is reporting the data (e.g. Practitioner/30001)."
    )
    reporter_display: str | None = Field(
        None, description="Display text for reporter."
    )

    # Fallback identifier for reporter
    reporter_identifier_use: IdentifierUse | None = Field(None)
    reporter_identifier_type_system: str | None = Field(None)
    reporter_identifier_type_version: str | None = Field(None)
    reporter_identifier_type_code: str | None = Field(None)
    reporter_identifier_type_display: str | None = Field(None)
    reporter_identifier_type_user_selected: bool | None = Field(None)
    reporter_identifier_type_text: str | None = Field(None)
    reporter_identifier_system: str | None = Field(None)
    reporter_identifier_value: str | None = Field(None)
    reporter_identifier_period_start: datetime | None = Field(None)
    reporter_identifier_period_end: datetime | None = Field(None)

    period_start: datetime | None = Field(
        None, description="What period the report covers (start)."
    )
    period_end: datetime | None = Field(
        None, description="What period the report covers (end)."
    )

    improvement_notation_text: str | None = Field(
        None, description="Increased or decreased score indicates improvement."
    )
    improvement_notation_coding: list[CodingInput] | None = Field(
        None, description="Coding for improvement notation."
    )

    evaluated_resource: list[MeasureReportEvaluatedResourceInput] | None = Field(
        None, description="What data was used to calculate the measure score."
    )
    group: list[MeasureReportGroupInput] | None = Field(
        None, description="Measure results for each group."
    )


class MeasureReportPatchSchema(BaseModel):
    """Payload to partially update a MeasureReport resource."""

    model_config = ConfigDict(extra="forbid")

    extension: list[dict[str, Any]] | None = None
    identifier: list[MeasureReportIdentifierInput] | None = None
    status: MeasureReportStatus | None = None
    type: MeasureReportType | None = None
    measure: str | None = None
    subject: str | None = None
    subject_display: str | None = None

    subject_identifier_use: IdentifierUse | None = None
    subject_identifier_type_system: str | None = None
    subject_identifier_type_version: str | None = None
    subject_identifier_type_code: str | None = None
    subject_identifier_type_display: str | None = None
    subject_identifier_type_user_selected: bool | None = None
    subject_identifier_type_text: str | None = None
    subject_identifier_system: str | None = None
    subject_identifier_value: str | None = None
    subject_identifier_period_start: datetime | None = None
    subject_identifier_period_end: datetime | None = None

    date: datetime | None = None
    reporter: str | None = None
    reporter_display: str | None = None

    reporter_identifier_use: IdentifierUse | None = None
    reporter_identifier_type_system: str | None = None
    reporter_identifier_type_version: str | None = None
    reporter_identifier_type_code: str | None = None
    reporter_identifier_type_display: str | None = None
    reporter_identifier_type_user_selected: bool | None = None
    reporter_identifier_type_text: str | None = None
    reporter_identifier_system: str | None = None
    reporter_identifier_value: str | None = None
    reporter_identifier_period_start: datetime | None = None
    reporter_identifier_period_end: datetime | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    improvement_notation_text: str | None = None
    improvement_notation_coding: list[CodingInput] | None = None

    evaluated_resource: list[MeasureReportEvaluatedResourceInput] | None = None
    group: list[MeasureReportGroupInput] | None = None

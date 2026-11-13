from datetime import datetime

from pydantic import Field

from app.schemas.fhir_input.base import FhirInputModel


class FhirPeriodInput(FhirInputModel):
    """FHIR R4 Period. Typed as `datetime` because every Period this project
    stores lands in a `DateTime(timezone=True)` column. A timezone-naive
    value passes Pydantic but is still rejected by base R4 validation (FHIR's
    dateTime requires an offset whenever a time is present)."""

    start: datetime | None = Field(
        None, description="Starting time with inclusive boundary (ISO 8601, with timezone offset)."
    )
    end: datetime | None = Field(
        None, description="End time with inclusive boundary, if not ongoing (ISO 8601, with timezone offset)."
    )

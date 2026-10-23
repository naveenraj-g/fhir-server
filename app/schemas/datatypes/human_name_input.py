from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import HumanNameUse


class HumanNameInput(BaseModel):
    """One HumanName entry (e.g. `name[]`) — reused wherever a resource
    embeds a dedicated HumanName child table (Practitioner.name)."""

    model_config = ConfigDict(extra="forbid")
    use: Optional[HumanNameUse] = Field(
        None,
        description="Identifies the purpose of this name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    text: Optional[str] = Field(
        None, description="Text representation of the full name, as it would normally be displayed."
    )
    family: Optional[str] = Field(None, description="Family name (often called 'surname').")
    given: Optional[List[str]] = Field(
        None, description="Given names (not always 'first'). Includes middle names — order matters."
    )
    prefix: Optional[List[str]] = Field(
        None, description="Parts that come before the name (e.g. Mr., Dr., titles)."
    )
    suffix: Optional[List[str]] = Field(
        None, description="Parts that come after the name (e.g. Jr., MD, qualifications)."
    )
    period_start: Optional[datetime] = Field(
        None, description="Start of the period during which this name was/is in use."
    )
    period_end: Optional[datetime] = Field(
        None, description="End of the period during which this name was/is in use."
    )

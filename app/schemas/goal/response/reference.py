from datetime import datetime

from pydantic import ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import AuditFields


class PlainGoalReference(AuditFields):
    """Plain snake_case serialization of a Goal reference child row (addresses, outcomeReference)."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this reference row.")
    reference_reference: str | None = Field(None, description="Raw literal reference string.")
    reference: str | None = Field(None, description="Computed reference string (e.g. 'Condition/120001').")
    reference_type: str | None = Field(None, description="Target resource type.")
    reference_id: int | None = Field(None, description="Target public ID.")
    reference_display: str | None = Field(None, description="Narrative display.")
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of this identifier."
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the identifier type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the identifier type."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for identifier type."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for identifier type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None, description="If this identifier type coding was chosen directly by the user."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Plain text representation of the identifier type."
    )
    reference_identifier_system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    reference_identifier_value: str | None = Field(
        None, description="The portion of the identifier typically relevant to the user."
    )
    reference_identifier_period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use - start."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use - end."
    )

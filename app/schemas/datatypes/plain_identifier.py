from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.plain_identifier_type import PlainIdentifierType


class PlainIdentifier(BaseModel):
    """Plain-JSON Identifier — a business identifier, unique within some defined namespace."""

    use: Optional[str] = Field(
        None, description="The purpose of this identifier. usual|official|temp|secondary|old."
    )
    system: Optional[str] = Field(
        None, description="The namespace (a URI) that identifies the scope this identifier's value is unique within."
    )
    value: Optional[str] = Field(None, description="The identifier value itself, unique within the given system.")
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    assigner: Optional[str] = Field(None, description="Display name of the organization that issued this identifier.")
    type: Optional[PlainIdentifierType] = Field(None, description="A coded description of the type of identifier.")

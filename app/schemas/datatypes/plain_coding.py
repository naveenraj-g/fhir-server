from typing import Optional
from pydantic import BaseModel, Field


class PlainCoding(BaseModel):
    """Plain-JSON Coding — a reference to a code defined by a terminology system."""

    system: Optional[str] = Field(None, description="Identity of the terminology system that defines this code.")
    version: Optional[str] = Field(
        None, description="Version of the terminology system in which this code was defined."
    )
    code: Optional[str] = Field(None, description="Symbol in the syntax defined by the terminology system.")
    display: Optional[str] = Field(
        None, description="Representation defined by the terminology system for this code."
    )
    user_selected: Optional[bool] = Field(
        None, description="Whether this coding was chosen directly by the user (vs. derived by the system)."
    )

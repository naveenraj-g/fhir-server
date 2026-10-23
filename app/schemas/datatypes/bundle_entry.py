from typing import Any
from pydantic import BaseModel, Field


class FHIRBundleEntry(BaseModel):
    """FHIR R4 Bundle.entry — a single resource entry within a Bundle."""

    resource: Any = Field(..., description="The resource contained in this bundle entry.")

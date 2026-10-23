from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.bundle_entry import FHIRBundleEntry


class FHIRBundle(BaseModel):
    """FHIR R4 Bundle — a container for a collection of resources, here always a 'searchset'."""

    resourceType: str = Field("Bundle", description="Always 'Bundle'.")
    type: str = Field("searchset", description="The purpose of this bundle. Always 'searchset' in this API.")
    total: int = Field(..., description="Total number of resources matching the search, across all pages.")
    entry: Optional[List[FHIRBundleEntry]] = Field(
        None, description="Resources matching the search, one per entry, for the current page."
    )

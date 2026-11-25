from pydantic import BaseModel, Field

from app.schemas.common.bundle_entry import FHIRBundleEntry


class FHIRBundle(BaseModel):
    """FHIR R4 Bundle — a container for a collection of resources, here always a 'searchset'."""

    resourceType: str = Field("Bundle", description="Always 'Bundle'.")
    type: str = Field(
        "searchset",
        description="The purpose of this bundle. Always 'searchset' in this API.",
    )
    total: int = Field(
        ...,
        description="Total number of resources matching the search, across all pages.",
    )
    entry: list[FHIRBundleEntry] | None = Field(
        None,
        description="Resources matching the search, one per entry, for the current page.",
    )

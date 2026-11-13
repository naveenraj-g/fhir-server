"""Pieces of a FHIR R4 searchset Bundle shared by every resource on the
search engine (app.fhir.search) — each resource's own `FHIR<X>Bundle`
combines these with its typed resource entry."""

from pydantic import BaseModel, Field


class FHIRBundleLink(BaseModel):
    relation: str = Field(
        ..., description="self (the search as applied), first, previous, next or last."
    )
    url: str = Field(..., description="URL of that page of results.")


class FHIRBundleEntrySearch(BaseModel):
    mode: str = Field(
        ...,
        description="match (matched the search), include (added by _include/_revinclude) or outcome (an OperationOutcome about the search, e.g. ignored parameters).",
    )
    extension: list[dict] | None = Field(
        None,
        description="Search-specific extensions, e.g. Location `near`'s http://hl7.org/fhir/StructureDefinition/location-distance.",
    )

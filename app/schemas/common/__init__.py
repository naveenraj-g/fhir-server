"""Search-result wrapper types shared by every resource's response schema (the searchset Bundle,
its entries and links). The FHIR datatypes themselves live in `app.schemas.fhir_datatypes`."""

from app.schemas.common.bundle import FHIRBundle
from app.schemas.common.bundle_entry import FHIRBundleEntry
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink

__all__ = ["FHIRBundle", "FHIRBundleEntry", "FHIRBundleEntrySearch", "FHIRBundleLink"]

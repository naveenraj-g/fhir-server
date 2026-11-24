"""
FHIR ObservationDefinition document -> search index. The only write-side mapper.

R4 defines no search parameter for ObservationDefinition (see ObservationDefinitionModel's
docstring), so there is nothing to derive from the document: no column and no child row. The
hooks stay, with the same signatures as every other resource's indexer, so that create and patch
share one path with the rest and a future search parameter has one place to be added.
"""

from __future__ import annotations


def index_columns(document: dict) -> dict:
    """Search columns on the observation_definition row itself (none)."""
    return {}


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by relationship name (none)."""
    return {}

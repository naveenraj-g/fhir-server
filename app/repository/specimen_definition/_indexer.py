"""
FHIR SpecimenDefinition document -> search index. The only write-side mapper.

SpecimenDefinition's whole resource is stored verbatim in SpecimenDefinitionModel.content; this
module derives every *other* row from it - exactly the values the FHIR R4 SpecimenDefinition
search parameters filter on (https://www.hl7.org/fhir/R4/specimendefinition.html#search),
nothing more. See SpecimenDefinitionModel's docstring for the parameter -> storage table; the
shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.specimen_definition import (
    SpecimenDefinitionIdentifier,
    SpecimenDefinitionToken,
)
from app.repository._content_index import identifier_rows, type_rows


def index_columns(document: dict) -> dict:
    """Search columns on the specimen_definition row itself (none: every parameter is a token
    held in a child table)."""
    return {}


def _token_rows(document: dict) -> list:
    rows: list = []
    type_collected = document.get("typeCollected")
    if isinstance(type_collected, dict):
        rows += type_rows(
            partial(SpecimenDefinitionToken, param="type"), type_collected
        )
    # container.type of every typeTested entry
    model = partial(SpecimenDefinitionToken, param="container")
    for tested in document.get("typeTested") or []:
        container = tested.get("container") if isinstance(tested, dict) else None
        concept = container.get("type") if isinstance(container, dict) else None
        if isinstance(concept, dict):
            rows += type_rows(model, concept)
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by SpecimenDefinitionModel relationship name."""
    identifier = document.get("identifier")
    return {
        "identifiers": (
            identifier_rows(SpecimenDefinitionIdentifier, identifier)
            if isinstance(identifier, dict)
            else []
        ),
        "tokens": _token_rows(document),
    }

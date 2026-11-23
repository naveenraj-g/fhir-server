from enum import Enum


class DocumentReferenceStatus(str, Enum):
    """DocumentReference.status (document-reference-status, required) - stored by value, so the
    real FHIR code `entered-in-error` is what the database holds."""

    current = "current"
    superseded = "superseded"
    entered_in_error = "entered-in-error"


class DocumentRelationshipType(str, Enum):
    """DocumentReference.relatesTo.code (document-relationship-type, required) - the `relation`
    search parameter."""

    replaces = "replaces"
    transforms = "transforms"
    signs = "signs"
    appends = "appends"

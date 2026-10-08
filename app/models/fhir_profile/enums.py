from enum import Enum


class FhirProfileScopeLevel(str, Enum):
    """Which layer of the base -> country -> organization profile chain a
    row represents — see docs/structure-definitions/12-three-layer-validation-architecture.md.
    Permanently fixed by this project's own design, not a FHIR terminology
    binding — a real Postgres Enum is the right call here the same way
    CLAUDE.md's "Category A" (required-binding, spec-fixed value sets)
    applies to FHIR's own enums. Member names are lowercase, matching their
    values exactly — this project's own established convention (see
    IdentifierUse in app/models/enums.py) for keeping the Postgres enum's
    stored labels equal to the Python value, not the member name."""

    base = "base"
    country = "country"
    organization = "organization"


class FhirProfileStatus(str, Enum):
    """Mirrors the real StructureDefinition.status value inside this row's
    own `structure_definition` JSON (see
    docs/structure-definitions/02-structuredefinition-root-fields.md) — kept
    here too, redundantly but synced at write time, so the app can filter by
    status without parsing JSONB. Deliberately the same four values FHIR
    itself defines for StructureDefinition.status, not a project-invented
    set."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"

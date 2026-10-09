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
    """This app's own "is this the profile layer currently enforced for
    its scope" flag — NOT a mirror of the StructureDefinition's own
    "status" field inside `structure_definition` (that's a different,
    HL7-defined concept: the resource's publication maturity, which can
    legitimately say "draft" for a profile that's fully live here, e.g.
    HL7's own real R4 Organization entry, or country_in.json before this
    was wired up). Reuses the same four FHIR status names only because
    they're a convenient, already-defined vocabulary for "not live yet /
    live / superseded / unknown", not because this column tracks what
    those names mean in the spec.

    Base rows: no draft -> active -> retired lifecycle at all — exactly
    one row per resource_type, seeded directly as 'active' (see
    seed_base_profiles.py), never created or activated through
    FhirProfileService.

    Country/organization rows: a real lifecycle —
    FhirProfileService.create_profile() always inserts 'draft';
    activate_profile() is the only path to 'active', and atomically
    retires whatever was active before it for the same scope. Seeded
    country rows (seed_country_profiles.py) are the one exception — they
    go in directly as 'active', since seeding is this app's own ground
    truth, not a draft awaiting admin action."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus


class CreatableProfileScopeLevel(str, Enum):
    """scope_level values valid for FhirProfileCreateSchema — deliberately
    narrower than app.models.fhir_profile.enums.FhirProfileScopeLevel,
    which also has 'base'. Base profiles are seeded from the HL7 bundle
    (see scripts/profiling/seed_base_profiles.py), never created through
    this endpoint — FhirProfileService.create_profile() already rejects
    'base' with a 422 at runtime, but narrowing the type here means a bad
    value (a typo, or 'base' itself) gets a clean Pydantic validation
    error before the request reaches the service at all, not a
    BusinessRuleViolationError from a runtime check. The service's own
    check stays as defense-in-depth for any caller that doesn't go through
    this schema."""

    country = "country"
    organization = "organization"


class FhirProfileCreateSchema(BaseModel):
    """Create a country or organization profile — never base, which is
    seeded once from the HL7 bundle (see scripts/profiling/seed_base_profiles.py)
    and has no write path here.

    `scope_id` means different things per scope_level, and is validated
    accordingly (see `_scope_id_matches_scope_level` below):
      - scope_level='country': a client-supplied country code (e.g. 'IN') —
        required, since there's no JWT claim a country code could come from.
      - scope_level='organization': must be OMITTED here entirely — the
        router derives it from the verified JWT's activeOrganizationId
        claim (actor.org_id) instead, same as every org-scoped resource in
        this codebase (see CLAUDE.md's Multi-Tenancy & Ownership). A caller
        can only ever create an organization-scope profile for their OWN
        org, never one named in the request body.

    The service resolves this profile's parent itself (country -> base;
    organization -> the active country profile for this deployment's
    configured country if one exists for this resource_type, else base —
    re-checked fresh on every write, not assumed from a prior one) and
    overwrites whatever `structure_definition['baseDefinition']` the caller
    sent to match — the chain is enforced server-side, not trusted from
    the request.

    `structure_definition['url']` is handled the same way for
    scope_level='organization': always auto-derived (from `scope_id` +
    `resource_type`, the same convention app.fhir.validation.dispatch
    falls back to) and unconditionally overwritten, never trusted from the
    request — a client-supplied value could drift from the real identity
    this profile is scoped to, or collide with another org's profile.
    scope_level='country' keeps `url` client-supplied, since a country
    profile may need to match a real externally-published canonical URL
    someday.

    `structure_definition['id']` (the base FHIR Resource.id, distinct from
    `url` — nothing in this pipeline reads or relies on it) is ALWAYS
    server-generated as a fresh UUID4, for every scope_level — a
    client-supplied value is silently overwritten, never required.

    `created_by` is NOT a field here — same as every other currently-built
    resource (see CLAUDE.md's Multi-Tenancy & Ownership), it comes from the
    verified JWT's `sub` at the router layer, not the request body."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "resource_type": "Organization",
                "scope_level": "organization",
                "structure_definition": {
                    "resourceType": "StructureDefinition",
                    "name": "OrgAbc123Organization",
                    "status": "draft",
                    "kind": "resource",
                    "abstract": False,
                    "type": "Organization",
                    "differential": {"element": []},
                },
            }
        },
    )

    resource_type: str
    scope_level: CreatableProfileScopeLevel
    scope_id: str | None = Field(
        None,
        description=(
            "A country code (e.g. 'IN') — required for scope_level='country'. "
            "Must be omitted for scope_level='organization': the org_id is "
            "derived from the verified JWT (activeOrganizationId) instead, "
            "never from this field."
        ),
    )
    structure_definition: dict

    @model_validator(mode="after")
    def _scope_id_matches_scope_level(self) -> "FhirProfileCreateSchema":
        if self.scope_level == CreatableProfileScopeLevel.organization:
            if self.scope_id is not None:
                raise ValueError(
                    "scope_id must be omitted for scope_level='organization' — "
                    "the org_id is derived from the verified JWT, not the request body."
                )
        elif self.scope_level == CreatableProfileScopeLevel.country:
            if not self.scope_id:
                raise ValueError(
                    "scope_id (a country code) is required for scope_level='country'."
                )
        return self


class FhirProfilePatchSchema(BaseModel):
    """Replaces a draft profile's structure_definition wholesale — only
    valid while status='draft'; an active or retired row is immutable
    history (create a new version via FhirProfileCreateSchema instead).

    `updated_by` is NOT a field here — comes from the verified JWT's `sub`
    at the router layer, same as every other currently-built resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "structure_definition": {
                    "resourceType": "StructureDefinition",
                    "differential": {"element": []},
                },
            }
        },
    )

    structure_definition: dict


class FhirProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_type: str
    scope_level: FhirProfileScopeLevel
    scope_id: str | None = None
    parent_profile_id: int | None = None
    canonical_url: str
    version: str
    status: FhirProfileStatus
    structure_definition: dict
    created_by: str
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class FhirProfileListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[FhirProfileResponse]

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus


class CreatableProfileScopeLevel(str, Enum):
    """The only scope_level value valid for FhirProfileCreateSchema —
    deliberately narrower than app.models.fhir_profile.enums.FhirProfileScopeLevel,
    which also has 'base' and 'country'.

    'base' is seeded once from the HL7 bundle (see scripts/profiling/
    seed_base_profiles.py), never created through this endpoint.

    'country' is EXCLUDED here too (this endpoint used to allow it) —
    a country profile is a deployment-wide, rarely-changing decision with
    its own dedicated write path (scripts/profiling/seed_country_profiles.py,
    reading scripts/data/profiling/resources/<type>/country_<code>.json
    straight into the DB as 'active', bypassing this schema/service
    entirely), and app.fhir.validation.dispatch.register_configured_country_profiles()
    now eagerly loads + registers every active country profile with the
    Java validator sidecar once, at application startup. Exposing live
    create/update of a country profile through this HTTP endpoint would
    let it drift out of step with that startup-time registration — an
    edit here wouldn't be picked up by the sidecar until the next
    restart, and this endpoint has no code to re-run the startup preload
    on demand. Re-seed via the script above (then restart the process) to
    change a country profile instead.

    FhirProfileService.create_profile() rejects both 'base' and 'country'
    with a 422 at runtime as defense-in-depth for any caller that doesn't
    go through this schema — narrowing the type here just means a bad
    value (a typo, or either excluded value) gets a clean Pydantic
    validation error before the request reaches the service at all."""

    organization = "organization"


class FhirProfileCreateSchema(BaseModel):
    """Create an organization profile — never base or country, neither of
    which have a write path here (see CreatableProfileScopeLevel's own
    docstring for why country was removed from this endpoint too).

    `scope_id` must be OMITTED here entirely — the router derives it from
    the verified JWT's activeOrganizationId claim (actor.org_id) instead,
    same as every org-scoped resource in this codebase (see CLAUDE.md's
    Multi-Tenancy & Ownership). A caller can only ever create an
    organization-scope profile for their OWN org, never one named in the
    request body.

    The service resolves this profile's parent itself (the active country
    profile for this deployment's configured country if one exists for
    this resource_type, else base — re-checked fresh on every write, not
    assumed from a prior one) and overwrites whatever
    `structure_definition['baseDefinition']` the caller sent to match —
    the chain is enforced server-side, not trusted from the request.

    `structure_definition['url']` is always auto-derived (from `scope_id`
    + `resource_type`, the same convention app.fhir.validation.dispatch
    falls back to) and unconditionally overwritten, never trusted from the
    request — a client-supplied value could drift from the real identity
    this profile is scoped to, or collide with another org's profile.

    `structure_definition['id']` (the base FHIR Resource.id, distinct from
    `url` — nothing in this pipeline reads or relies on it) is ALWAYS
    server-generated as a fresh UUID4 — a client-supplied value is
    silently overwritten, never required.

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
            "Must be omitted — the org_id is derived from the verified JWT "
            "(activeOrganizationId) instead, never from this field."
        ),
    )
    structure_definition: dict

    @model_validator(mode="after")
    def _scope_id_must_be_omitted(self) -> "FhirProfileCreateSchema":
        if self.scope_id is not None:
            raise ValueError(
                "scope_id must be omitted — this endpoint only creates "
                "organization-scope profiles, and the org_id is derived from "
                "the verified JWT, not the request body."
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

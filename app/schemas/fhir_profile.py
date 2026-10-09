from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus


class CreatableProfileScopeLevel(str, Enum):
    """scope_level values valid for FhirProfileCreateSchema — deliberately
    narrower than app.models.fhir_profile.enums.FhirProfileScopeLevel,
    which also has 'base'. Base profiles are seeded from the HL7 bundle
    (see app/fhir_profile/seed_base_profiles.py), never created through
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
    seeded once from the HL7 bundle (see app/fhir_profile/seed_base_profiles.py)
    and has no write path here. `scope_id` is the country code for
    scope_level='country' or the org's public org_id for
    scope_level='organization'; required for both.

    The service resolves this profile's parent itself (country -> base;
    organization -> the active country profile for this deployment's
    configured country if one exists, else base) and overwrites whatever
    `structure_definition['baseDefinition']` the caller sent to match —
    the chain is enforced server-side, not trusted from the request."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "resource_type": "Organization",
                "scope_level": "organization",
                "scope_id": "org_abc123",
                "structure_definition": {
                    "resourceType": "StructureDefinition",
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/org-org_abc123-organization",
                    "name": "OrgAbc123Organization",
                    "status": "draft",
                    "kind": "resource",
                    "abstract": False,
                    "type": "Organization",
                    "differential": {"element": []},
                },
                "created_by": "user_42",
            }
        },
    )

    resource_type: str
    scope_level: CreatableProfileScopeLevel
    scope_id: str
    structure_definition: dict
    created_by: str


class FhirProfilePatchSchema(BaseModel):
    """Replaces a draft profile's structure_definition wholesale — only
    valid while status='draft'; an active or retired row is immutable
    history (create a new version via FhirProfileCreateSchema instead)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "structure_definition": {
                    "resourceType": "StructureDefinition",
                    "differential": {"element": []},
                },
                "updated_by": "user_42",
            }
        },
    )

    structure_definition: dict
    updated_by: str


class FhirProfileActivateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"example": {"updated_by": "user_42"}}
    )

    updated_by: str


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

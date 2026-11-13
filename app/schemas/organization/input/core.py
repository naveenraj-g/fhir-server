from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

from .contact import OrganizationContactInput

_EXAMPLE = {
    "resourceType": "Organization",
    "active": True,
    "name": "General Hospital",
    "partOf": {"reference": "Organization/190001", "display": "Parent Health System"},
    "identifier": [
        {
            "use": "official",
            "system": "https://fhir-server.dev/fhir/identifier-system/facility-id",
            "value": "12345",
            "assigner": {
                "reference": "Organization/190001",
                "display": "State Health Department",
            },
        }
    ],
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider",
                }
            ]
        }
    ],
    "alias": ["Gen Hosp"],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "address": [
        {
            "use": "work",
            "type": "both",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA",
            "postalCode": "12345",
            "country": "US",
        }
    ],
    "contact": [
        {
            "purpose": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
                        "code": "ADMIN",
                    }
                ]
            },
            "name": {"family": "Smith", "given": ["John"]},
            "telecom": [{"system": "phone", "value": "555-0001"}],
            "address": {"type": "both", "city": "Anytown", "state": "CA", "country": "US"},
        }
    ],
    "endpoint": [
        {
            "display": "EHR FHIR Gateway",
            "identifier": {
                "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
                "value": "EP-1",
            },
        }
    ],
}


class _OrganizationFields(FhirInputModel):
    """Every writable Organization element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/organization.html). Create and patch accept
    exactly the same fields — Organization has no element that is required
    at this layer (org-1, "SHALL at least have a name or an identifier", is
    enforced by base R4 validation, not here).

    The validated body is stored whole (OrganizationModel.content), so any
    valid R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    organization_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. Like other tenant-level
    resources (unlike Patient/Practitioner) there is no user_id."""

    resourceType: Literal["Organization"] | None = Field(
        None,
        description="Optional; if supplied it must be 'Organization'.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None,
        description="Identifies this organization across multiple systems.",
    )
    active: bool | None = Field(
        None, description="Whether the organization's record is still in active use."
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Kind of organization (e.g. prov, dept, team, govt, ins)."
    )
    name: str | None = Field(
        None, description="Name used for the organization."
    )
    alias: list[str] | None = Field(
        None,
        description="A list of alternate names that the organization is known as, or was known as in the past.",
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None, description="A contact detail for the organization."
    )
    address: list[FhirAddressInput] | None = Field(
        None, description="An address for the organization."
    )
    partOf: FhirReferenceInput | None = Field(
        None,
        description="The organization of which this organization forms a part — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    contact: list[OrganizationContactInput] | None = Field(
        None, description="Contact for the organization for a certain purpose."
    )
    endpoint: list[FhirReferenceInput] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the organization — Reference(Endpoint).",
    )


class OrganizationCreateSchema(_OrganizationFields):
    """POST body — a FHIR R4 Organization resource. Creates the
    organization and every supplied nested element atomically in one
    transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class OrganizationPatchSchema(_OrganizationFields):
    """PATCH body — a partial FHIR R4 Organization (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones
    are left untouched. A supplied element replaces the stored value
    wholesale — a list (even `[]`) replaces every existing entry, an object
    such as `partOf` replaces the whole Reference, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "General Hospital Health System",
                "alias": ["Gen Hosp", "GHHS"],
                "telecom": [{"system": "phone", "value": "555-9999", "use": "work"}],
            }
        }
    }

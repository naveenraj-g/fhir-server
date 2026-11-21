from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirCodingInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

EndpointStatusCode = Literal[
    "active", "suspended", "error", "off", "entered-in-error", "test"
]

_EXAMPLE = {
    "resourceType": "Endpoint",
    "status": "active",
    "name": "General Hospital FHIR API",
    "managingOrganization": {
        "reference": "Organization/190001",
        "display": "General Hospital",
    },
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
            "value": "EP-1",
        }
    ],
    "connectionType": {
        "system": "http://terminology.hl7.org/CodeSystem/endpoint-connection-type",
        "code": "hl7-fhir-rest",
    },
    "payloadType": [{"coding": [{"code": "any", "display": "Any"}]}],
    "payloadMimeType": ["application/fhir+json"],
    "address": "https://fhir.generalhospital.example/r4",
    "header": ["Authorization: Bearer <token>"],
    "contact": [{"system": "email", "value": "it@generalhospital.example"}],
    "period": {"start": "2026-01-01T00:00:00Z"},
}


class _EndpointFields(FhirInputModel):
    """Every writable Endpoint element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/endpoint.html). Create and patch accept
    exactly the same fields. R4 requires `status`, `connectionType`,
    `payloadType` and `address`; that is enforced by base R4 validation of the
    stored document (the `java_validator` backend — the native structural
    check has no cardinality minimums), not by this model. A PATCH may omit
    them: it is merged onto the current resource before validating.

    The validated body is stored whole (EndpointModel.content), so any valid
    R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    endpoint_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Endpoint"] | None = Field(
        None, description="Optional; if supplied it must be 'Endpoint'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Identifies this endpoint across multiple systems."
    )
    status: EndpointStatusCode | None = Field(
        None,
        description="active | suspended | error | off | entered-in-error | test (required by R4).",
    )
    connectionType: FhirCodingInput | None = Field(
        None,
        description="Protocol/Profile/Standard to be used with this endpoint connection (required by R4; extensible binding).",
    )
    name: str | None = Field(
        None, description="A name that this endpoint can be identified by."
    )
    managingOrganization: FhirReferenceInput | None = Field(
        None,
        description="Organization that manages this endpoint — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    contact: list[FhirContactPointInput] | None = Field(
        None, description="Contact details for source (e.g. troubleshooting)."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Interval the endpoint is expected to be operational."
    )
    payloadType: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="The type of content that may be used at this endpoint (required by R4).",
    )
    payloadMimeType: list[str] | None = Field(
        None,
        description="Mimetype to send. If not specified, the content could be anything (including no payload, if the connectionType defined this).",
    )
    address: str | None = Field(
        None,
        description="The technical base address for connecting to this endpoint (a URL; required by R4).",
    )
    header: list[str] | None = Field(
        None, description="Usage depends on the channel type (e.g. HTTP headers)."
    )


class EndpointCreateSchema(_EndpointFields):
    """POST body — a FHIR R4 Endpoint resource. Creates the endpoint and
    every supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class EndpointPatchSchema(_EndpointFields):
    """PATCH body — a partial FHIR R4 Endpoint (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `managingOrganization` replaces the whole Reference, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "suspended",
                "address": "https://fhir.generalhospital.example/r4-new",
            }
        }
    }

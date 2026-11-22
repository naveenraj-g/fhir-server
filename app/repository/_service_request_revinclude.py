"""`_revinclude=ServiceRequest:...` declarations for the registries of the resources a
ServiceRequest points at (Patient, Location, Practitioner, PractitionerRole, RelatedPerson,
Organization, HealthcareService, Encounter, Specimen).

Kept in one neutral module that imports the ServiceRequest registry lazily, so the registries
don't import each other at load (same arrangement as `_specimen_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_service_request_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """ServiceRequest:<param> - service requests whose `prefix` column reference points at one
    of the matched rows of `resource_type` (`subject` and `patient` for a Patient, `subject` for
    a Location, `requester` for a requester type, `encounter` for an Encounter)."""

    async def fetch(session, ctx, rows):
        from app.repository.service_request.search import (
            revinclude_service_requests_via_column,
        )

        return await revinclude_service_requests_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("ServiceRequest", param, resource_type, fetch, reverse=True)
        for param in params
    )


def performer_service_request_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """ServiceRequest:performer - service requests with a performer pointing at one of the
    matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.service_request import ServiceRequestPerformer
        from app.repository.service_request.search import (
            revinclude_service_requests_via_child,
        )

        return await revinclude_service_requests_via_child(
            ServiceRequestPerformer, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "ServiceRequest", "performer", resource_type, fetch, reverse=True
        ),
    )


def specimen_service_request_revincludes(key) -> tuple[IncludeTarget, ...]:
    """ServiceRequest:specimen - service requests whose `specimen` points at one of the matched
    Specimens."""

    async def fetch(session, ctx, rows):
        from app.models.service_request import ServiceRequestReference
        from app.repository.service_request.search import (
            revinclude_service_requests_via_child,
        )

        return await revinclude_service_requests_via_child(
            ServiceRequestReference,
            "Specimen",
            key,
            ServiceRequestReference.param == "specimen",
        )(session, ctx, rows)

    return (
        IncludeTarget("ServiceRequest", "specimen", "Specimen", fetch, reverse=True),
    )


def based_on_service_request_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """ServiceRequest:based-on - service requests whose `basedOn` is one of the matched rows of
    `resource_type` (a CarePlan)."""

    async def fetch(session, ctx, rows):
        from app.models.service_request import ServiceRequestReference
        from app.repository.service_request.search import (
            revinclude_service_requests_via_child,
        )

        return await revinclude_service_requests_via_child(
            ServiceRequestReference,
            resource_type,
            key,
            ServiceRequestReference.param == "based-on",
        )(session, ctx, rows)

    return (
        IncludeTarget("ServiceRequest", "based-on", resource_type, fetch, reverse=True),
    )

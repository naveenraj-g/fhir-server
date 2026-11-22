"""`_revinclude=Group:...` declarations for the registries of the resources a Group points at
(`member`: Patient, Practitioner, PractitionerRole, Medication; `managing-entity`: Organization,
RelatedPerson, Practitioner, PractitionerRole).

Kept in one neutral module that imports the Group registry lazily, so the registries don't
import each other at load (same arrangement as `_medication_request_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def member_group_revincludes(resource_type: str, key) -> tuple[IncludeTarget, ...]:
    """Group:member - groups with a member pointing at one of the matched rows of
    `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.group.search import revinclude_groups_via_member

        return await revinclude_groups_via_member(resource_type, key)(
            session, ctx, rows
        )

    return (IncludeTarget("Group", "member", resource_type, fetch, reverse=True),)


def managing_entity_group_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """Group:managing-entity - groups whose managingEntity points at one of the matched rows of
    `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.group.search import revinclude_groups_via_managing_entity

        return await revinclude_groups_via_managing_entity(resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("Group", "managing-entity", resource_type, fetch, reverse=True),
    )

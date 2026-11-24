"""`_revinclude=PlanDefinition:definition` declared on the registries of the resources an
action's `definitionCanonical` can name (ActivityDefinition, Questionnaire; PlanDefinition itself
declares it in its own registry).

Kept in one neutral module that imports the PlanDefinition registry lazily, so the registries do
not import each other at load (same arrangement as `_communication_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def definition_plan_definition_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """PlanDefinition:definition - plan definitions whose action names one of the matched rows of
    `resource_type` (by a relative `Type/<id>` canonical)."""

    async def fetch(session, ctx, rows):
        from app.repository.plan_definition.search import (
            revinclude_plan_definitions_via_reference,
        )

        return await revinclude_plan_definitions_via_reference(
            "definition", resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "PlanDefinition", "definition", resource_type, fetch, reverse=True
        ),
    )

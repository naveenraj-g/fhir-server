"""`_revinclude=MedicationKnowledge:...` declarations for the registries of the resources a
MedicationKnowledge points at (`manufacturer`: Organization; `monograph`: DocumentReference).

Kept in one neutral module that imports the MedicationKnowledge registry lazily, so the
registries do not import each other at load (same arrangement as `_medication_dispense_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_medication_knowledge_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationKnowledge:<param> - entries whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`manufacturer` for an Organization)."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_knowledge.search import (
            revinclude_medication_knowledge_via_column,
        )

        return await revinclude_medication_knowledge_via_column(
            prefix, resource_type, key
        )(session, ctx, rows)

    return tuple(
        IncludeTarget("MedicationKnowledge", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_medication_knowledge_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """MedicationKnowledge:monograph - entries with a reference row of `param` pointing at one
    of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.medication_knowledge.search import (
            revinclude_medication_knowledge_via_reference,
        )

        return await revinclude_medication_knowledge_via_reference(
            param, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget("MedicationKnowledge", param, resource_type, fetch, reverse=True),
    )

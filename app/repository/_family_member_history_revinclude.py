"""`_revinclude=FamilyMemberHistory:...` declarations for the registries of the resources
a FamilyMemberHistory points at (Patient).

Kept in one neutral module that imports the FamilyMemberHistory registry lazily, so the
registries don't import each other at load (same arrangement as `_immunization_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def patient_history_revincludes(key) -> tuple[IncludeTarget, ...]:
    """FamilyMemberHistory:patient — histories about one of the matched Patients."""

    async def fetch(session, ctx, rows):
        from app.repository.family_member_history.search import (
            revinclude_histories_via_patient,
        )

        return await revinclude_histories_via_patient(key)(session, ctx, rows)

    return (
        IncludeTarget("FamilyMemberHistory", "patient", "Patient", fetch, reverse=True),
    )

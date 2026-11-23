"""`_revinclude=DocumentReference:...` declarations for the registries of the resources a
DocumentReference points at (`subject` / `patient`: Patient, Practitioner, Group; `author`:
Practitioner, PractitionerRole, Organization, Patient, RelatedPerson; `authenticator`:
Practitioner, PractitionerRole, Organization; `custodian`: Organization; `encounter`: Encounter,
EpisodeOfCare).

Kept in one neutral module that imports the DocumentReference registry lazily, so the registries
don't import each other at load (same arrangement as `_care_team_revinclude`). There is no
`:related` revinclude (Reference(Any))."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_document_reference_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """DocumentReference:<param> - documents whose `prefix` column reference points at one of the
    matched rows of `resource_type` (`subject` and `patient` for a Patient, `subject` for a
    Practitioner or Group, `authenticator` / `custodian` for the types they can name)."""

    async def fetch(session, ctx, rows):
        from app.repository.document_reference.search import (
            revinclude_documents_via_column,
        )

        return await revinclude_documents_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("DocumentReference", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_document_reference_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """DocumentReference:author / :encounter - documents with a reference row of `param` pointing
    at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.document_reference.search import (
            revinclude_documents_via_reference,
        )

        return await revinclude_documents_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget("DocumentReference", param, resource_type, fetch, reverse=True),
    )

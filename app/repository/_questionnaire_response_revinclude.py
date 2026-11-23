"""`_revinclude=QuestionnaireResponse:...` declarations for the registries of the resources a
QuestionnaireResponse points at (`subject` / `patient`: Patient; `author`: Practitioner,
PractitionerRole, Organization, Patient, RelatedPerson; `source`: Practitioner, PractitionerRole,
Patient, RelatedPerson; `encounter`: Encounter; `based-on`: CarePlan, ServiceRequest; `part-of`:
Observation, Procedure).

Kept in one neutral module that imports the QuestionnaireResponse registry lazily, so the
registries don't import each other at load (same arrangement as `_document_reference_revinclude`).
"""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_questionnaire_response_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """QuestionnaireResponse:<param> - responses whose `prefix` column reference points at one of
    the matched rows of `resource_type` (`subject` and `patient` for a Patient; `author`, `source`
    or `encounter` for the types they can name)."""

    async def fetch(session, ctx, rows):
        from app.repository.questionnaire_response.search import (
            revinclude_responses_via_column,
        )

        return await revinclude_responses_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget(
            "QuestionnaireResponse", param, resource_type, fetch, reverse=True
        )
        for param in params
    )


def reference_questionnaire_response_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """QuestionnaireResponse:based-on / :part-of - responses with a reference row of `param`
    pointing at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.repository.questionnaire_response.search import (
            revinclude_responses_via_reference,
        )

        return await revinclude_responses_via_reference(param, resource_type, key)(
            session, ctx, rows
        )

    return (
        IncludeTarget(
            "QuestionnaireResponse", param, resource_type, fetch, reverse=True
        ),
    )

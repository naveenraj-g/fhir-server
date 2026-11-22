"""`_revinclude=CarePlan:...` declarations for the registries of the resources a CarePlan points at
(`subject` / `patient`: Patient, Group; `encounter`: Encounter; `care-team`: CareTeam;
`condition`: Condition; `performer`: Practitioner, PractitionerRole, Organization, RelatedPerson,
Patient, CareTeam, HealthcareService; `activity-reference`: Appointment, MedicationRequest,
ServiceRequest).

Kept in one neutral module that imports the CarePlan registry lazily, so the registries don't
import each other at load (same arrangement as `_care_team_revinclude`)."""

from __future__ import annotations

from app.fhir.search import IncludeTarget


def column_care_plan_revincludes(
    params: tuple[str, ...], prefix: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CarePlan:<param> - care plans whose `prefix` column reference points at one of the matched
    rows of `resource_type` (`subject` and `patient` for a Patient, `subject` for a Group,
    `encounter` for an Encounter)."""

    async def fetch(session, ctx, rows):
        from app.repository.care_plan.search import revinclude_care_plans_via_column

        return await revinclude_care_plans_via_column(prefix, resource_type, key)(
            session, ctx, rows
        )

    return tuple(
        IncludeTarget("CarePlan", param, resource_type, fetch, reverse=True)
        for param in params
    )


def reference_care_plan_revincludes(
    param: str, resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CarePlan:care-team / CarePlan:condition - care plans with a row of that `param` in the
    reference table pointing at one of the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.care_plan import CarePlanReference
        from app.repository.care_plan.search import revinclude_care_plans_via_child

        return await revinclude_care_plans_via_child(
            CarePlanReference,
            resource_type,
            key,
            CarePlanReference.param == param,
        )(session, ctx, rows)

    return (IncludeTarget("CarePlan", param, resource_type, fetch, reverse=True),)


def performer_care_plan_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CarePlan:performer - care plans with an activity performer pointing at one of the matched
    rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.care_plan import CarePlanPerformer
        from app.repository.care_plan.search import revinclude_care_plans_via_child

        return await revinclude_care_plans_via_child(
            CarePlanPerformer, resource_type, key
        )(session, ctx, rows)

    return (IncludeTarget("CarePlan", "performer", resource_type, fetch, reverse=True),)


def activity_care_plan_revincludes(
    resource_type: str, key
) -> tuple[IncludeTarget, ...]:
    """CarePlan:activity-reference - care plans with an activity whose reference points at one of
    the matched rows of `resource_type`."""

    async def fetch(session, ctx, rows):
        from app.models.care_plan import CarePlanActivity
        from app.repository.care_plan.search import revinclude_care_plans_via_child

        return await revinclude_care_plans_via_child(
            CarePlanActivity, resource_type, key
        )(session, ctx, rows)

    return (
        IncludeTarget(
            "CarePlan", "activity-reference", resource_type, fetch, reverse=True
        ),
    )

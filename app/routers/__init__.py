import inspect
import sys

from fastapi import APIRouter

# Every resource router module this server can mount. Every module is always
# imported (cheap, no side effects) — only *mounting* is conditional on
# configs/routes.yaml, resolved via discover_routers() at startup (see
# app/main.py's lifespan). Adding a new resource means adding one more
# `<name>,` entry below — nothing else to register (mirrors txtai's
# api/routers/__init__.py + api/application.py's apirouters() pattern).
#
# Trimmed down to Organization/Location/HealthcareService only — every other
# resource was deleted to rebuild from scratch against the now-settled
# tenant_id/coding-list/location_pk-style conventions, one resource at a
# time, rather than carrying forward drifted code. See git history for the
# deleted implementations if a past version is ever needed for reference.
from . import activity_definition as activity_definition
from . import allergy_intolerance as allergy_intolerance
from . import appointment as appointment
from . import appointment_response as appointment_response
from . import care_plan as care_plan
from . import care_team as care_team
from . import condition as condition
from . import consent as consent
from . import diagnostic_report as diagnostic_report
from . import document_reference as document_reference
from . import encounter as encounter
from . import episode_of_care as episode_of_care
from . import flag as flag
from . import group as group
from . import healthcare_service as healthcare_service
from . import location as location
from . import medication_request as medication_request
from . import observation as observation
from . import observation_definition as observation_definition
from . import organization as organization
from . import patient as patient
from . import plan_definition as plan_definition
from . import practitioner as practitioner
from . import practitioner_role as practitioner_role
from . import procedure as procedure
from . import questionnaire as questionnaire
from . import questionnaire_response as questionnaire_response
from . import related_person as related_person
from . import schedule as schedule
from . import service_request as service_request
from . import slot as slot
from . import specimen as specimen
from . import task as task
from . import goal as goal
from . import communication_request as communication_request

__all__ = [
    "activity_definition",
    "allergy_intolerance",
    "appointment",
    "appointment_response",
    "care_plan",
    "care_team",
    "condition",
    "consent",
    "diagnostic_report",
    "discover_routers",
    "document_reference",
    "encounter",
    "episode_of_care",
    "flag",
    "group",
    "healthcare_service",
    "location",
    "medication_request",
    "observation",
    "observation_definition",
    "organization",
    "patient",
    "plan_definition",
    "practitioner",
    "practitioner_role",
    "procedure",
    "questionnaire",
    "questionnaire_response",
    "related_person",
    "schedule",
    "service_request",
    "slot",
    "specimen",
    "communication_request",
    "goal",
    "task",
]


def discover_routers() -> dict[str, APIRouter]:
    """Returns the module-level `router: APIRouter` for every name in this
    module's own `__all__` — mirrors txtai's api/application.py::apirouters().
    Each router already carries its own prefix/tags (set at construction in
    the resource's own module/package), so mounting is just
    `app.include_router(router)` — no separate prefix/tag table to keep in
    sync.

    Deliberately NOT a blanket `inspect.getmembers(here, inspect.ismodule)`
    scan of this package's whole namespace, even though that looks
    equivalent at first glance — Python's import machinery binds ANY
    submodule anyone imports anywhere (e.g. main.py's
    `from app.routers.terminology import router as ...`) onto this package
    object as a side effect, regardless of whether it's re-exported here.
    A blanket scan would see those too, and if a name like "terminology"
    ever also appeared in configs/config.yaml's routes.enabled (exactly
    what making it independently toggleable requires), this function would
    hand it back to mount_routers() for a SECOND, duplicate mount on top of
    its own separate app.include_router() call in main.py — confirmed the
    hard way via duplicate-operation-id warnings at startup. Restricting to
    __all__ is what actually keeps this scoped to the resources meant to be
    mounted together under one shared /api/fhir/v1 prefix."""
    here = sys.modules[__name__]
    result: dict[str, APIRouter] = {}
    for name in __all__:
        if name == "discover_routers":
            continue
        mod = getattr(here, name, None)
        if inspect.ismodule(mod) and isinstance(getattr(mod, "router", None), APIRouter):
            result[name] = mod.router
    return result

import inspect
import sys

from fastapi import APIRouter

# Every resource router module this server can mount. Every module is always
# imported (cheap, no side effects) — only *mounting* is conditional on
# configs/routes.yaml, resolved via discover_routers() at startup (see
# app/main.py's lifespan). Adding a new resource means adding one more
# `<name>,` entry below — nothing else to register (mirrors txtai's
# api/routers/__init__.py + api/application.py's apirouters() pattern).
from . import allergy_intolerance as allergy_intolerance
from . import appointment as appointment
from . import audit_event as audit_event
from . import care_plan as care_plan
from . import claim as claim
from . import claim_response as claim_response
from . import condition as condition
from . import coverage as coverage
from . import device_request as device_request
from . import diagnostic_report as diagnostic_report
from . import document_reference as document_reference
from . import encounter as encounter
from . import episode_of_care as episode_of_care
from . import healthcare_service as healthcare_service
from . import immunization as immunization
from . import insurance_plan as insurance_plan
from . import invoice as invoice
from . import location as location
from . import medication as medication
from . import medication_request as medication_request
from . import observation as observation
from . import organization as organization
from . import patient as patient
from . import practitioner as practitioner
from . import practitioner_role as practitioner_role
from . import procedure as procedure
from . import provenance as provenance
from . import questionnaire_response as questionnaire_response
from . import related_person as related_person
from . import schedule as schedule
from . import service_request as service_request
from . import slot as slot
from . import specimen as specimen
from . import task as task

__all__ = [
    "allergy_intolerance",
    "appointment",
    "audit_event",
    "care_plan",
    "claim",
    "claim_response",
    "condition",
    "coverage",
    "device_request",
    "diagnostic_report",
    "discover_routers",
    "document_reference",
    "encounter",
    "episode_of_care",
    "healthcare_service",
    "immunization",
    "insurance_plan",
    "invoice",
    "location",
    "medication",
    "medication_request",
    "observation",
    "organization",
    "patient",
    "practitioner",
    "practitioner_role",
    "procedure",
    "provenance",
    "questionnaire_response",
    "related_person",
    "schedule",
    "service_request",
    "slot",
    "specimen",
    "task",
]


def discover_routers() -> dict[str, APIRouter]:
    """Introspects this package's own namespace for submodules exposing a
    module-level `router: APIRouter` — mirrors txtai's
    api/application.py::apirouters(). Each router already carries its own
    prefix/tags (set at construction in the resource's own module/package),
    so mounting is just `app.include_router(router)` — no separate
    prefix/tag table to keep in sync."""
    here = sys.modules[__name__]
    return {
        name: mod.router
        for name, mod in inspect.getmembers(here, inspect.ismodule)
        if isinstance(getattr(mod, "router", None), APIRouter)
    }

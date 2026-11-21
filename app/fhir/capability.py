"""
FHIR R4 CapabilityStatement (https://www.hl7.org/fhir/R4/capabilitystatement.html),
generated at request time — nothing is stored.

What a resource declares comes from its `SearchRegistry` (the same one that
drives parsing, SQL and the OpenAPI parameter list), so the statement can't
drift from what search actually accepts.

Only resources whose search runs on `app.fhir.search` are listed in detail
(`SEARCH_REGISTRIES` below). To add a resource: give it a registry factory and
add one line here. Resources still on the old per-resource list filters are
not listed at all; the statement says so in `rest.documentation`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.core.config import settings
from app.fhir.search import SearchParam, SearchRegistry
from app.repository.endpoint.search import endpoint_search
from app.repository.appointment.search import appointment_search
from app.repository.appointment_response.search import appointment_response_search
from app.repository.encounter.search import encounter_search
from app.repository.allergy_intolerance.search import allergy_intolerance_search
from app.repository.condition.search import condition_search
from app.repository.diagnostic_report.search import diagnostic_report_search
from app.repository.family_member_history.search import family_member_history_search
from app.repository.immunization.search import immunization_search
from app.repository.immunization_evaluation.search import immunization_evaluation_search
from app.repository.immunization_recommendation.search import immunization_recommendation_search
from app.repository.procedure.search import procedure_search
from app.repository.related_person.search import related_person_search
from app.repository.healthcare_service.search import healthcare_service_search
from app.repository.location.search import location_search
from app.repository.organization.search import organization_search
from app.repository.patient.search import patient_search
from app.repository.practitioner.search import practitioner_search
from app.repository.practitioner_role.search import practitioner_role_search
from app.repository.schedule.search import schedule_search
from app.repository.slot.search import slot_search

# routes.enabled name -> registry factory.
SEARCH_REGISTRIES: dict[str, Callable[[], SearchRegistry]] = {
    "organization": organization_search,
    "location": location_search,
    "practitioner": practitioner_search,
    "healthcare_service": healthcare_service_search,
    "endpoint": endpoint_search,
    "practitioner_role": practitioner_role_search,
    "schedule": schedule_search,
    "slot": slot_search,
    "patient": patient_search,
    "appointment": appointment_search,
    "appointment_response": appointment_response_search,
    "encounter": encounter_search,
    "related_person": related_person_search,
    "allergy_intolerance": allergy_intolerance_search,
    "condition": condition_search,
    "diagnostic_report": diagnostic_report_search,
    "family_member_history": family_member_history_search,
    "immunization": immunization_search,
    "immunization_evaluation": immunization_evaluation_search,
    "immunization_recommendation": immunization_recommendation_search,
    "procedure": procedure_search,
}

# Interactions the Organization/Location/Practitioner/HealthcareService/Endpoint/PractitionerRole/Schedule routers implement.
# (No `update`/PUT, no `vread`, no history.)
_INTERACTIONS = ("read", "create", "patch", "delete", "search-type")

_RESULT_PARAMS = (
    "_count (default %d, max %d; 0 = count only), _offset, _sort (multi-key, -desc), "
    "_total, _summary, _elements, _include / _revinclude (+ :iterate)"
)


def _param_documentation(param: SearchParam) -> str:
    doc = param.description
    mods = sorted(m for m in param.modifiers if m != "missing")
    if "missing" in param.modifiers:
        mods.append("missing")
    if mods:
        doc += " Modifiers: " + ", ".join(f":{m}" for m in mods) + "."
    if param.targets:
        doc += " Targets: " + ", ".join(param.targets) + "."
    if param.chain_targets:
        doc += f" Chaining: {param.name}.<param> on {', '.join(param.chain_targets)}."
    if param.sort is not None:
        doc += " Sortable."
    return doc


def _search_param(resource_type: str, param: SearchParam) -> dict:
    # Common (Resource-level) parameters carry the `Resource-` definition.
    owner = "Resource" if param.name in ("_id", "_lastUpdated") else resource_type
    return {
        "name": param.name,
        "definition": f"http://hl7.org/fhir/SearchParameter/{owner}-{param.name.lstrip('_')}",
        "type": param.type,
        "documentation": _param_documentation(param),
    }


def _include_strings(targets) -> list[str]:
    return [f"{t.source}:{t.param}" for t in targets]


def _resource_entry(resource_type: str, registry: SearchRegistry) -> dict:
    entry = {
        "type": resource_type,
        "profile": f"http://hl7.org/fhir/StructureDefinition/{resource_type}",
        "interaction": [{"code": code} for code in _INTERACTIONS],
        "versioning": "no-version",
        "conditionalCreate": False,
        "conditionalUpdate": False,
        "conditionalDelete": "not-supported",
        "searchParam": [
            _search_param(resource_type, p) for p in registry.params.values()
        ],
    }
    if registry.includes:
        entry["searchInclude"] = _include_strings(registry.includes)
    if registry.revincludes:
        entry["searchRevInclude"] = _include_strings(registry.revincludes)
    return entry


def build_capability_statement(base_url: str) -> dict:
    enabled = set(settings.routes.enabled)
    resources = []
    for name, factory in SEARCH_REGISTRIES.items():
        if name not in enabled:
            continue
        registry = factory()
        resources.append(_resource_entry(registry.resource_type, registry))
    resources.sort(key=lambda r: r["type"])

    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "publisher": settings.app.title,
        "kind": "instance",
        "software": {"name": settings.app.title, "version": settings.app.version},
        "implementation": {"description": settings.app.title, "url": base_url},
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "rest": [
            {
                "mode": "server",
                "documentation": (
                    "Search results parameters: "
                    + _RESULT_PARAMS
                    % (settings.pagination.default_limit, settings.pagination.max_limit)
                    + ". Unknown search parameters are ignored and reported in the Bundle "
                    "(400 with `Prefer: handling=strict`). Only the resources listed here are "
                    "described: resources not listed still use older, non-FHIR-search list "
                    "filters and are not covered by this statement."
                ),
                "resource": resources,
            }
        ],
    }

"""Which resource types a reference search can follow is defined once (`_search_targets.MODELED`,
derived from RESOURCE_REGISTRY), not listed per resource. These tests are the guard: a rebuilt
resource must be followable from every Reference(Any) element, and from every known reference
that can point at it, without anyone adding it to a list."""

import importlib

import pytest

from app.fhir.search import SearchRegistry
from app.models.shared.resource_types import ANY_RESOURCE_TYPES, is_any
from app.repository._reference_check import checkable_types
from app.repository._search_targets import MODELED, modeled_types, snake


def _registry(resource_type: str) -> SearchRegistry:
    _m, _c, _i, module, factory = MODELED[resource_type]
    return getattr(importlib.import_module(module), factory)()


def test_every_rebuilt_resource_is_followable():
    """A content-based resource in RESOURCE_REGISTRY has a model and a search registry by the
    naming convention; one that does not would be missing from every chain and include."""
    assert set(modeled_types()) == set(checkable_types())


@pytest.mark.parametrize("resource_type", modeled_types())
def test_search_registry_by_convention(resource_type):
    registry = _registry(resource_type)
    assert registry.resource_type == resource_type
    model_module, model_class, id_column, *_ = MODELED[resource_type]
    model = getattr(importlib.import_module(model_module), model_class)
    assert hasattr(model, id_column) and hasattr(model, "content")
    assert id_column == f"{snake(resource_type)}_id"


def _reference_params():
    for resource_type in modeled_types():
        registry = _registry(resource_type)
        for param in registry.params.values():
            if param.type == "reference":
                yield resource_type, registry, param


def test_reference_any_allows_every_r4_type_and_follows_every_rebuilt_one():
    """Every Reference(Any) parameter (its targets are the whole R4 list) chains through, and
    `_include`s, every rebuilt resource - none is missing, whatever order they were built in."""
    any_params = [
        (rt, reg, p) for rt, reg, p in _reference_params() if is_any(p.targets)
    ]
    # ClinicalImpression.supporting-info, DetectedIssue.implicated, ImmunizationRecommendation.
    # information, Condition.evidence-detail, Appointment.supporting-info, DocumentReference.
    # related, Observation.focus, QuestionnaireResponse.subject
    assert {(rt, p.name) for rt, _r, p in any_params} == {
        ("ClinicalImpression", "supporting-info"),
        ("DetectedIssue", "implicated"),
        ("ImmunizationRecommendation", "information"),
        ("Condition", "evidence-detail"),
        ("Appointment", "supporting-info"),
        ("DocumentReference", "related"),
        ("Observation", "focus"),
        ("QuestionnaireResponse", "subject"),
        ("Task", "subject"),
        ("Task", "focus"),
        ("Task", "based-on"),
        ("Consent", "data"),
        ("Communication", "based-on"),
        ("Communication", "part-of"),
    }
    for rt, registry, param in any_params:
        assert param.targets is ANY_RESOURCE_TYPES
        assert set(param.chain_targets) == set(MODELED), (rt, param.name)
        included = {
            i.target
            for i in registry.includes
            if i.source == rt and i.param == param.name
        }
        assert included == set(MODELED), (rt, param.name)


def test_known_references_follow_only_types_their_spec_list_allows():
    """A known reference's `targets` is the spec's list; it chains only through the types in it
    that are rebuilt, never through a type outside it (that is the check that rejects
    `subject:Observation.` on an element that is not allowed to hold one)."""
    for rt, _registry_, param in _reference_params():
        if is_any(param.targets):
            continue
        assert set(param.chain_targets) <= set(param.targets) & set(MODELED), (
            rt,
            param.name,
        )

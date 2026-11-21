"""The search engine's own tables must agree with every registry that uses it.

A resource declares each search parameter with a `type`; the engine then looks that type up in
`MODIFIERS_BY_TYPE` (which modifiers it may carry), documents it from `_TYPE_DOCS` (OpenAPI) and
names it in the `ParamType` literal. Adding a new type (`composite` for Observation) and forgetting
one of those leaves a silent hole, so this walks every registry mounted on the server and checks
the three places line up, and that each parameter's modifiers are ones its type allows.
"""

import typing

import pytest

from app.fhir.capability import SEARCH_REGISTRIES
from app.fhir.search import openapi, params

PARAM_TYPES = set(typing.get_args(params.ParamType))


def test_the_three_type_tables_list_the_same_types():
    assert PARAM_TYPES == set(params.MODIFIERS_BY_TYPE) == set(openapi._TYPE_DOCS)


@pytest.mark.parametrize("name", sorted(SEARCH_REGISTRIES))
def test_every_parameter_of_a_registry_uses_a_known_type_and_valid_modifiers(name):
    registry = SEARCH_REGISTRIES[name]()
    for param in registry.params.values():
        where = f"{registry.resource_type}.{param.name}"
        assert param.type in PARAM_TYPES, f"{where}: unknown type {param.type!r}"
        extra = set(param.modifiers) - params.MODIFIERS_BY_TYPE[param.type]
        assert not extra, f"{where} ({param.type}): modifiers {sorted(extra)} are not valid for the type"
        if param.type == "reference":
            assert param.targets, f"{where}: a reference parameter needs its target types"
        else:
            assert not (param.targets or param.chain_targets), f"{where}: targets/chaining on a non-reference"


def test_composite_parameters_take_no_modifiers_and_are_not_sortable():
    from app.repository.observation.search import observation_search

    composites = [p for p in observation_search().params.values() if p.type == "composite"]
    assert len(composites) == 8
    for param in composites:
        assert param.modifiers == frozenset(), param.name
        assert param.sort is None, param.name

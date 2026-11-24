"""Which resource types a search can follow - one definition for every resource.

A reference search parameter needs two things about each type it can point at:

- is the type allowed in this element at all - `SearchParam.targets`: the spec's list for a
  known reference (kept in the resource's model package), every R4 type for Reference(Any)
  (`app.fhir.search.resource_types.ANY_RESOURCE_TYPES`);
- can the server follow it (chaining, `_include`) - the type is a rebuilt resource: it has a model
  and a search registry. That is what `_MODELED` used to list by hand in every resource's
  `search.py`, and it drifted (a rebuilt resource was missing from half of them).

`MODELED` answers the second question from `RESOURCE_REGISTRY` (the same source the write-time
reference check uses) and the project's naming convention, so registering a rebuilt resource is
all it takes for every other resource to chain and `_include` through it:

    app/models/<snake>                      <Type>Model (the registry's model class)
    app/repository/<snake>/search.py        <snake>_search()

It is a lazy mapping with the shape the old dicts had:
`type -> (model module, model class, public id column, search module, search factory)`.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
from collections.abc import Iterator, Mapping
from functools import lru_cache


def snake(resource_type: str) -> str:
    """`EpisodeOfCare` -> `episode_of_care`."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", resource_type).lower()


@lru_cache(maxsize=1)
def _entries() -> dict[str, tuple[str, str, str, str, str]]:
    # Imported here: app.core.reference_resolver imports every model.
    from app.repository._reference_check import checkable_types
    from app.core.reference_resolver import RESOURCE_REGISTRY

    out: dict[str, tuple[str, str, str, str, str]] = {}
    for resource_type in sorted(checkable_types()):
        model, id_column = RESOURCE_REGISTRY[resource_type]
        s = snake(resource_type)
        module = f"app.repository.{s}.search"
        if importlib.util.find_spec(module) is None:
            continue  # content-based but no search registry yet
        out[resource_type] = (
            model.__module__,
            model.__name__,
            id_column,
            module,
            f"{s}_search",
        )
    return out


class _Modeled(Mapping):
    def __getitem__(self, resource_type: str):
        return _entries()[resource_type]

    def __iter__(self) -> Iterator[str]:
        return iter(_entries())

    def __len__(self) -> int:
        return len(_entries())


# Every rebuilt resource type the server can chain through and `_include`.
MODELED: Mapping[str, tuple[str, str, str, str, str]] = _Modeled()


def modeled_types() -> list[str]:
    return sorted(_entries())

"""
FHIR R4 ObservationDefinition search (https://www.hl7.org/fhir/R4/search.html).

R4 defines **no** resource-specific search parameter for ObservationDefinition: its resource
page (https://www.hl7.org/fhir/R4/observationdefinition.html) has no Search Parameters section,
so only the common `_id` and `_lastUpdated` apply. They are declared here once for
app.fhir.search, which also gives the resource `_sort`, `_count`, `_offset`, `_total`,
`_summary`, `_elements` and the searchset Bundle. There is no search index to read: `_id` is the
public `observation_definition_id` column and `_lastUpdated` the audit timestamps.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import false, func, true

from app.fhir.search import SearchParam, SearchRegistry
from app.fhir.search.sql import date_match
from app.fhir.search.values import parse_token
from app.models.observation_definition import ObservationDefinitionModel

M = ObservationDefinitionModel


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.observation_definition_id == int(token.code)


def _register_kind() -> None:
    """How the search engine identifies and renders ObservationDefinition rows."""
    from app.fhir.mappers.observation_definition import (
        to_fhir_observation_definition,
    )
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "ObservationDefinition",
            lambda r: r.observation_definition_id,
            to_fhir_observation_definition,
            "observation-definitions",
        )
    )


@cache
def observation_definition_search() -> SearchRegistry:
    _register_kind()
    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public observation_definition id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.observation_definition_id,
            example="400001",
        ),
        SearchParam(
            "_lastUpdated",
            "date",
            "When the resource last changed (meta.lastUpdated)",
            "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v),
            lambda ctx: true(),
            sort=last_updated,
            example="ge2024-01-01",
        ),
    ]
    return SearchRegistry(
        resource_type="ObservationDefinition",
        params={p.name: p for p in params},
        # Σ elements in the R4 ObservationDefinition definition (beyond id/meta/implicitRules).
        summary_elements=frozenset({"category", "code", "identifier"}),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"code"}),
        # Nothing it references (ValueSet) is on the engine, and R4 defines no search parameter
        # that points at an ObservationDefinition.
        includes=(),
        revincludes=(),
        default_sort=lambda: [M.observation_definition_id.desc()],
    )

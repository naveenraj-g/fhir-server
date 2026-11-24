"""
FHIR R4 SpecimenDefinition search parameters
(https://www.hl7.org/fhir/R4/specimendefinition.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort` and the OpenAPI docs
all come from specimen_definition_search() below. R4 defines three parameters, all tokens:
`identifier` (an Identifier), `type` (`typeCollected`) and `container` (`container.type` of every
`typeTested` entry).

Each parameter's SQL reads only the search index (SpecimenDefinitionModel's child tables, see its
docstring) - never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, select, true

from app.fhir.search import MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.specimen_definition import (
    SpecimenDefinitionIdentifier,
    SpecimenDefinitionModel,
    SpecimenDefinitionToken,
)

M = SpecimenDefinitionModel
_I = SpecimenDefinitionIdentifier
_Tk = SpecimenDefinitionToken


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(
        select(literal(1)).where(model.specimen_definition_pk == M.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.specimen_definition_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.specimen_definition_id == int(token.code)


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(
            _I, token_text_match((_I.type_text_norm, _I.type_display_norm), value)
        )
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(
            _I,
            _I.type_system == type_system,
            _I.type_code == type_code,
            _I.value == ident,
        )
    return _exists(_I, token_match(_I.system, _I.value, value))


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


def _register_kind() -> None:
    """How the search engine identifies and renders SpecimenDefinition rows."""
    from app.fhir.mappers.specimen_definition import to_fhir_specimen_definition
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "SpecimenDefinition",
            lambda r: r.specimen_definition_id,
            to_fhir_specimen_definition,
            "specimen-definitions",
        )
    )


_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})


@cache
def specimen_definition_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _TOKEN,
            sort=sort,
            example=example,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public specimen_definition id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.specimen_definition_id,
            example="550001",
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
        token(
            "container",
            "The type of specimen conditioned in container expected by the lab",
            "SpecimenDefinition.typeTested.container.type",
            "http://terminology.hl7.org/CodeSystem/v2-0487|SPECIMEN",
        ),
        SearchParam(
            "identifier",
            "token",
            "The unique identifier associated with the specimen",
            "SpecimenDefinition.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            _IDENTIFIER,
            sort=lambda: _child_sort(_I.value, _I),
            example="https://fhir-server.dev/fhir/identifier-system/specimen-definition-id|SD-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        token(
            "type",
            "The type of collected specimen",
            "SpecimenDefinition.typeCollected",
            "http://terminology.hl7.org/CodeSystem/v2-0487|BLD",
        ),
    ]
    return SearchRegistry(
        resource_type="SpecimenDefinition",
        params={p.name: p for p in params},
        # Σ elements in the R4 SpecimenDefinition definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "typeCollected",
                "patientPreparation",
                "timeAspect",
                "collection",
            }
        ),
        # No element has min cardinality 1 at the top level in R4.
        mandatory_elements=frozenset(),
        # Nothing it references is on the engine (its additive may be a Substance), and no R4
        # search parameter of another resource points at a SpecimenDefinition.
        includes=(),
        revincludes=(),
        default_sort=lambda: [M.specimen_definition_id.desc()],
    )

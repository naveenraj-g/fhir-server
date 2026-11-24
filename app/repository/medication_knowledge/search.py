"""
FHIR R4 MedicationKnowledge search parameters
(https://www.hl7.org/fhir/R4/medicationknowledge.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from medication_knowledge_search()
below. Same arrangement as app.repository.medication.search (a column reference, shared token
and reference tables).

Each parameter's SQL reads only the search index (MedicationKnowledgeModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    reference_match,
    token_condition,
)
from app.fhir.search.values import parse_token
from app.models.medication_knowledge import (
    MANUFACTURER_TYPES,
    REFERENCE_TYPES,
    MedicationKnowledgeModel,
    MedicationKnowledgeReference,
    MedicationKnowledgeStatus,
    MedicationKnowledgeToken,
)
from app.repository._search_targets import MODELED

P = MedicationKnowledgeModel
_Tk = MedicationKnowledgeToken
_R = MedicationKnowledgeReference
_STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medicationknowledge-status"

# Every rebuilt resource type this server can chain through and `_include`: derived from
# RESOURCE_REGISTRY by app/repository/_search_targets.py, so there is no list to keep here.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = MODELED


def _model(resource_type: str):
    module, cls, id_col, *_ = _MODELED[resource_type]
    model = getattr(importlib.import_module(module), cls)
    return model, getattr(model, id_col)


def _registry_of(resource_type: str):
    def get():
        _m, _c, _i, module, factory = _MODELED[resource_type]
        return getattr(importlib.import_module(module), factory)()

    return get


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(
        select(literal(1)).where(model.medication_knowledge_pk == P.id, *conditions)
    )


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.medication_knowledge_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to
    the outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return P.medication_knowledge_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the medicationknowledge-status system: `code` or
    `system|code`; another system or `|code` (no system) never matches; an unknown code
    matches nothing (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.status.is_not(None)
    try:
        return P.status == MedicationKnowledgeStatus(token.code)
    except ValueError:
        return false()


# -- the token parameters ------------------------------------------------------------------


def _token_param(param: str):
    """(match, present, sort) for one of the CodeableConcept token parameters held in the
    shared token table, selected by its `param` value."""

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


def _string_token_param(param: str):
    """(match, present, sort) for a token search over a plain string (`monitoring-program-name`,
    `source-cost`): it matches the code only, so a `system|code` value (a string has no system)
    never matches."""

    def match(value, modifier, ctx):
        token = parse_token(value)
        if token.system is not None or token.code is None:
            return false()
        return _exists(_Tk, _Tk.param == param, _Tk.code == token.code)

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


# -- manufacturer: a reference held as columns ---------------------------------------------


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    medication_knowledge row."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        # `modifier` is a target type (manufacturer:Organization=190001) or None.
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- ingredient / monograph: the reference table -------------------------------------------


def _reference_param(param: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a reference parameter held in the shared reference
    table (`ingredient`, `monograph`)."""

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _R,
                _R.param == param,
                token_condition(
                    _R.reference_identifier_system,
                    _R.reference_identifier_value,
                    parse_token(value),
                ),
            )
        return _exists(
            _R,
            _R.param == param,
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _R,
            _R.param == param,
            or_(
                _R.reference_reference.is_not(None),
                _R.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# -- _include / _revinclude ----------------------------------------------------------------


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`manufacturer`): the rows of `resource_type`
    these entries point at."""

    async def fetch(session, ctx, rows):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(m, id_)
            for m in rows
            if getattr(m, type_) == resource_type and getattr(m, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (`ingredient`, `monograph`)."""

    async def fetch(session, ctx, rows):
        ids = select(model.reference_id).where(
            model.medication_knowledge_pk.in_({m.id for m in rows}),
            model.reference_type == resource_type,
            model.reference_id.is_not(None),
            *conditions,
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_medication_knowledge_via_column(prefix: str, resource_type: str, key):
    """_revinclude=MedicationKnowledge:manufacturer - entries whose column reference points at
    one of these rows (matched on the public id `key(row)`). Declared on the registry of each
    target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(P, f"{prefix}_type"), getattr(P, f"{prefix}_id")
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_medication_knowledge_via_reference(param: str, resource_type: str, key):
    """_revinclude=MedicationKnowledge:monograph - entries with a reference row of `param`
    pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_R.medication_knowledge_pk).where(
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.in_(ids),
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders MedicationKnowledge rows."""
    from app.fhir.mappers.medication_knowledge import to_fhir_medication_knowledge
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "MedicationKnowledge",
            lambda m: m.medication_knowledge_id,
            to_fhir_medication_knowledge,
            "medication-knowledge",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_STRING_TOKEN = frozenset({"not", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def medication_knowledge_search() -> SearchRegistry:
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

    def string_token(name, description, expression, example):
        match, present, sort = _string_token_param(name)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _STRING_TOKEN,
            sort=sort,
            example=example,
        )

    ingredient_targets = REFERENCE_TYPES["ingredient"]
    monograph_targets = REFERENCE_TYPES["monograph"]
    ing_match, ing_present, ing_chain, ing_sort = _reference_param(
        "ingredient", ingredient_targets
    )
    mono_match, mono_present, mono_chain, mono_sort = _reference_param(
        "monograph", monograph_targets
    )
    man_match, man_present, man_chain, man_sort = _column_ref(
        "manufacturer", MANUFACTURER_TYPES
    )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public medication knowledge id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.medication_knowledge_id,
            example="600001",
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
            "classification",
            "Returns entries for a specific category of medication",
            "MedicationKnowledge.medicineClassification.classification",
            "http://www.whocc.no/atc|N02BE01",
        ),
        token(
            "classification-type",
            "Returns entries for a specific type of category (for example a therapeutic classification)",
            "MedicationKnowledge.medicineClassification.type",
            "http://terminology.hl7.org/CodeSystem/medicationknowledge-classification|therapeutic",
        ),
        token(
            "code",
            "Returns entries for a specific code",
            "MedicationKnowledge.code",
            "http://www.nlm.nih.gov/research/umls/rxnorm|1049502",
        ),
        token(
            "doseform",
            "Returns entries for a specific dose form",
            "MedicationKnowledge.doseForm",
            "http://snomed.info/sct|385055001",
        ),
        SearchParam(
            "ingredient",
            "reference",
            "Returns entries for this ingredient (a Substance)",
            "(MedicationKnowledge.ingredient.item as Reference)",
            ing_match,
            ing_present,
            _REFERENCE,
            targets=ingredient_targets,
            chain=ing_chain,
            chain_targets={
                t: _registry_of(t) for t in ingredient_targets if t in _MODELED
            },
            sort=ing_sort,
            example="Substance/1",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "ingredient-code",
            "Returns entries for this ingredient code",
            "(MedicationKnowledge.ingredient.item as CodeableConcept)",
            "http://snomed.info/sct|387458008",
        ),
        SearchParam(
            "manufacturer",
            "reference",
            "Returns entries made or sold for this manufacturer",
            "MedicationKnowledge.manufacturer",
            man_match,
            man_present,
            _REFERENCE,
            targets=MANUFACTURER_TYPES,
            chain=man_chain,
            chain_targets={t: _registry_of(t) for t in MANUFACTURER_TYPES},
            sort=man_sort,
            example="Organization/190001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        string_token(
            "monitoring-program-name",
            "Returns entries monitored by a program with this name",
            "MedicationKnowledge.monitoringProgram.name",
            "Opioid-Safety",
        ),
        token(
            "monitoring-program-type",
            "Returns entries monitored under a program of this type",
            "MedicationKnowledge.monitoringProgram.type",
            "http://example.org/program-types|safety",
        ),
        SearchParam(
            "monograph",
            "reference",
            "Returns entries with this associated documentation (a DocumentReference or Media)",
            "MedicationKnowledge.monograph.source",
            mono_match,
            mono_present,
            _REFERENCE,
            targets=monograph_targets,
            chain=mono_chain,
            chain_targets={
                t: _registry_of(t) for t in monograph_targets if t in _MODELED
            },
            sort=mono_sort,
            example="DocumentReference/320001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "monograph-type",
            "Returns entries with a monograph of this category",
            "MedicationKnowledge.monograph.type",
            "http://snomed.info/sct|374273001",
        ),
        string_token(
            "source-cost",
            "Returns entries whose price information comes from this source or owner",
            "MedicationKnowledge.cost.source",
            "Wholesaler-A",
        ),
        SearchParam(
            "status",
            "token",
            f"active | inactive | entered-in-error (system {_STATUS_SYSTEM})",
            "MedicationKnowledge.status",
            _status_match,
            lambda ctx: P.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="active",
        ),
    ]

    return SearchRegistry(
        resource_type="MedicationKnowledge",
        params={p.name: p for p in params},
        # Σ elements in the R4 MedicationKnowledge definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {"code", "status", "manufacturer", "amount", "synonym"}
        ),
        # MedicationKnowledge has no element with minimum cardinality 1 at the top level.
        mandatory_elements=frozenset(),
        includes=(
            IncludeTarget(
                "MedicationKnowledge",
                "manufacturer",
                "Organization",
                _include_column("manufacturer", "Organization"),
            ),
            *(
                IncludeTarget(
                    "MedicationKnowledge",
                    "monograph",
                    t,
                    _include_child(_R, t, _R.param == "monograph"),
                )
                for t in monograph_targets
                if t in _MODELED
            ),
            *(
                IncludeTarget(
                    "MedicationKnowledge",
                    "ingredient",
                    t,
                    _include_child(_R, t, _R.param == "ingredient"),
                )
                for t in ingredient_targets
                if t in _MODELED
            ),
        ),
        # Nothing points back at a MedicationKnowledge through a search parameter.
        revincludes=(),
        default_sort=lambda: [P.medication_knowledge_id.desc()],
    )

"""
FHIR R4 Measure search parameters
(https://www.hl7.org/fhir/R4/measure.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`, `_include` and the
OpenAPI docs all come from measure_search() below. Measure is a
definitional resource: the parameters are strings, uris, dates, tokens held in one shared table,
a quantity over an Age/Range-like value (`context-quantity`), two composites that pair a
useContext's code with its value (same `slot`, as in Observation) and the five relatedArtifact
reference parameters, which read canonical URLs (as Procedure's `instantiates-canonical` does).

Each parameter's SQL reads only the search index (MeasureModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
import re
from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased

from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchParam,
    SearchRegistry,
)
from app.fhir.search.composite import split_composite
from app.fhir.search.quantity import quantity_range_match
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    string_match,
    token_match,
    token_text_match,
    uri_match,
)
from app.fhir.search.values import like_escape, parse_of_type, parse_token
from app.models.measure import (
    REFERENCE_PARAMS,
    TOKEN_PARAMS,
    MeasureContextQuantity,
    MeasureIdentifier,
    MeasureModel,
    MeasureReference,
    MeasureStatus,
    MeasureToken,
)
from app.models.shared.resource_types import ANY_RESOURCE_TYPES
from app.repository._measure_report_revinclude import (
    measure_measure_report_revincludes,
)
from app.repository._search_targets import MODELED

M = MeasureModel
_I = MeasureIdentifier
_Tk = MeasureToken
_R = MeasureReference
_Q = MeasureContextQuantity

# Measure.status is a `code` from the R4 publication-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
_ABSOLUTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

# Every rebuilt resource type this server can chain through and `_include`: derived from
# RESOURCE_REGISTRY by app/repository/_search_targets.py, so there is no list to keep here.
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
    return exists(select(literal(1)).where(model.measure_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.measure_pk == M.id, *conditions)
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
    return M.measure_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the publication-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing (rather
    than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == MeasureStatus(token.code)
    except ValueError:
        return false()


def _version_match(value, modifier, ctx):
    """`version` is a token search over a plain string: it matches the code only, so a
    `system|code` value (a string has no system) never matches."""
    token = parse_token(value)
    if token.system is not None or token.code is None:
        return false()
    return M.version == token.code


def _date_match(value, modifier, ctx):
    # Measure.date is a dateTime, possibly partial (`2026`, `2026-02`): matched as the range
    # it covers.
    return period_match(M.date_start, M.date_end, value)


def _effective_match(value, modifier, ctx):
    return period_match(M.effective_start, M.effective_end, value)


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


def _string_param(raw, norm):
    """(match, present, sort) for a 0..1 string held as a raw + normalized column pair."""

    def match(value, modifier, ctx):
        return string_match(raw, norm, value, modifier)

    return match, lambda ctx: raw.is_not(None), lambda: norm


def _context_quantity_match(value, modifier, ctx):
    # useContext.value as Quantity | Range: R4 range semantics over [low, high].
    return _exists(
        _Q,
        quantity_range_match(
            _Q.quantity_low,
            _Q.quantity_high,
            _Q.quantity_system,
            _Q.quantity_code,
            _Q.quantity_unit,
            value,
        ),
    )


def _composite(value_kind: str):
    """`context-type$<value>`: some useContext (slot) has a code matching the first part *and* a
    value of `value_kind` (`concept` -> the `context` token, `quantity` -> the quantity row)
    matching the second part. Both rows must carry the same `slot`, which is what stops the code
    of one useContext pairing with the value of another. (`,` ORs several composites - the parser
    splits it; `$` splits the parts here.)"""

    def match(value, modifier, ctx):
        code_part, value_part = split_composite(value, 2)
        code = aliased(_Tk)
        if value_kind == "concept":
            other = aliased(_Tk)
            paired = exists(
                select(literal(1))
                .where(
                    other.measure_pk == M.id,
                    other.slot == code.slot,
                    other.param == "context",
                    token_match(other.system, other.code, value_part),
                )
                .correlate(M, code)
            )
        else:
            other = aliased(_Q)
            paired = exists(
                select(literal(1))
                .where(
                    other.measure_pk == M.id,
                    other.slot == code.slot,
                    quantity_range_match(
                        other.quantity_low,
                        other.quantity_high,
                        other.quantity_system,
                        other.quantity_code,
                        other.quantity_unit,
                        value_part,
                    ),
                )
                .correlate(M, code)
            )
        return exists(
            select(literal(1))
            .where(
                code.measure_pk == M.id,
                code.param == "context-type",
                token_match(code.system, code.code, code_part),
                paired,
            )
            .correlate(M)
        )

    return match


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _reference_param(param: str):
    """(match, present, chain, sort) for one of the relatedArtifact reference parameters held in
    the shared reference table, selected by its `param` value. The stored value is a canonical
    URL: `url|version` is found by itself and by the unversioned `url`, and a relative
    `Type/<id>` matches by its resolved type and id."""

    def match(value, modifier, ctx):
        conditions = [
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                ANY_RESOURCE_TYPES,
                str,
            )
        ]
        if modifier is None and "|" not in value and _ABSOLUTE.match(value):
            conditions.append(
                _R.reference_reference.like(like_escape(value) + "|%", escape="\\")
            )
        return _exists(_R, _R.param == param, or_(*conditions))

    def present(ctx):
        return _exists(_R, _R.param == param)

    def chain(target, inner, ctx):
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(_referenced(target, inner, ctx)),
        )

    return (
        match,
        present,
        chain,
        lambda: _child_sort(_R.reference_reference, _R, _R.param == param),
    )


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return list(
        (
            await session.execute(
                select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
            )
        )
        .scalars()
        .all()
    )


def _include_reference(param: str, resource_type: str):
    """_include of a relatedArtifact reference parameter: the rebuilt resources of
    `resource_type` named by a relative `Type/<id>` canonical."""

    async def fetch(session, ctx, rows):
        ids = select(_R.reference_id).where(
            _R.measure_pk.in_({r.id for r in rows}),
            _R.param == param,
            _R.reference_type == resource_type,
            _R.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def _revinclude_self(param: str):
    """_revinclude=Measure:<param> on Measure itself: the definitions
    that name a matched definition as their predecessor, successor, ..."""

    async def fetch(session, ctx, rows):
        ids = {r.measure_id for r in rows}
        pks = select(_R.measure_pk).where(
            _R.param == param,
            _R.reference_type == "Measure",
            _R.reference_id.in_(ids),
        )
        return list(
            (
                await session.execute(
                    select(M).where(M.tenant_id == ctx.tenant_id, M.id.in_(pks))
                )
            )
            .scalars()
            .all()
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Measure rows."""
    from app.fhir.mappers.measure import to_fhir_measure
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Measure",
            lambda r: r.measure_id,
            to_fhir_measure,
            "measures",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_STRING = frozenset({"exact", "contains", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})
_TEXT_DOC = {
    "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
}
_COMPOSITE_DOC = (
    " Composite: `<context-type>$<value>`, the two parts separated by `$` (a literal `$` is"
    " written `\\$`), both taken from the same useContext. Takes no modifiers and cannot be"
    " sorted."
)


@cache
def measure_search() -> SearchRegistry:
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

    def string(name, description, expression, raw, norm, example):
        match, present, sort = _string_param(raw, norm)
        return SearchParam(
            name,
            "string",
            description,
            expression,
            match,
            present,
            _STRING,
            sort=sort,
            example=example,
        )

    def reference(name, description, expression):
        match, present, chain, sort = _reference_param(name)
        reachable = [t for t in ANY_RESOURCE_TYPES if t in _MODELED]
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            frozenset({"identifier", "missing"}),
            targets=ANY_RESOURCE_TYPES,
            chain=chain,
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example="Library/1",
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public measure id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.measure_id,
            example="560001",
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
        reference(
            "composed-of",
            "What resource is being referenced",
            "Measure.relatedArtifact.where(type='composed-of').resource(Any)",
        ),
        token(
            "context",
            "A use context assigned to the measure",
            "(Measure.useContext.value as CodeableConcept)",
            "http://snomed.info/sct|35489007",
        ),
        SearchParam(
            "context-quantity",
            "quantity",
            "A quantity- or range-valued use context assigned to the measure",
            "(Measure.useContext.value as Quantity) | (Measure.useContext.value as Range)",
            _context_quantity_match,
            lambda ctx: _exists(_Q),
            frozenset({"missing"}),
            sort=lambda: _child_sort(_Q.quantity_low, _Q),
            example="ge5|http://unitsofmeasure.org|mg",
        ),
        token(
            "context-type",
            "A type of use context assigned to the measure",
            "Measure.useContext.code",
            "http://terminology.hl7.org/CodeSystem/usage-context-type|focus",
        ),
        SearchParam(
            "context-type-quantity",
            "composite",
            "A use context type and quantity- or range-based value assigned to the measure"
            + _COMPOSITE_DOC,
            "Measure.useContext",
            _composite("quantity"),
            lambda ctx: true(),
            frozenset(),
            example="age$ge18|http://unitsofmeasure.org|a",
        ),
        SearchParam(
            "context-type-value",
            "composite",
            "A use context type and value assigned to the measure" + _COMPOSITE_DOC,
            "Measure.useContext",
            _composite("concept"),
            lambda ctx: true(),
            frozenset(),
            example="focus$http://snomed.info/sct|35489007",
        ),
        SearchParam(
            "date",
            "date",
            "The measure publication date",
            "Measure.date",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        reference(
            "depends-on",
            "What resource is being referenced",
            "Measure.relatedArtifact.where(type='depends-on').resource | Measure.library(Library, Any)",
        ),
        reference(
            "derived-from",
            "What resource is being referenced",
            "Measure.relatedArtifact.where(type='derived-from').resource(Any)",
        ),
        string(
            "description",
            "The description of the measure",
            "Measure.description",
            M.description,
            M.description_norm,
            "depression",
        ),
        SearchParam(
            "effective",
            "date",
            "The time during which the measure is intended to be in use",
            "Measure.effectivePeriod",
            _effective_match,
            lambda ctx: or_(
                M.effective_start.is_not(None), M.effective_end.is_not(None)
            ),
            sort=lambda: M.effective_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "External identifier for the measure",
            "Measure.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            _IDENTIFIER,
            sort=lambda: _child_sort(_I.value, _I),
            example="https://fhir-server.dev/fhir/identifier-system/measure-id|PHQ-9",
            modifier_docs=_TEXT_DOC,
        ),
        token(
            "jurisdiction",
            "Intended jurisdiction for the measure",
            "Measure.jurisdiction",
            "urn:iso:std:iso:3166|US",
        ),
        string(
            "name",
            "Computationally friendly name of the measure",
            "Measure.name",
            M.name,
            M.name_norm,
            "PHQ",
        ),
        reference(
            "predecessor",
            "What resource is being referenced",
            "Measure.relatedArtifact.where(type='predecessor').resource(Any)",
        ),
        string(
            "publisher",
            "Name of the publisher of the measure",
            "Measure.publisher",
            M.publisher,
            M.publisher_norm,
            "Example",
        ),
        SearchParam(
            "status",
            "token",
            "The current status of the measure",
            "Measure.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="active",
        ),
        reference(
            "successor",
            "What resource is being referenced",
            "Measure.relatedArtifact.where(type='successor').resource(Any)",
        ),
        string(
            "title",
            "The human-friendly name of the measure",
            "Measure.title",
            M.title,
            M.title_norm,
            "Patient Health",
        ),
        token(
            "topic",
            "Topics associated with the module",
            "Measure.topic",
            "http://terminology.hl7.org/CodeSystem/definition-topic|treatment",
        ),
        SearchParam(
            "url",
            "uri",
            "The uri that identifies the measure",
            "Measure.url",
            lambda v, m, ctx: uri_match(M.url, v, m),
            lambda ctx: M.url.is_not(None),
            frozenset({"above", "below", "missing"}),
            sort=lambda: M.url,
            example="https://fhir-server.dev/fhir/Measure/phq-9",
            modifier_docs={
                "below": "`:below` — stored URLs that start with the value.",
                "above": "`:above` — stored URLs that are a prefix of the value.",
            },
        ),
        SearchParam(
            "version",
            "token",
            "The business version of the measure",
            "Measure.version",
            _version_match,
            lambda ctx: M.version.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.version,
            example="1.0",
        ),
    ]

    # Keep the declared token parameters and the model's TOKEN_PARAMS in step.
    assert {"topic", "context", "context-type", "jurisdiction"} == set(TOKEN_PARAMS)
    assert set(REFERENCE_PARAMS) == {
        "composed-of",
        "depends-on",
        "derived-from",
        "predecessor",
        "successor",
    }

    return SearchRegistry(
        resource_type="Measure",
        params={p.name: p for p in params},
        # Σ elements in the R4 Measure definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "url",
                "identifier",
                "version",
                "name",
                "title",
                "status",
                "experimental",
                "date",
                "publisher",
                "contact",
                "description",
                "useContext",
                "jurisdiction",
                "effectivePeriod",
                "disclaimer",
                "scoring",
                "compositeScoring",
                "type",
                "riskAdjustment",
                "rateAggregation",
                "rationale",
                "clinicalRecommendationStatement",
                "improvementNotation",
                "definition",
                "guidance",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status"}),
        # The relatedArtifact canonical URLs that name a rebuilt resource by a relative
        # `Type/<id>` can be `_include`d.
        includes=tuple(
            IncludeTarget("Measure", param, t, _include_reference(param, t))
            for param in REFERENCE_PARAMS
            for t in ANY_RESOURCE_TYPES
            if t in _MODELED
        ),
        revincludes=tuple(
            IncludeTarget(
                "Measure",
                param,
                "Measure",
                _revinclude_self(param),
                reverse=True,
            )
            for param in REFERENCE_PARAMS
        )
        # A MeasureReport names its measure by canonical URL.
        + measure_measure_report_revincludes(lambda r: r.url, lambda r: r.measure_id),
        default_sort=lambda: [M.measure_id.desc()],
    )

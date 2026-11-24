"""
FHIR R4 Flag search parameters (https://www.hl7.org/fhir/R4/flag.html#search) plus the common
`_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from flag_search() below. Same
arrangement as app.repository.goal.search (multi-target references held as columns, `patient`
narrowed to Patients).

R4 defines no `status`, `category` or `code` search parameter for Flag, so none is declared.

Each parameter's SQL reads only the search index (FlagModel's columns and child tables, see its
docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.flag import (
    AUTHOR_TYPES,
    ENCOUNTER_TYPES,
    SUBJECT_TYPES,
    FlagIdentifier,
    FlagModel,
)
from app.repository._search_targets import MODELED

P = FlagModel
_I = FlagIdentifier

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
    return exists(select(literal(1)).where(model.flag_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.flag_pk == P.id, *conditions)
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
    return P.flag_id == int(token.code)


def _date_match(value, modifier, ctx):
    # Flag.period is a Period: matched as the range it covers (a flag with no period never
    # matches).
    return period_match(P.period_start, P.period_end, value)


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


# -- references held as columns: subject / patient, encounter, author ------------------------


def _column_ref(prefix: str, targets: tuple[str, ...], narrowed: str | None = None):
    """(match, present, chain, sort) for a Reference held as `{prefix}_*` columns on the flag
    row. `narrowed` restricts a multi-target element to one type (`patient` is `subject`
    resolved to a Patient)."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )
    # `is_not(None)` keeps `NOT present` (`:missing=true`) from going NULL for a row whose
    # reference has no resolved type (a logical, identifier-only reference).
    type_filter = (type_.is_not(None), type_ == narrowed) if narrowed else ()

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return and_(
                token_condition(ident_system, ident_value, parse_token(value)),
                *type_filter,
            )
        # `modifier` is a target type (subject:Patient=10001) or None; a bare id with several
        # targets is ambiguous and is rejected by reference_target().
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return and_(or_(ref.is_not(None), ident_value.is_not(None)), *type_filter)

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


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
    """_include of a reference held as columns (`subject`, `encounter`, `author`): the rows of
    `resource_type` these flags point at."""

    async def fetch(session, ctx, flags):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(f, id_)
            for f in flags
            if getattr(f, type_) == resource_type and getattr(f, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def revinclude_flags_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Flag:subject / :patient / :encounter / :author - flags whose column reference
    points at one of these rows (matched on the public id `key(row)`). Declared on the registry
    of each target type."""

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


def _register_kind() -> None:
    """How the search engine identifies and renders Flag rows."""
    from app.fhir.mappers.flag import to_fhir_flag
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Flag", lambda f: f.flag_id, to_fhir_flag, "flags"))


# -- registry ------------------------------------------------------------------------------

_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def flag_search() -> SearchRegistry:
    _register_kind()

    def column_ref(
        name, description, expression, prefix, targets, example, narrowed=None
    ):
        match, present, chain, sort = _column_ref(prefix, targets, narrowed)
        reachable = [t for t in targets if t in _MODELED]
        return SearchParam(
            name,
            "reference",
            description,
            expression,
            match,
            present,
            _REFERENCE,
            targets=targets,
            chain=chain,
            chain_targets={t: _registry_of(t) for t in reachable},
            sort=sort,
            example=example,
            modifier_docs=_IDENTIFIER_DOC,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public flag id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.flag_id,
            example="450001",
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
        column_ref(
            "author",
            "Flag creator",
            "Flag.author",
            "author",
            AUTHOR_TYPES,
            "Practitioner/30001",
        ),
        SearchParam(
            "date",
            "date",
            "Time period when flag is active",
            "Flag.period",
            _date_match,
            lambda ctx: or_(P.period_start.is_not(None), P.period_end.is_not(None)),
            sort=lambda: P.period_start,
            example="ge2026-01-01",
        ),
        column_ref(
            "encounter",
            "Alert relevant during encounter",
            "Flag.encounter",
            "encounter",
            ENCOUNTER_TYPES,
            "Encounter/20001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Business identifier",
            "Flag.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:flags|F-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        column_ref(
            "patient",
            "The identity of a subject to list flags for",
            "Flag.subject.where(resolve() is Patient)",
            "subject",
            ("Patient",),
            "10001",
            narrowed="Patient",
        ),
        column_ref(
            "subject",
            "The identity of a subject to list flags for",
            "Flag.subject",
            "subject",
            SUBJECT_TYPES,
            "Patient/10001",
        ),
    ]

    def column_includes(param, prefix, targets):
        return tuple(
            IncludeTarget("Flag", param, t, _include_column(prefix, t))
            for t in targets
            if t in _MODELED
        )

    return SearchRegistry(
        resource_type="Flag",
        params={p.name: p for p in params},
        # Σ elements in the R4 Flag definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "status",
                "category",
                "code",
                "subject",
                "period",
                "encounter",
                "author",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status", "code", "subject"}),
        includes=(
            IncludeTarget(
                "Flag", "patient", "Patient", _include_column("subject", "Patient")
            ),
            *column_includes("subject", "subject", SUBJECT_TYPES),
            *column_includes("encounter", "encounter", ENCOUNTER_TYPES),
            *column_includes("author", "author", AUTHOR_TYPES),
        ),
        # Nothing points back at a Flag through a search parameter.
        revincludes=(),
        default_sort=lambda: [P.flag_id.desc()],
    )

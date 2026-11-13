"""
SQL condition builders for each FHIR R4 search parameter type. Each takes
the index column(s) a parameter is stored in plus one search value and
returns a SQLAlchemy boolean clause; app.fhir.search.build ORs them across
a comma-separated value list and applies `:not` / `:missing` generically.

String columns come in (raw, normalized) pairs: the raw value answers
`:exact` (case- and accent-sensitive), the normalized one (see
values.normalize) answers the default starts-with and `:contains`.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

from sqlalchemy import and_, bindparam, case, exists, false, func, literal, or_, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import Boolean, String

from app.core.filters import array_contains

from .errors import SearchError
from .values import (
    ReferenceValue,
    Token,
    like_escape,
    normalize,
    parse_date,
    parse_reference_value,
    parse_token,
    unescape,
)

# ── string ───────────────────────────────────────────────────────────────────


def _like_pattern(value: str, modifier: str | None) -> str:
    pattern = like_escape(normalize(unescape(value)))
    return f"%{pattern}%" if modifier == "contains" else f"{pattern}%"


def string_match(raw_col, norm_col, value: str, modifier: str | None):
    """Default: the field equals or starts with the value, ignoring case
    and accents. `:contains`: anywhere in the field. `:exact`: the whole
    field, case- and accent-sensitive."""
    if modifier == "exact":
        return raw_col == unescape(value)
    return norm_col.like(_like_pattern(value, modifier), escape="\\")


class ArrayAnyLike(ColumnElement):
    """Boolean clause: some element of an ARRAY(String) column is LIKE
    `pattern` (ESCAPE '\\'). Postgres form here; the SQLite form used by the
    test suite is registered in tests/conftest.py (same arrangement as
    app.core.filters.ArrayContainsILike)."""

    inherit_cache = True

    def __init__(self, column, pattern: str):
        super().__init__()
        self.column = column
        self.pattern = pattern
        self.type = Boolean()


@compiles(ArrayAnyLike)
def _array_any_like_default(element, compiler, **kw):
    col_sql = compiler.process(element.column, **kw)
    pattern_sql = compiler.process(bindparam(None, element.pattern), **kw)
    return (
        f"EXISTS (SELECT 1 FROM unnest({col_sql}) AS _aal(value) "
        f"WHERE _aal.value LIKE {pattern_sql} ESCAPE '\\')"
    )


class ArrayAggregate(ColumnElement):
    """min() or max() over the elements of an ARRAY(String) column — the
    _sort key of a list-valued string (e.g. Organization.alias). NULL for an
    empty or NULL array. Postgres form here; the SQLite form used by the test
    suite is registered in tests/conftest.py."""

    inherit_cache = True

    def __init__(self, column, aggregate: str):
        super().__init__()
        assert aggregate in ("min", "max")
        self.column = column
        self.aggregate = aggregate
        self.type = String()


@compiles(ArrayAggregate)
def _array_aggregate_default(element, compiler, **kw):
    col_sql = compiler.process(element.column, **kw)
    return f"(SELECT {element.aggregate}(_aag.value) FROM unnest({col_sql}) AS _aag(value))"


def earliest(a, b, *, descending: bool):
    """The value of `a` / `b` that comes first in the sort order (the smaller
    ascending, the larger descending), ignoring a NULL side. Written as a
    CASE so it behaves the same on Postgres and SQLite (whose two-argument
    min()/max() return NULL if either side is NULL, unlike Postgres'
    LEAST/GREATEST)."""
    a, b = func.coalesce(a, b), func.coalesce(b, a)
    first = (a >= b) if descending else (a <= b)
    return case((first, a), else_=b)


def array_string_match(raw_col, norm_col, value: str, modifier: str | None):
    """string_match() over every element of an ARRAY(String) column pair."""
    if modifier == "exact":
        return array_contains(raw_col, unescape(value))
    return ArrayAnyLike(norm_col, _like_pattern(value, modifier))


# ── token ────────────────────────────────────────────────────────────────────


def token_match(system_col, code_col, value: str):
    """`code` (any system) | `system|code` | `|code` (no system) |
    `system|` (any code in the system). Codes match exactly."""
    return token_condition(system_col, code_col, parse_token(value))


def token_condition(system_col, code_col, token: Token):
    conditions = []
    if token.system is not None:
        conditions.append(system_col == token.system if token.system else system_col.is_(None))
    if token.code is not None:
        conditions.append(code_col == token.code)
    return and_(*conditions) if conditions else literal(True)


def token_text_match(norm_cols, value: str):
    """`:text` — the text associated with the code (CodeableConcept.text,
    Coding.display, Identifier.type.text) as a default string search."""
    pattern = _like_pattern(value, None)
    return or_(*(c.like(pattern, escape="\\") for c in norm_cols))


# ── token: terminology-backed modifiers (:in, :not-in, :above, :below) ───────

_cte_names = itertools.count(1)


def _terminology_models():
    from app.models.terminology.terminology import (
        TerminologyCodeSystem,
        TerminologyConcept,
        TerminologyRelationship,
        TerminologyValueSet,
        TerminologyValueSetConcept,
    )

    return (
        TerminologyCodeSystem,
        TerminologyConcept,
        TerminologyRelationship,
        TerminologyValueSet,
        TerminologyValueSetConcept,
    )


def valueset_member(system_col, code_col, value: str):
    """`:in` — the coding is in the ValueSet (by canonical URL, optionally
    `|version`, or `ValueSet/<id>`), per its stored expansion in the
    terminology service. An unknown ValueSet matches nothing."""
    CodeSystem, Concept, _, ValueSet, ValueSetConcept = _terminology_models()
    ref = unescape(value)
    if ref.startswith("ValueSet/") and ref[9:].isdigit():
        vs_condition = ValueSet.id == int(ref[9:])
    else:
        url, _, version = ref.partition("|")
        vs_condition = and_(ValueSet.canonical_url == url, *([ValueSet.version == version] if version else []))
    return exists(
        select(literal(1))
        .select_from(ValueSetConcept)
        .join(ValueSet, ValueSet.id == ValueSetConcept.value_set_id)
        .join(Concept, Concept.id == ValueSetConcept.concept_id)
        .join(CodeSystem, CodeSystem.id == Concept.code_system_id)
        .where(
            vs_condition,
            ValueSetConcept.active.is_not(False),
            CodeSystem.canonical_url == system_col,
            Concept.code == code_col,
        )
    )


def subsumption_member(system_col, code_col, value: str, direction: str, max_depth: int = 50):
    """`:below` — the coding is the given code or subsumed by it (a
    descendant over IS-A); `:above` — the given code or one of its
    ancestors. Walks the terminology service's IS-A hierarchy."""
    CodeSystem, Concept, Relationship, _, _ = _terminology_models()
    token = parse_token(value)
    if token.code is None:
        raise SearchError(value, f"':{direction}' needs a code: [system|]code.")
    seed_concept, seed_system = aliased(Concept), aliased(CodeSystem)
    anchor = (
        select(seed_concept.id.label("cid"), literal(0).label("depth"))
        .join(seed_system, seed_system.id == seed_concept.code_system_id)
        .where(
            seed_concept.code == token.code,
            *([seed_system.canonical_url == token.system] if token.system else []),
        )
    )
    tree = anchor.cte(name=f"subsumption_{next(_cte_names)}", recursive=True)
    rel = aliased(Relationship)
    if direction == "below":
        step = select(rel.child_concept_id, tree.c.depth + 1).where(rel.parent_concept_id == tree.c.cid)
    else:
        step = select(rel.parent_concept_id, tree.c.depth + 1).where(rel.child_concept_id == tree.c.cid)
    tree = tree.union_all(step.where(rel.relationship_type == "is-a", tree.c.depth < max_depth))
    member, member_system = aliased(Concept), aliased(CodeSystem)
    return exists(
        select(literal(1))
        .select_from(tree)
        .join(member, member.id == tree.c.cid)
        .join(member_system, member_system.id == member.code_system_id)
        .where(member_system.canonical_url == system_col, member.code == code_col)
    )


def coded_token_match(system_col, code_col, value: str, modifier: str | None, text_cols=()):
    """Token match for a Coding/CodeableConcept-backed parameter, with every
    token modifier it supports (`:not`/`:not-in` arrive here positive)."""
    if modifier == "text":
        return token_text_match(text_cols, value)
    if modifier == "in":
        return valueset_member(system_col, code_col, value)
    if modifier in ("above", "below"):
        return subsumption_member(system_col, code_col, value, modifier)
    return token_match(system_col, code_col, value)


# ── date ─────────────────────────────────────────────────────────────────────


def date_match(column, value: str, now: datetime | None = None):
    """A date/instant column against a prefixed date value. The value is a
    range ([low, high) at its written precision); for a point-in-time
    target t (an instant column):

      eq  low <= t < high          ne  not eq
      gt  t >= high                lt  t < low
      ge  t >= low                 le  t < high
      sa  t >= high (starts after) eb  t < low (ends before)
      ap  within the range widened by 10% of its distance from now
    """
    d = parse_date(value)
    lo, hi = d.low, d.high
    if d.prefix == "eq":
        return and_(column >= lo, column < hi)
    if d.prefix == "ne":
        return or_(column < lo, column >= hi)
    if d.prefix in ("gt", "sa"):
        return column >= hi
    if d.prefix in ("lt", "eb"):
        return column < lo
    if d.prefix == "ge":
        return column >= lo
    if d.prefix == "le":
        return column < hi
    # ap
    now = now or datetime.now(UTC)
    slack = abs(now - lo) * 0.1
    return and_(column >= lo - slack, column < hi + slack)


# ── reference ────────────────────────────────────────────────────────────────


def reference_target(value: str, modifier: str | None, targets: tuple[str, ...], fhir_base: str | None):
    """Resolve a reference search value to (resource_type, public_id) for
    a local match, or ReferenceValue(url=...) for an absolute URL this
    server doesn't own, or None when it can't match anything (wrong type,
    non-numeric id — every local id here is the numeric public sequence id)."""
    ref = parse_reference_value(value, fhir_base)
    if ref.url is not None:
        return ref
    rtype = ref.resource_type or modifier or (targets[0] if len(targets) == 1 else None)
    if rtype is None:
        raise SearchError(value, f"Reference '{value}' is ambiguous: give a type ({', '.join(targets)}).")
    if (modifier and rtype != modifier) or rtype not in targets or not (ref.resource_id or "").isdigit():
        return None
    return ReferenceValue(rtype, ref.resource_id)


def reference_match(
    type_col, id_col, raw_col, value: str, modifier: str | None, ctx, targets: tuple[str, ...], type_enum
):
    """`[id]` / `[type]/[id]` / `[url]`, optionally restricted by a
    `:[type]` modifier. Local references match on the resolved
    (type, public id) columns; external absolute URLs on the stored raw
    reference string."""
    ref = reference_target(value, modifier, targets, ctx.fhir_base)
    if ref is None:
        return false()
    if ref.url is not None:
        return raw_col == ref.url
    return and_(type_col == type_enum(ref.resource_type), id_col == int(ref.resource_id))

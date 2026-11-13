"""
SearchRequest -> SQL: WHERE conditions and ORDER BY, resolved through a
resource's SearchRegistry.

Combination rules (R4 §2.21.1.2): a comma-separated list of values ORs
(`name=a,b`); repeating a parameter ANDs (`name=a&name=b`). `:not` /
`:not-in` match the resources for which *no* value matches the positive
form, which includes resources with no value at all. `:missing=true`
matches resources without a value for the parameter.
"""

from __future__ import annotations

from sqlalchemy import and_, false, func, not_, or_

from .params import (
    NEGATING_MODIFIERS,
    Clause,
    MultiValueSort,
    SearchContext,
    SearchRegistry,
    SearchRequest,
)


def clause_condition(registry: SearchRegistry, clause: Clause, ctx: SearchContext):
    param = registry.params[clause.name]

    if clause.chain is not None:
        target_registry = param.chain_targets[clause.modifier]()
        inner = clause_condition(target_registry, clause.chain, ctx)
        return param.chain(clause.modifier, inner, ctx)

    if clause.modifier == "missing":
        present = param.present(ctx)
        return not_(present) if clause.values[0] == "true" else present

    if clause.modifier in ("above", "below") and param.type == "reference":
        return or_(*(param.hierarchy(v, clause.modifier, ctx) for v in clause.values))

    negate = clause.modifier in NEGATING_MODIFIERS
    modifier = NEGATING_MODIFIERS[clause.modifier] if negate else clause.modifier
    matched = or_(*(param.match(v, modifier, ctx) for v in clause.values))
    if not negate:
        return matched
    # `:not` matches resources with no value too. A comparison on a NULL
    # column is NULL, and NOT NULL is still NULL (not true), so treat
    # "unknown" as "no match" before negating.
    return not_(func.coalesce(matched, false()))


def where_conditions(registry: SearchRegistry, request: SearchRequest, ctx: SearchContext) -> list:
    return [clause_condition(registry, c, ctx) for c in request.clauses]


def order_by(registry: SearchRegistry, request: SearchRequest, tiebreak) -> list:
    """`_sort` (comma list, `-` for descending) then a unique tiebreaker so
    paging is stable; the registry's default order when `_sort` is absent."""
    if not request.sort:
        return registry.default_sort() if registry.default_sort else [tiebreak.desc()]
    clauses = []
    for name, desc in request.sort:
        key = registry.params[name].sort()
        if isinstance(key, MultiValueSort):
            key = key.descending if desc else key.ascending
        # Resources without a value sort last either way.
        clauses.append(key.desc().nulls_last() if desc else key.asc().nulls_last())
    clauses.append(tiebreak.asc())
    return clauses


def all_of(conditions: list):
    return and_(*conditions) if conditions else None

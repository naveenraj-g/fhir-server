"""
Running a parsed search against a resource's table: the page of matches,
the total, and `_include` / `_revinclude` — shared by every resource on the
search engine, so a resource's repository `search()` is one call.

Includes cross resource types (`Location?_include=Location:organization`
returns Organizations; `Organization?_revinclude=Location:organization`
returns Locations), so the engine needs to know, per resource type, how to
identify a row and how to render it as FHIR. Each resource registers that
once as a ResourceKind (see register_kind); the router uses the same
registry to render included rows and build their fullUrl.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select

from .build import order_by, where_conditions
from .params import SearchContext, SearchRegistry, SearchRequest


@dataclass(frozen=True)
class ResourceKind:
    """How the engine handles rows of one resource type."""

    resource_type: str
    # The row's public id (what FHIR calls Resource.id).
    public_id: Callable[[Any], Any]
    # The row as a FHIR resource dict.
    to_fhir: Callable[[Any], dict]
    # Path segment of the resource's endpoint under the FHIR base
    # (`organizations`), for entry fullUrls.
    path: str


_KINDS: dict[str, ResourceKind] = {}


def register_kind(kind: ResourceKind) -> None:
    _KINDS[kind.resource_type] = kind


def kind_of(resource_type: str) -> ResourceKind:
    return _KINDS[resource_type]


async def execute_search(
    session,
    *,
    model,
    registry: SearchRegistry,
    request: SearchRequest,
    ctx: SearchContext,
    tiebreak,
) -> tuple[list, int | None, list[tuple[str, Any]]]:
    """(matches for this page, total or None, included (type, row) pairs).

    Always scoped to ctx.tenant_id via `model.tenant_id`. `tiebreak` is a
    unique column (the public id) appended to the ORDER BY so paging is
    stable. The total is skipped for `_total=none`; `_summary=count` /
    `_count=0` fetches no rows at all."""
    conditions = [model.tenant_id == ctx.tenant_id, *where_conditions(registry, request, ctx)]

    rows: list = []
    if request.summary != "count" and request.count > 0:
        stmt = (
            select(model)
            .where(*conditions)
            .order_by(*order_by(registry, request, tiebreak))
            .offset(request.offset)
            .limit(request.count)
        )
        rows = list((await session.execute(stmt)).scalars().all())

    total = None
    if request.total != "none" or request.summary == "count":
        count_stmt = select(func.count()).select_from(model).where(*conditions)
        total = (await session.execute(count_stmt)).scalar_one()

    included = await resolve_includes(session, ctx, request, registry.resource_type, rows)
    return rows, total, included


async def resolve_includes(
    session,
    ctx: SearchContext,
    request: SearchRequest,
    match_type: str,
    matches: list,
    max_rounds: int = 10,
) -> list[tuple[str, Any]]:
    """Apply `_include` / `_revinclude`. Round 1 applies every requested
    include to the matches; each later round applies only the `:iterate`
    ones, to what the previous round added — up to max_rounds levels
    (R4 leaves the depth to the server). A resource is returned once: never
    twice, and never as an include when it is already a match."""
    specs = [*request.include, *request.revinclude]
    if not specs:
        return []

    seen = {(match_type, kind_of(match_type).public_id(r)) for r in matches}
    included: list[tuple[str, Any]] = []
    frontier: list[tuple[str, Any]] = [(match_type, r) for r in matches]

    for round_no in range(max_rounds):
        added: list[tuple[str, Any]] = []
        for spec in specs:
            target = spec.definition
            if round_no > 0 and not spec.iterate:
                continue
            if target.fetch is None:
                continue  # target type not stored here (e.g. Endpoint)
            sources = [row for rtype, row in frontier if rtype == target.applies_to]
            if not sources:
                continue
            for row in await target.fetch(session, ctx, sources):
                key = (target.yields, kind_of(target.yields).public_id(row))
                if key not in seen:
                    seen.add(key)
                    added.append((target.yields, row))
        if not added:
            break
        included.extend(added)
        frontier = added
    return included

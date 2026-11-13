"""
Search-parameter definitions and the parsed form of a search request.

A resource declares its FHIR search parameters once, as a `SearchRegistry`
of `SearchParam`s. That one registry drives everything: parsing and
validating the query (app.fhir.search.parser), building the SQL WHERE /
ORDER BY (app.fhir.search.build), and the OpenAPI documentation of the
search endpoint (app.fhir.search.openapi) — so what is documented is
exactly what is accepted.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

ParamType = Literal["string", "token", "reference", "date", "number", "quantity", "uri", "special"]

# Modifiers each parameter type can carry in R4 (search.html §2.21.1.4).
# `missing` applies to every type. A parameter lists the subset it really
# supports; anything else is rejected (400), as R4 requires.
MODIFIERS_BY_TYPE: dict[str, frozenset[str]] = {
    "string": frozenset({"exact", "contains", "missing"}),
    "token": frozenset({"text", "not", "above", "below", "in", "not-in", "of-type", "missing"}),
    "reference": frozenset({"identifier", "above", "below", "missing"}),  # + :[type]
    "date": frozenset({"missing"}),
    "number": frozenset({"missing"}),
    "quantity": frozenset({"missing"}),
    "uri": frozenset({"above", "below", "missing"}),
    # `special` parameters (Location `near`) define their own syntax and
    # take no modifiers.
    "special": frozenset(),
}

# Modifiers that invert the match: the resource matches when *no* value
# matches the (positive) form of the modifier.
NEGATING_MODIFIERS = {"not": None, "not-in": "in"}


@dataclass(frozen=True)
class SearchContext:
    """Per-request facts a condition builder may need."""

    tenant_id: str
    # This server's FHIR base URL (e.g. http://host/api/fhir/v1), so an
    # absolute reference to one of its own resources matches the relative
    # form.
    fhir_base: str | None = None


# build(value, modifier, ctx) -> SQL condition for ONE value (OR'd across a
# comma-separated list by the caller). `modifier` is the positive form
# (`not` arrives as None, `not-in` as `in`) — negation is applied generically.
MatchBuilder = Callable[[str, "str | None", SearchContext], Any]


@dataclass(frozen=True)
class MultiValueSort:
    """_sort key for a parameter with several values per resource (a name
    plus aliases, several identifiers, ...). R4: "the sort is based on the
    item in the set of multiple parameters that comes earliest in the
    specified sort order" — the smallest value ascending, the largest
    descending — so the key depends on the direction."""

    ascending: Any
    descending: Any


@dataclass(frozen=True)
class SearchParam:
    name: str
    type: ParamType
    description: str
    # FHIRPath expression from the R4 spec, for documentation.
    expression: str
    match: MatchBuilder
    # SQL condition: "the resource has a value for this parameter" (:missing).
    present: Callable[[SearchContext], Any]
    modifiers: frozenset[str] = frozenset({"missing"})
    # Reference parameters: allowed target types (for `:[type]` and bare ids)
    # and, per chainable target type, the registry chained params resolve
    # against plus a builder wrapping the target-side condition.
    targets: tuple[str, ...] = ()
    chain: Callable[[str, Any, SearchContext], Any] | None = None
    chain_targets: dict[str, Callable[[], SearchRegistry]] = field(default_factory=dict)
    # Hierarchy (:above / :below) builder for a reference parameter that
    # points along a strict hierarchy (Organization.partOf).
    hierarchy: Callable[[str, str, SearchContext], Any] | None = None
    # _sort key, if sortable: an ORDER BY expression, or a MultiValueSort
    # for a parameter that can hold several values per resource.
    sort: Callable[[], Any] | None = None
    example: str | None = None
    # Extra free-text documentation per modifier, for OpenAPI.
    modifier_docs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class IncludeTarget:
    """One `_include` or `_revinclude` this resource supports, named the
    FHIR way — `source:param` is the reference search parameter `param` on
    resource type `source`, pointing at `target`:

      _include=Organization:partof     source=Organization, target=Organization
      _revinclude=Location:organization source=Location,     target=Organization

    `fetch(session, ctx, rows)` loads what the include adds for a batch of
    rows it applies to — for an _include, the `source` rows' referenced
    `target` rows; for a _revinclude (`reverse=True`), the `source` rows
    that reference the given `target` rows. None means the target isn't
    stored on this server (e.g. Endpoint): accepted, adds nothing."""

    source: str
    param: str
    target: str
    fetch: Callable[..., Any] | None = None
    reverse: bool = False

    @property
    def applies_to(self) -> str:
        """Resource type of the rows this include starts from."""
        return self.target if self.reverse else self.source

    @property
    def yields(self) -> str:
        """Resource type of the rows it adds."""
        return self.source if self.reverse else self.target


@dataclass(frozen=True)
class SearchRegistry:
    resource_type: str
    params: dict[str, SearchParam]
    # Element names in the resource marked Σ (isSummary) in the R4 spec,
    # beyond the always-summary id/meta/implicitRules.
    summary_elements: frozenset[str]
    # Elements with min cardinality >= 1 (kept by _summary=text and _elements).
    mandatory_elements: frozenset[str] = frozenset()
    includes: tuple[IncludeTarget, ...] = ()
    revincludes: tuple[IncludeTarget, ...] = ()
    default_sort: Callable[[], list] | None = None
    # Extra `Bundle.entry.search.extension` for a match, computed from the
    # request and the matched row — e.g. Location `near`'s distance
    # (http://hl7.org/fhir/StructureDefinition/location-distance).
    entry_extensions: Callable[[SearchRequest, Any], list[dict] | None] | None = None


# ── Parsed request ───────────────────────────────────────────────────────────


@dataclass
class Clause:
    """One search parameter occurrence. `values` is the comma-split OR list,
    still escaped for `|`/`$` (unescaping is type-specific). A chained
    parameter (`partof.name=x`) has `chain` set to the clause evaluated on
    the referenced resource; the values then live on the innermost clause."""

    key: str
    name: str
    modifier: str | None
    values: list[str]
    chain: Clause | None = None


@dataclass
class IncludeSpec:
    """One requested `_include`/`_revinclude`, resolved to the registry's
    IncludeTarget (which knows how to fetch it)."""

    definition: IncludeTarget
    iterate: bool


@dataclass
class SearchRequest:
    clauses: list[Clause] = field(default_factory=list)
    count: int = 50
    offset: int = 0
    sort: list[tuple[str, bool]] = field(default_factory=list)  # (param, descending)
    total: Literal["none", "estimate", "accurate"] = "accurate"
    summary: Literal["true", "text", "data", "count", "false"] | None = None
    elements: list[str] | None = None
    include: list[IncludeSpec] = field(default_factory=list)
    revinclude: list[IncludeSpec] = field(default_factory=list)
    # (key, value) pairs that were applied — rebuilt into the Bundle's self link.
    applied: list[tuple[str, str]] = field(default_factory=list)
    # Parameters ignored under lenient handling (reported as an outcome entry).
    ignored: list[str] = field(default_factory=list)

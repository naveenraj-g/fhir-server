"""
Query string -> SearchRequest, validated against a resource's
SearchRegistry (R4 search.html).

Unknown parameters follow R4's lenient default — ignored, and reported back
as an `outcome` entry in the Bundle — unless the client sent
`Prefer: handling=strict`, which turns them into a 400. A *known* parameter
with an unsupported modifier or a malformed value is always a 400: R4 says
servers SHALL reject those.
"""

from __future__ import annotations

from .errors import SearchError, UnsupportedSearchError
from .params import (
    MODIFIERS_BY_TYPE,
    Clause,
    IncludeSpec,
    SearchRegistry,
    SearchRequest,
)
from .values import split_escaped

# R4 common search parameters this server does not implement. They are
# treated exactly like unknown parameters (lenient: ignored + reported).
UNSUPPORTED_COMMON = frozenset(
    {"_tag", "_profile", "_security", "_source", "_text", "_content", "_list", "_has", "_type", "_filter"}
)

RESULT_PARAMS = frozenset(
    {
        "_count",
        "_offset",
        "_sort",
        "_total",
        "_summary",
        "_elements",
        "_include",
        "_revinclude",
        "_contained",
        "_containedType",
        "_format",
        "_pretty",
    }
)

_JSON_FORMATS = {"json", "application/json", "application/fhir+json", "application/json+fhir"}

_ALL_MODIFIERS = frozenset().union(*MODIFIERS_BY_TYPE.values())


class _Unknown(Exception):
    def __init__(self, key: str):
        self.key = key


def parse_prefer_strict(prefer_header: str | None) -> bool:
    """`Prefer: handling=strict` (RFC 7240, R4 §2.21.1.1)."""
    if not prefer_header:
        return False
    for token in prefer_header.split(","):
        k, _, v = token.strip().partition("=")
        if k.strip().lower() == "handling" and v.strip().strip('"').lower() == "strict":
            return True
    return False


def parse_search(
    items: list[tuple[str, str]],
    registry: SearchRegistry,
    *,
    strict: bool = False,
    default_count: int = 50,
    max_count: int = 200,
) -> SearchRequest:
    req = SearchRequest(count=default_count)
    for key, value in items:
        if value == "":
            # R4: a parameter with no value is ignored.
            continue
        base = key.split(":", 1)[0]
        if base in RESULT_PARAMS:
            _apply_result_param(req, registry, key, base, value, max_count)
            req.applied.append((key, value))
            continue
        if base == "_query":
            # R4: servers SHALL refuse an unrecognized _query.
            raise UnsupportedSearchError(key, f"Named query '{value}' is not supported.")
        try:
            clause = _parse_clause(registry, key, value)
        except _Unknown as exc:
            if strict:
                raise UnsupportedSearchError(
                    exc.key,
                    f"Unknown or unsupported search parameter '{exc.key}' for {registry.resource_type}.",
                ) from None
            req.ignored.append(key)
            continue
        if clause is not None:
            req.clauses.append(clause)
            req.applied.append((key, value))

    if req.summary == "text" and (req.include or req.revinclude):
        raise SearchError("_summary", "_include/_revinclude cannot be combined with _summary=text.")
    return req


# ── search parameters ────────────────────────────────────────────────────────


def _parse_clause(registry: SearchRegistry, key: str, value: str) -> Clause | None:
    head, _, rest = key.partition(".")
    name, _, modifier = head.partition(":")
    modifier = modifier or None
    if name in UNSUPPORTED_COMMON:
        raise _Unknown(key)
    param = registry.params.get(name)
    if param is None:
        raise _Unknown(key)

    if rest:
        # Chained parameter: partof.name=x / partof:Organization.name=x
        if param.type != "reference":
            raise SearchError(key, f"'{name}' is not a reference parameter; it can't be chained.")
        if modifier and modifier not in param.targets:
            raise SearchError(key, f"'{modifier}' is not a target type of '{name}' ({', '.join(param.targets)}).")
        target = modifier
        if target is None:
            if len(param.targets) != 1:
                raise SearchError(key, f"Chaining '{name}' needs a target type: {name}:[type].{rest}.")
            target = param.targets[0]
        factory = param.chain_targets.get(target)
        if factory is None or param.chain is None:
            raise UnsupportedSearchError(
                key, f"Chaining through '{name}' to {target} is not supported: {target} is not searchable on this server."
            )
        try:
            inner = _parse_clause(factory(), rest, value)
        except _Unknown as exc:
            raise UnsupportedSearchError(key, f"Unknown chained parameter '{exc.key}' on {target}.") from None
        if inner is None:
            return None
        return Clause(key=key, name=name, modifier=target, values=[], chain=inner)

    if modifier is not None:
        is_type_modifier = param.type == "reference" and modifier[:1].isupper()
        if is_type_modifier:
            if modifier not in param.targets:
                raise SearchError(key, f"'{modifier}' is not a target type of '{name}' ({', '.join(param.targets)}).")
        elif modifier not in param.modifiers:
            if modifier in _ALL_MODIFIERS:
                raise UnsupportedSearchError(key, f"Modifier ':{modifier}' is not supported on '{name}'.")
            raise SearchError(key, f"Unknown modifier ':{modifier}' on '{name}'.")

    values = [v for v in split_escaped(value, ",") if v != ""]
    if not values:
        return None
    if modifier == "missing" and (len(values) != 1 or values[0] not in ("true", "false")):
        raise SearchError(key, f"':missing' takes 'true' or 'false', not '{value}'.")
    return Clause(key=key, name=name, modifier=modifier, values=values)


# ── result parameters ────────────────────────────────────────────────────────


def _int(key: str, value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise SearchError(key, f"'{key}' must be a non-negative integer, not '{value}'.") from None
    if n < 0:
        raise SearchError(key, f"'{key}' must be a non-negative integer, not '{value}'.")
    return n


def _one_of(key: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise SearchError(key, f"'{key}' must be one of {', '.join(allowed)}, not '{value}'.")
    return value


def _apply_result_param(
    req: SearchRequest, registry: SearchRegistry, key: str, base: str, value: str, max_count: int
) -> None:
    modifier = key[len(base) + 1 :] if ":" in key else None
    if modifier and base not in ("_include", "_revinclude"):
        raise SearchError(key, f"'{base}' takes no modifier.")

    if base == "_count":
        n = _int(key, value)
        # R4: servers SHALL NOT return more than requested; they may return fewer.
        req.count = min(n, max_count)
        if n == 0:
            req.summary = "count"
    elif base == "_offset":
        req.offset = _int(key, value)
    elif base == "_total":
        req.total = _one_of(key, value, ("none", "estimate", "accurate"))
    elif base == "_summary":
        req.summary = _one_of(key, value, ("true", "text", "data", "count", "false"))
    elif base == "_elements":
        req.elements = [e.strip() for e in value.split(",") if e.strip()]
    elif base == "_sort":
        req.sort = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            desc = part.startswith("-")
            name = part[1:] if desc else part
            param = registry.params.get(name)
            if name == "_score":
                raise UnsupportedSearchError(key, "Sorting by _score (relevance) is not supported.")
            if param is None:
                raise SearchError(key, f"Unknown sort parameter '{name}' for {registry.resource_type}.")
            if param.sort is None:
                raise UnsupportedSearchError(key, f"Sorting by '{name}' is not supported.")
            req.sort.append((name, desc))
    elif base in ("_include", "_revinclude"):
        if modifier not in (None, "iterate"):
            raise UnsupportedSearchError(key, f"Modifier ':{modifier}' is not supported on {base} (use :iterate).")
        supported = registry.includes if base == "_include" else registry.revincludes
        specs = _parse_includes(key, value, supported, iterate=modifier == "iterate", reverse=base == "_revinclude")
        (req.include if base == "_include" else req.revinclude).extend(specs)
    elif base == "_contained":
        if _one_of(key, value, ("false", "true", "both")) != "false":
            raise UnsupportedSearchError(key, "Searching contained resources is not supported.")
    elif base == "_containedType":
        if _one_of(key, value, ("container", "contained")) != "container":
            raise UnsupportedSearchError(key, "Returning contained resources is not supported.")
    elif base == "_format":
        if value not in _JSON_FORMATS:
            raise UnsupportedSearchError(key, f"Only JSON is supported (_format={value}).")
    # _pretty: accepted, no effect (responses are compact JSON).


def _parse_includes(key, value, supported, *, iterate: bool, reverse: bool) -> list[IncludeSpec]:
    if value == "*":
        return [IncludeSpec(t, iterate) for t in supported]
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise SearchError(key, f"Invalid {key} '{value}': expected SourceType:searchParam[:targetType].")
    source, param = parts[0], parts[1]
    target = parts[2] if len(parts) == 3 else None
    for t in supported:
        if t.source == source and t.param == param and (target is None or target == t.target):
            return [IncludeSpec(t, iterate)]
    allowed = ", ".join(f"{t.source}:{t.param}" for t in supported) or "none"
    raise UnsupportedSearchError(key, f"{key}={value} is not supported (supported: {allowed}).")

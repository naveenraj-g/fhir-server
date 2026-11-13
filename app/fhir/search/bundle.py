"""
Searchset Bundle assembly (R4 bundle.html / search.html §2.21.1.6):
`total`, paging links (`self` — the parameters actually applied — `first`,
`previous`, `next`, `last`), one entry per resource with `fullUrl` and
`search.mode` (`match` | `include` | `outcome`), and `_summary` /
`_elements` subsetting (subsetted resources are tagged SUBSETTED).
"""

from __future__ import annotations

import copy
from urllib.parse import urlencode

from .params import SearchRegistry, SearchRequest

SUBSETTED_TAG = {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationValue",
    "code": "SUBSETTED",
    "display": "Resource encoded in summary mode",
}

# Resource-level elements that are always part of a summary (R4 Resource:
# id, meta and implicitRules are Σ).
_BASE_SUMMARY = frozenset({"resourceType", "id", "meta", "implicitRules"})


def _tag_subsetted(resource: dict) -> dict:
    meta = dict(resource.get("meta") or {})
    tags = [t for t in meta.get("tag") or [] if t.get("code") != "SUBSETTED"]
    meta["tag"] = [*tags, SUBSETTED_TAG]
    resource["meta"] = meta
    return resource


def subset(resource: dict, request: SearchRequest, registry: SearchRegistry, *, match: bool) -> dict:
    """Apply `_summary` (every entry) and `_elements` (match entries)."""
    mode = request.summary
    keep: frozenset[str] | None = None
    if mode == "true":
        keep = _BASE_SUMMARY | registry.summary_elements
    elif mode == "text":
        keep = _BASE_SUMMARY | {"text"} | registry.mandatory_elements
    elif mode == "data":
        keep = frozenset(k for k in resource if k != "text")
    elif match and request.elements is not None and mode in (None, "false"):
        keep = _BASE_SUMMARY | registry.mandatory_elements | frozenset(request.elements)
    if keep is None or keep >= set(resource):
        return resource
    out = {k: copy.deepcopy(v) for k, v in resource.items() if k in keep}
    return _tag_subsetted(out)


def _link(url: str, items: list[tuple[str, str]], count: int, offset: int) -> str:
    params = [(k, v) for k, v in items if k not in ("_count", "_offset")]
    params += [("_count", str(count)), ("_offset", str(offset))]
    return f"{url}?{urlencode(params)}"


def paging_links(url: str, request: SearchRequest, total: int | None, returned: int) -> list[dict]:
    count, offset = request.count, request.offset
    links = [{"relation": "self", "url": _link(url, request.applied, count, offset)}]
    if request.summary == "count" or count == 0:
        return links
    links.append({"relation": "first", "url": _link(url, request.applied, count, 0)})
    if offset > 0:
        links.append({"relation": "previous", "url": _link(url, request.applied, count, max(offset - count, 0))})
    has_next = (offset + count < total) if total is not None else returned >= count
    if has_next:
        links.append({"relation": "next", "url": _link(url, request.applied, count, offset + count)})
    if total is not None:
        last = max(((total - 1) // count) * count, 0) if total else 0
        links.append({"relation": "last", "url": _link(url, request.applied, count, last)})
    return links


def ignored_outcome(request: SearchRequest, resource_type: str) -> dict | None:
    if not request.ignored:
        return None
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "warning",
                "code": "not-supported",
                "diagnostics": f"Unknown or unsupported search parameter '{key}' for {resource_type} was ignored.",
                "expression": [key],
            }
            for key in request.ignored
        ],
    }


def searchset_bundle(
    *,
    registry: SearchRegistry,
    request: SearchRequest,
    url: str,
    matches: list[dict],
    includes: list[dict],
    total: int | None,
    full_url,
    match_extensions: list[list[dict] | None] | None = None,
) -> dict:
    """`full_url(resource)` gives each entry's absolute URL.
    `match_extensions`, parallel to `matches`, adds `search.extension` to
    a match entry (e.g. Location `near`'s location-distance)."""
    entries = []
    if request.summary != "count":
        for i, r in enumerate(matches):
            search: dict = {"mode": "match"}
            extensions = match_extensions[i] if match_extensions else None
            if extensions:
                search["extension"] = extensions
            entries.append(
                {"fullUrl": full_url(r), "resource": subset(r, request, registry, match=True), "search": search}
            )
        entries += [
            {"fullUrl": full_url(r), "resource": subset(r, request, registry, match=False), "search": {"mode": "include"}}
            for r in includes
        ]
    outcome = ignored_outcome(request, registry.resource_type)
    if outcome:
        entries.append({"resource": outcome, "search": {"mode": "outcome"}})

    bundle: dict = {"resourceType": "Bundle", "type": "searchset"}
    if total is not None:
        bundle["total"] = total
    bundle["link"] = paging_links(url, request, total, len(matches))
    if entries:
        bundle["entry"] = entries
    return bundle

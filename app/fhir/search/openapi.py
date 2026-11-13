"""
OpenAPI documentation of a search endpoint, generated from the same
SearchRegistry the parser validates against — every parameter, every
supported modifier (as its own `name:modifier` query parameter, so MCP
callers can discover them), and the result parameters.
"""

from __future__ import annotations

from .params import SearchParam, SearchRegistry

R4_SEARCH = "https://www.hl7.org/fhir/R4/search.html"

_TYPE_DOCS = {
    "string": (
        "FHIR `string` search: matches when the field equals or STARTS WITH the value, ignoring case and "
        "accents (`name=gen` matches 'General Hospital', `name=hopital` matches 'Hôpital')."
    ),
    "token": "FHIR `token` search: `code`, `system|code`, `|code` (no system) or `system|` (any code in system). Codes match exactly.",
    "reference": (
        "FHIR `reference` search: `[id]`, `[type]/[id]` or an absolute URL "
        "(an absolute URL on this server matches its relative form)."
    ),
    "date": (
        "FHIR `date` search: `[prefix]YYYY[-MM[-DD[Thh:mm[:ss[.fff]][Z|±hh:mm]]]]`, matched at the precision written "
        "(`2024-03` = all of March 2024). Prefixes: eq (default), ne, gt, lt, ge, le, sa (starts after), "
        "eb (ends before), ap (approximately, ±10%). Repeat the parameter for a range: "
        "`ge2024-01-01&...=lt2025-01-01`."
    ),
}

_COMBINING = (
    " Comma-separated values are OR'd (`a,b`); repeating the parameter ANDs. "
    "Escape a literal `,` `|` `$` or `\\` with a backslash."
)

_MODIFIER_DOCS = {
    "exact": "`:exact` — the whole field equals the value, case- and accent-sensitive.",
    "contains": "`:contains` — the value appears anywhere in the field (case/accent-insensitive).",
    "missing": "`:missing=true` — resources with no value for this parameter; `:missing=false` — resources that have one.",
    "not": "`:not` — resources with no matching code (includes resources with no value at all).",
    "text": "`:text` — string search (starts-with, case/accent-insensitive) on the code's text/display instead of the code.",
    "in": "`:in` — the code is in the given ValueSet (canonical URL, `url|version` or `ValueSet/<id>`), per the terminology service.",
    "not-in": "`:not-in` — no code is in the given ValueSet.",
    "below": "`:below` — the code, or any code it subsumes (IS-A descendants in the terminology service): `[system|]code`.",
    "above": "`:above` — the code, or any code that subsumes it (IS-A ancestors in the terminology service): `[system|]code`.",
    "of-type": "`:of-type` — identifier of a given type: `type-system|type-code|value` (all three required).",
    "identifier": "`:identifier` — matches Reference.identifier as a token: `[system|]value`.",
}


def _param(
    name: str,
    description: str,
    *,
    array: bool = True,
    example: str | None = None,
    enum: list[str] | None = None,
) -> dict:
    schema: dict = {"type": "array", "items": {"type": "string"}} if array else {"type": "string"}
    if enum:
        schema["enum"] = enum
    p: dict = {
        "name": name,
        "in": "query",
        "required": False,
        "description": description,
        "schema": schema,
    }
    if array:
        p["style"] = "form"
        p["explode"] = True
    if example is not None:
        p["example"] = [example] if array else example
    return p


def _search_params(param: SearchParam) -> list[dict]:
    head = f"{param.description} (R4 expression: `{param.expression}`). " + _TYPE_DOCS.get(param.type, "") + _COMBINING
    mods = sorted(m for m in param.modifiers if m != "missing")
    if "missing" in param.modifiers:
        mods.append("missing")
    extra = []
    if param.type == "reference" and param.targets:
        extra.append(f"`:{param.targets[0]}` — restrict to that target type (value is the bare id).")
    if param.chain_targets:
        targets = ", ".join(param.chain_targets)
        extra.append(
            f"Chaining: `{param.name}.<param>=value` applies any {targets} search parameter (with its modifiers) "
            f"to the referenced resource, e.g. `{param.name}.name=Acme`, `{param.name}.{param.name}.name=Acme`."
        )
    lines = [param.modifier_docs.get(m) or _MODIFIER_DOCS[m] for m in mods] + extra
    docs = (" Modifiers: " + " ".join(lines)) if lines else " No modifiers."
    out = [_param(param.name, head + docs, example=param.example)]
    for m in mods:
        desc = param.modifier_docs.get(m) or _MODIFIER_DOCS[m]
        if m == "missing":
            out.append(_param(f"{param.name}:missing", f"{param.name} with {desc}", array=False, enum=["true", "false"]))
        else:
            out.append(_param(f"{param.name}:{m}", f"{param.name} with {desc}"))
    if param.type == "reference":
        for t in param.targets:
            out.append(_param(f"{param.name}:{t}", f"{param.name} restricted to {t} references; value is the {t} id."))
    return out


def search_parameters(registry: SearchRegistry, max_count: int, default_count: int) -> list[dict]:
    """Every query parameter the search endpoint accepts, for
    `openapi_extra={"parameters": ...}`."""
    params: list[dict] = []
    for p in registry.params.values():
        params += _search_params(p)

    sortable = ", ".join(n for n, p in registry.params.items() if p.sort)
    includes = ", ".join(f"{i.source}:{i.param}" for i in registry.includes) or "none"
    revincludes = ", ".join(f"{i.source}:{i.param}" for i in registry.revincludes) or "none"
    params += [
        _param(
            "_count",
            f"Page size (default {default_count}, max {max_count}; larger values are capped). `_count=0` returns only the total.",
            array=False,
            example=str(default_count),
        ),
        _param("_offset", "Number of matches to skip (paging; the Bundle's next/previous links carry it).", array=False, example="0"),
        _param(
            "_sort",
            f"Comma-separated sort parameters, `-` prefix for descending. Sortable: {sortable}. "
            "Default: newest first (`-_id`).",
            array=False,
            example="-_lastUpdated",
        ),
        _param(
            "_total",
            "`accurate` (default) counts every match; `none` skips the count (Bundle.total omitted); `estimate` = accurate.",
            array=False,
            enum=["accurate", "estimate", "none"],
        ),
        _param(
            "_summary",
            "`true` — summary elements only (" + ", ".join(sorted(registry.summary_elements)) + "); "
            "`text` — id, meta, narrative; `data` — everything but the narrative; `count` — total only, no entries; "
            "`false` (default) — the full resource. Subsetted resources carry the SUBSETTED meta tag.",
            array=False,
            enum=["true", "text", "data", "count", "false"],
        ),
        _param(
            "_elements",
            "Comma-separated top-level elements to return (id and meta are always included), e.g. `name,identifier`.",
            array=False,
        ),
        _param(
            "_include",
            f"Also return resources the matches reference: {includes}, or `*`. `_include:iterate` repeats it on included resources.",
        ),
        _param("_include:iterate", f"Iterative _include: {includes} applied again to each included resource."),
        _param(
            "_revinclude",
            f"Also return resources that reference the matches: {revincludes}, or `*`. `_revinclude:iterate` repeats it.",
        ),
        _param("_revinclude:iterate", f"Iterative _revinclude: {revincludes} applied again to each included resource."),
        _param("_contained", "Only `false` (default) is supported.", array=False, enum=["false"]),
        _param("_containedType", "Only `container` (default) is supported.", array=False, enum=["container"]),
        _param(
            "_format",
            "Only JSON is supported; anything else (e.g. `xml`) is 406 Not Acceptable.",
            array=False,
            enum=["json", "application/json", "application/fhir+json"],
        ),
        {
            "name": "Prefer",
            "in": "header",
            "required": False,
            "description": (
                "`handling=strict` rejects unknown search parameters with 400; by default (`handling=lenient`) they "
                "are ignored and reported in an OperationOutcome entry (search.mode=outcome)."
            ),
            "schema": {"type": "string", "enum": ["handling=lenient", "handling=strict"]},
        },
    ]
    return params


def search_description(registry: SearchRegistry) -> str:
    names = ", ".join(f"`{n}`" for n in registry.params)
    return (
        f"FHIR R4 search ({R4_SEARCH}) over {registry.resource_type}. Search parameters: {names} — each with the "
        "modifiers listed on it. A comma-separated value list ORs; repeating a parameter ANDs. A known parameter "
        "with an unsupported modifier or a malformed value is rejected with 400 (OperationOutcome). Unknown "
        "parameters are ignored and reported in an `outcome` entry, or rejected with `Prefer: handling=strict`. "
        "Not supported (ignored as unknown): `_tag`, `_profile`, `_security`, `_source`, `_text`, `_content`, "
        "`_list`, `_has`, `_type`, `_filter`; `_query` is always rejected. Returns a searchset Bundle with "
        "`total`, `link` (self/first/previous/next/last) and entries carrying `fullUrl` and `search.mode`."
    )

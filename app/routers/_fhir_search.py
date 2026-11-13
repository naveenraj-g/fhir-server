"""
Shared HTTP glue for FHIR search endpoints (resources on app.fhir.search):
reading the raw parameters of `GET [type]?...` / `POST [type]/_search`,
and turning a search result into the searchset Bundle response.

Query parameters are read raw — FHIR parameter names carry modifiers
(`name:exact`), chains (`partof.name`) and repeat to AND, none of which
FastAPI's per-name Query() declarations can express. Each resource's
OpenAPI parameter list is generated from its SearchRegistry instead
(app.fhir.search.openapi).
"""

from __future__ import annotations

from urllib.parse import parse_qsl

from fastapi import Request

from app.core.content_negotiation import fhir_response
from app.fhir.search import SearchRegistry, SearchRequest, parse_prefer_strict, searchset_bundle
from app.fhir.search.execute import kind_of


def get_query(request: Request) -> list[tuple[str, str]]:
    """GET search: the query string's (name, value) pairs, in order."""
    return request.query_params.multi_items()


async def post_query(request: Request) -> list[tuple[str, str]]:
    """POST _search: query-string parameters plus the
    application/x-www-form-urlencoded body, combined (R4 allows both)."""
    body = (await request.body()).decode("utf-8")
    return request.query_params.multi_items() + parse_qsl(body, keep_blank_values=True)


def strict_handling(request: Request) -> bool:
    """`Prefer: handling=strict` — unknown parameters become a 400."""
    return parse_prefer_strict(request.headers.get("prefer"))


def search_urls(request: Request, route_name: str) -> tuple[str, str]:
    """(search_url, fhir_base). search_url is the GET search route itself
    (with its trailing slash — paging links must hit it directly, not via a
    redirect); fhir_base is the API root (`.../api/fhir/v1`) that entry
    fullUrls and absolute-reference matching are built against."""
    search_url = str(request.url_for(route_name))
    fhir_base = search_url.rstrip("/").rsplit("/", 1)[0]
    return search_url, fhir_base


def searchset_response(
    *,
    registry: SearchRegistry,
    search_request: SearchRequest,
    search_url: str,
    fhir_base: str,
    rows: list,
    total: int | None,
    included: list[tuple[str, object]],
):
    """The searchset Bundle as an `application/fhir+json` response. Matches
    and included rows (of any resource type) are rendered through their
    registered ResourceKind."""
    match_kind = kind_of(registry.resource_type)

    def full_url(resource: dict) -> str:
        kind = kind_of(resource["resourceType"])
        return f"{fhir_base}/{kind.path}/{resource['id']}"

    extensions = None
    if registry.entry_extensions is not None:
        extensions = [registry.entry_extensions(search_request, row) for row in rows]

    bundle = searchset_bundle(
        registry=registry,
        request=search_request,
        url=search_url,
        matches=[match_kind.to_fhir(row) for row in rows],
        includes=[kind_of(rtype).to_fhir(row) for rtype, row in included],
        total=total,
        full_url=full_url,
        match_extensions=extensions,
    )
    return fhir_response(bundle)

"""
Resource-agnostic FHIR R4 search (https://www.hl7.org/fhir/R4/search.html).

A resource declares its search parameters once as a SearchRegistry
(params.py); from that one declaration this package parses and validates
the query (parser.py), builds the SQL (build.py, sql.py), assembles the
searchset Bundle (bundle.py) and documents the endpoint in OpenAPI
(openapi.py). Organization is the first resource on it — see
app/repository/organization/search.py.
"""

from .build import clause_condition, order_by, where_conditions
from .bundle import searchset_bundle
from .errors import SearchError, UnsupportedSearchError
from .params import (
    Clause,
    IncludeSpec,
    IncludeTarget,
    MultiValueSort,
    SearchContext,
    SearchParam,
    SearchRegistry,
    SearchRequest,
)
from .parser import parse_prefer_strict, parse_search
from .values import normalize

__all__ = [
    "Clause",
    "IncludeSpec",
    "IncludeTarget",
    "MultiValueSort",
    "SearchContext",
    "SearchError",
    "SearchParam",
    "SearchRegistry",
    "SearchRequest",
    "UnsupportedSearchError",
    "clause_condition",
    "normalize",
    "order_by",
    "parse_prefer_strict",
    "parse_search",
    "searchset_bundle",
    "where_conditions",
]

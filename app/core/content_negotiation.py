from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType

logger = get_logger(__name__)

FHIR_MEDIA_TYPE = "application/fhir+json"


def wants_fhir(request: Request) -> bool:
    """Return True when the client signals it wants a FHIR-formatted response."""
    accept = request.headers.get("accept", "")
    chose_fhir = FHIR_MEDIA_TYPE in accept
    # DEBUG only — the useful case is a client insisting it asked for FHIR and
    # getting plain JSON, which is always an Accept-header problem.
    logger.debug(
        "Content negotiated",
        extra={
            "event": "content.negotiated",
            "accept": accept,
            "format": "fhir" if chose_fhir else "plain",
        },
    )
    return chose_fhir


def format_response(
    fhir_data: dict, plain_data: dict, request: Request, status_code: int = 200
) -> JSONResponse:
    """
    Serialise and return either the FHIR or the plain JSON representation
    depending on the Accept header.

    Always returns a JSONResponse so that FastAPI skips response_model
    validation — the response_model decorators are kept for OpenAPI docs only.
    jsonable_encoder handles dates, Enum subclasses, Decimal, etc.

    status_code must be passed explicitly by the caller (e.g. 201 on create)
    — returning a Response instance makes FastAPI use ITS status code
    verbatim and ignore the route decorator's own status_code= entirely.
    """
    if wants_fhir(request):
        return JSONResponse(
            content=jsonable_encoder(fhir_data),
            media_type=FHIR_MEDIA_TYPE,
            status_code=status_code,
        )
    return JSONResponse(content=jsonable_encoder(plain_data), status_code=status_code)


def format_list_response(
    fhir_list: list, plain_list: list, request: Request, status_code: int = 200
) -> JSONResponse:
    if wants_fhir(request):
        return JSONResponse(
            content=jsonable_encoder(fhir_list),
            media_type=FHIR_MEDIA_TYPE,
            status_code=status_code,
        )
    return JSONResponse(content=jsonable_encoder(plain_list), status_code=status_code)


def format_paginated_response(
    fhir_list: list[dict],
    plain_list: list[dict],
    total: int,
    limit: int,
    offset: int,
    request: Request,
    status_code: int = 200,
) -> JSONResponse:
    """
    Return a paginated response in either plain-JSON or FHIR Bundle format.

    Plain JSON envelope:  { total, limit, offset, data: [...] }
    FHIR Bundle:          { resourceType: "Bundle", type: "searchset", total, entry: [{ resource: ... }] }
    """
    if wants_fhir(request):
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": total,
            "entry": [{"resource": r} for r in fhir_list],
        }
        return JSONResponse(
            content=jsonable_encoder(bundle),
            media_type=FHIR_MEDIA_TYPE,
            status_code=status_code,
        )
    return JSONResponse(
        content=jsonable_encoder(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": plain_list,
            }
        ),
        status_code=status_code,
    )


# ── FHIR-only responses ──────────────────────────────────────────────────────
# For resources stored Medplum-style (whole resource in a `content` JSONB
# column — Organization first): there is no plain representation to
# negotiate, so the Accept header isn't consulted at all.


class FHIRJSONResponse(JSONResponse):
    """JSONResponse with `application/fhir+json` as its media type. Use as a
    router's `default_response_class` so the OpenAPI spec advertises only
    the FHIR content type (FastAPI otherwise adds the default class's
    `application/json` next to whatever `responses=` declares)."""

    media_type = FHIR_MEDIA_TYPE


def fhir_response(data: dict, status_code: int = 200) -> JSONResponse:
    """A single FHIR resource as `application/fhir+json`. As with
    format_response(), status_code must be passed explicitly (e.g. 201)."""
    return FHIRJSONResponse(content=jsonable_encoder(data), status_code=status_code)

# ── Accept / _format for FHIR-only resources ─────────────────────────────────
# Medplum's approach: there is exactly one representation (FHIR R4 JSON), so
# it is sent whatever the client's Accept header says — no negotiation. The
# one exception is a client that has said it can ONLY take something we
# don't produce (XML, Turtle, ...): R4 (http.html#mime-type) has the server
# answer 406 Not Acceptable rather than send a format the client refused.
# `_format` overrides Accept when present, same rule.

# Media ranges that FHIR JSON satisfies. `application/json+fhir` is the
# DSTU2-era name some clients still send.
_JSON_RANGES = {
    "*/*",
    "application/*",
    "application/json",
    FHIR_MEDIA_TYPE,
    "application/json+fhir",
}
# _format short names / mime types that mean JSON.
_JSON_FORMATS = {"json", "application/json", FHIR_MEDIA_TYPE, "application/json+fhir"}


class NotAcceptableError(ApplicationError):
    """406 — the client accepts no format this server can produce."""

    def __init__(self, message: str):
        super().__init__(
            name="NotAcceptableError",
            message=message,
            status_code=406,
            code="NOT_ACCEPTABLE",
            issue_type=IssueType.NOT_SUPPORTED,
        )


def _accepts_json(accept: str) -> bool:
    """True when some media range in the Accept header (with q > 0) is
    satisfied by FHIR JSON. Parameters other than q (e.g. fhirVersion,
    charset) don't change the answer."""
    for part in accept.split(","):
        media, *params = (p.strip() for p in part.split(";"))
        if not media:
            continue
        q = 1.0
        for param in params:
            key, _, value = param.partition("=")
            if key.strip().lower() == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        if q > 0 and media.lower() in _JSON_RANGES:
            return True
    return False


def require_fhir_json(request: Request) -> None:
    """Router dependency for FHIR-only resources (Organization): let every
    request through — the response is FHIR JSON regardless — except one
    whose `_format` or Accept header rules JSON out, which gets a 406
    OperationOutcome. A missing/empty Accept means "anything" (RFC 9110)."""
    fmt = request.query_params.get("_format")
    if fmt is not None:
        if fmt.strip().lower() not in _JSON_FORMATS:
            raise NotAcceptableError(
                f"_format={fmt} is not supported; this server returns FHIR JSON only "
                f"({FHIR_MEDIA_TYPE})."
            )
        return  # an acceptable _format overrides Accept
    accept = request.headers.get("accept", "").strip()
    if accept and not _accepts_json(accept):
        raise NotAcceptableError(
            f"Accept: {accept} can't be satisfied; this server returns FHIR JSON only "
            f"({FHIR_MEDIA_TYPE})."
        )


# A searchset Bundle (with links, fullUrl, search.mode, _summary, ...) is
# built by app.fhir.search.bundle.searchset_bundle() and sent with
# fhir_response().

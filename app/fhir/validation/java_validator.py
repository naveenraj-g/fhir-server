"""Stopgap validation backend: delegates to the HL7 Java FHIR validator
sidecar (docker/fhir-validator/) over its REST API, instead of this
project's own fhir.schema.json structural check — see
docs/structure-definitions/12-three-layer-validation-architecture.md for why
this exists and what it trades off against `base_r4.py`'s native path.

Profile registration reads a country layer's StructureDefinition from the
fhir_profile DB table (behind FhirProfileService's cache-aside layer,
app/services/fhir_profile/core.py) instead of the file-based
app/fhir/profiling/ convention that stood in for it before that table
existed — dispatch.py is the caller that resolves which structure_definition
(if any) applies and passes it in here; this module no longer reads
anything off disk at validation time."""

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.errors.fhir_codes import IssueType

logger = get_logger(__name__)

# Tracks which (resource_type, layer) pairs this process has already POSTed
# to the sidecar's /profiles endpoint — registration is almost certainly
# held in the sidecar's in-memory validator context (not persisted), but is
# also almost certainly idempotent to repeat, so this cache only exists to
# avoid a redundant network round-trip per validation call, not for
# correctness. Separate from (and sitting in front of) FhirProfileService's
# own cache, which avoids the Postgres round-trip instead — this one avoids
# the sidecar round-trip.
_registered: set[str] = set()


def _client() -> httpx.AsyncClient:
    cfg = settings.fhir_validation.java_validator
    return httpx.AsyncClient(base_url=cfg.base_url, timeout=cfg.timeout_seconds)


async def _ensure_registered(
    resource_type: str, layer: str, structure_definition: dict
) -> None:
    key = f"{resource_type}:{layer}"
    if key in _registered:
        return
    async with _client() as client:
        resp = await client.post("/profiles", json=structure_definition)
        resp.raise_for_status()
    _registered.add(key)
    logger.info(
        "Registered profile with Java validator sidecar",
        extra={
            "event": "fhir_validation.profile_registered",
            "resource_type": resource_type,
            "layer": layer,
            "url": structure_definition.get("url"),
        },
    )


def _issues_to_errors(operation_outcome: dict) -> list[dict]:
    """Converts the sidecar's OperationOutcome into this project's own
    {"field", "message", "issue_type", "details"} shape — the same shape
    FhirValidationError's `errors` list expects — so callers never need to
    know which backend produced it.

    The sidecar already computes a precise, correct IssueType per issue
    (e.g. "invariant" for a constraint failure, confirmed against real
    org-1/org-2/org-3 test runs) — this function PRESERVES that value
    (mapped onto our own IssueType enum) and the issue's own `details`
    (CodeableConcept, when present) instead of discarding them, so the
    client-facing OperationOutcome ends up with the real code rather than
    a generic fallback. Only error/fatal severities become failures;
    warning/information (e.g. the base spec's own "should have narrative"
    best-practice rule) are logged, not surfaced as validation failures."""
    errors = []
    for issue in operation_outcome.get("issue", []):
        severity = issue.get("severity")
        message = issue.get("details", {}).get("text") or issue.get("diagnostics") or ""
        if severity in ("error", "fatal"):
            field = ".".join(issue.get("expression", [])) or "(root)"
            raw_code = issue.get("code")
            try:
                issue_type = IssueType(raw_code) if raw_code else None
            except ValueError:
                # The sidecar emitted a real HL7 code we don't have a member
                # for yet (e.g. a future CodeSystem addition) — fail open to
                # the caller's own default rather than erroring on a code
                # that's valid FHIR, just not yet mirrored into our enum.
                issue_type = None
            error = {"field": field, "message": message}
            if issue_type is not None:
                error["issue_type"] = issue_type
            if issue.get("details"):
                error["details"] = issue["details"]
            errors.append(error)
        elif severity == "warning":
            logger.info(
                "Java validator warning (not a validation failure)",
                extra={"event": "fhir_validation.java_warning", "detail": message},
            )
    return errors


async def check_profile_registers(structure_definition: dict) -> list[dict]:
    """POSTs `structure_definition` to the sidecar's /profiles endpoint to
    force snapshot generation and surface whatever the sidecar does catch,
    in the same {"field", "message"} shape validate_via_java() returns —
    used by the (future) profile authoring/activation write-path to reject
    a candidate country/organization profile before it's ever persisted,
    instead of unconditionally registering it the way _ensure_registered()
    does for an already-trusted, already-persisted profile.

    Caveat, confirmed empirically against the real sidecar: this is a
    best-effort check, not a guarantee that every illegal "child profile
    widens/contradicts its parent" case is rejected. The sidecar hard-fails
    on some malformed differentials (e.g. the zero-slice-member pattern
    this project hit earlier — see country_in.json's _comment_element_order)
    but silently accepted, in direct testing, both a differential
    referencing a field that doesn't exist and one widening a cardinality
    beyond its own baseDefinition — neither raised an error at registration
    or at a subsequent /validate call. Treat a clean return here as "the
    sidecar didn't object", not as "this profile is provably a legal
    narrowing of its parent"; a real narrowing-legality guarantee would
    need this project's own field-by-field comparison against the parent's
    resolved snapshot, which doesn't exist yet."""
    async with _client() as client:
        try:
            resp = await client.post("/profiles", json=structure_definition)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return _registration_error_to_errors(exc.response)
    return []


def _registration_error_to_errors(response: httpx.Response) -> list[dict]:
    try:
        body = response.json()
    except ValueError:
        return [
            {
                "field": "(root)",
                "message": response.text.strip() or f"HTTP {response.status_code}",
            }
        ]
    if isinstance(body, dict) and body.get("resourceType") == "OperationOutcome":
        errors = _issues_to_errors(body)
        if errors:
            return errors
    # Not an OperationOutcome (e.g. a plain Spring Boot error body) — fall
    # back to whatever text is available rather than silently returning no
    # errors for a genuinely non-2xx response.
    message = None
    if isinstance(body, dict):
        message = body.get("message") or body.get("error")
    return [{"field": "(root)", "message": message or f"HTTP {response.status_code}"}]


async def validate_via_java(
    resource_type: str,
    fhir_resource: dict,
    *,
    profile_url: str,
    layer: str | None = None,
    structure_definition: dict | None = None,
) -> list[dict]:
    """Validates `fhir_resource` (true FHIR JSON, same shape validate_base_r4()
    takes) against `profile_url` via the Java validator sidecar.

    `layer=None` (the default) means "plain base R4" — every base R4
    definition ships preloaded in the sidecar itself (confirmed via its own
    GET /profiles), so nothing needs registering first; this is also the
    only way validation can work at all for a resource_type this project
    hasn't authored a country profile for — there's no reason to ever fetch
    one, since the sidecar already has every resource's base definition
    built in.

    Pass an actual `layer` (e.g. "country_in") together with
    `structure_definition` (the real StructureDefinition dict, already
    resolved by dispatch.py from FhirProfileService) only for a profile this
    project authored itself, not preloaded anywhere — registered with the
    sidecar from that dict first if this process hasn't already."""
    if layer is not None:
        if structure_definition is None:
            raise ValueError("structure_definition is required when layer is set")
        await _ensure_registered(resource_type, layer, structure_definition)
    async with _client() as client:
        resp = await client.post(
            "/validate", params={"profile": profile_url}, json=fhir_resource
        )
        resp.raise_for_status()
        operation_outcome = resp.json()
    return _issues_to_errors(operation_outcome)

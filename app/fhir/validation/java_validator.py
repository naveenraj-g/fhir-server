"""Stopgap validation backend: delegates to the HL7 Java FHIR validator
sidecar (docker/fhir-validator/) over its REST API, instead of this
project's own fhir.schema.json structural check — see
docs/structure-definitions/12-three-layer-validation-architecture.md for why
this exists and what it trades off against `base_r4.py`'s native path.

Profile registration is file-backed for now (app/fhir/profiling/, see its
README) — a deliberate stand-in for the planned `fhir_profile` DB table, so
only `_ensure_registered()`'s file-read needs to change when that table
exists; nothing about registering with or calling the sidecar does.
"""

import json
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.errors.fhir_codes import IssueType

logger = get_logger(__name__)

_PROFILING_ROOT = Path(__file__).resolve().parent.parent / "profiling"

# Tracks which (resource_type, layer) pairs this process has already POSTed
# to the sidecar's /profiles endpoint — registration is almost certainly
# held in the sidecar's in-memory validator context (not persisted), but is
# also almost certainly idempotent to repeat, so this cache only exists to
# avoid a redundant network round-trip per validation call, not for
# correctness.
_registered: set[str] = set()


def _profile_path(resource_type: str, layer: str) -> Path:
    return _PROFILING_ROOT / resource_type.lower() / f"{layer}.json"


def profile_exists(resource_type: str, layer: str) -> bool:
    """Whether a `<resource_type>/<layer>.json` file exists under
    app/fhir/profiling/ — lets a caller (dispatch.py) check whether a given
    resource type has a country-layer profile before asking for it, since
    not every resource will have one from day one. Not every (resource_type,
    layer) pair is expected to exist; a missing one is a normal, silent
    "nothing more specific than base for this resource" case, not an error."""
    return _profile_path(resource_type, layer).is_file()


def _client() -> httpx.AsyncClient:
    cfg = settings.fhir_validation.java_validator
    return httpx.AsyncClient(base_url=cfg.base_url, timeout=cfg.timeout_seconds)


async def _ensure_registered(resource_type: str, layer: str) -> None:
    key = f"{resource_type}:{layer}"
    if key in _registered:
        return
    path = _profile_path(resource_type, layer)
    structure_definition = json.loads(path.read_text(encoding="utf-8"))
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


async def validate_via_java(
    resource_type: str,
    fhir_resource: dict,
    *,
    profile_url: str,
    layer: str | None = None,
) -> list[dict]:
    """Validates `fhir_resource` (true FHIR JSON, same shape validate_base_r4()
    takes) against `profile_url` via the Java validator sidecar.

    `layer=None` (the default) means "plain base R4" — every base R4
    definition ships preloaded in the sidecar itself (confirmed via its own
    GET /profiles), so nothing needs registering first; this is also the
    only way validation can work at all for a resource_type this project has
    no local base_fhir_r4.json for (i.e. everything except Organization
    today — there's no reason to ever author one, since the sidecar already
    has every resource's base definition built in).

    Pass an actual `layer` (e.g. "country_in") only for a profile this
    project authored itself, not preloaded anywhere — that's registered
    from app/fhir/profiling/ first if this process hasn't already."""
    if layer is not None:
        await _ensure_registered(resource_type, layer)
    async with _client() as client:
        resp = await client.post(
            "/validate", params={"profile": profile_url}, json=fhir_resource
        )
        resp.raise_for_status()
        operation_outcome = resp.json()
    return _issues_to_errors(operation_outcome)

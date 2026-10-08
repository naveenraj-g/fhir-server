"""Single entrypoint for resolving which terminology backend answers a
request — same shape as app/fhir/validation/dispatch.py's backend swap for
FHIR profile validation (settings.fhir_validation.backend). Nothing that
needs terminology (today: just this app's own /api/v1/terminology router,
via app/di/dependencies/terminology.py) should import TerminologyService or
RemoteTerminologyClient directly; go through get_terminology_client()
instead, so flipping settings.terminology.backend from "embedded" to
"remote" — the day this service is actually extracted into its own
deployment — needs no code changes at any call site, only a config edit."""

from app.core.config import settings
from app.terminology.client import TerminologyClient
from app.terminology.remote_client import RemoteTerminologyClient


def get_terminology_client(embedded_service: TerminologyClient) -> TerminologyClient:
    """`embedded_service` is the real, DI-wired TerminologyService — passed
    in rather than constructed here, so the caller's own DI/override
    machinery (tests included) still controls how it's built; this
    function never touches the container directly. Returned as-is for
    "embedded" (the default). For "remote", a RemoteTerminologyClient is
    built instead from settings.terminology.remote and the DI-wired
    instance is discarded unused — the network hop replaces it entirely,
    it doesn't wrap it."""
    if settings.terminology.backend == "remote":
        cfg = settings.terminology.remote
        return RemoteTerminologyClient(
            base_url=cfg.base_url, timeout_seconds=cfg.timeout_seconds
        )
    return embedded_service

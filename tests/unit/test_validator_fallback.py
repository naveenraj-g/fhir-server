"""Java validator: which failures are "system errors" (fall back to native)
and which are not."""

import httpx
import pytest

from app.core.config import settings
from app.errors.infrastructure import ValidatorUnavailableError
from app.fhir.validation import dispatch, java_validator
from app.fhir.validation.java_validator import JavaValidatorUnavailable

_DOC = {"resourceType": "Organization", "name": "X"}
_NATIVE = [{"field": "native", "message": "from native"}]
_JAVA_INVALID = [{"field": "name", "message": "java says no"}]
_PROFILE = "http://hl7.org/fhir/StructureDefinition/Organization"


def _sidecar(monkeypatch, handler):
    monkeypatch.setattr(
        java_validator,
        "_client",
        lambda: httpx.AsyncClient(
            base_url="http://sidecar", transport=httpx.MockTransport(handler)
        ),
    )


async def _validate():
    return await java_validator.validate_via_java(
        "Organization", _DOC, profile_url=_PROFILE
    )


# -- classification (java_validator.validate_via_java) -------------------------


async def test_connect_error_is_unavailable(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("refused")

    _sidecar(monkeypatch, handler)
    with pytest.raises(JavaValidatorUnavailable):
        await _validate()


async def test_timeout_is_unavailable(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("slow")

    _sidecar(monkeypatch, handler)
    with pytest.raises(JavaValidatorUnavailable):
        await _validate()


async def test_5xx_is_unavailable(monkeypatch):
    _sidecar(monkeypatch, lambda request: httpx.Response(503))
    with pytest.raises(JavaValidatorUnavailable):
        await _validate()


async def test_non_json_200_is_unavailable(monkeypatch):
    _sidecar(monkeypatch, lambda request: httpx.Response(200, text="<html>"))
    with pytest.raises(JavaValidatorUnavailable):
        await _validate()


async def test_4xx_is_not_unavailable(monkeypatch):
    _sidecar(monkeypatch, lambda request: httpx.Response(400, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        await _validate()


async def test_validation_errors_are_returned_not_raised(monkeypatch):
    outcome = {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invariant",
                "diagnostics": "org-1 failed",
                "expression": ["Organization"],
            }
        ],
    }
    _sidecar(monkeypatch, lambda request: httpx.Response(200, json=outcome))
    errors = await _validate()
    assert errors and errors[0]["message"] == "org-1 failed"


# -- dispatch.validate_resource --------------------------------------------------


@pytest.fixture
def java_backend(monkeypatch):
    cfg = settings.fhir_validation
    monkeypatch.setattr(cfg, "enabled", True)
    monkeypatch.setattr(cfg, "backend", "java_validator")
    monkeypatch.setattr(cfg, "country", None)  # no profile lookups -> no DB
    monkeypatch.setattr(cfg.java_validator, "fallback_to_native", True)
    monkeypatch.setattr(dispatch, "validate_base_r4", lambda rt, doc: _NATIVE)
    return cfg


def _java_raises(monkeypatch):
    async def boom(*a, **k):
        raise JavaValidatorUnavailable("down")

    monkeypatch.setattr(dispatch, "validate_via_java", boom)


async def test_system_error_falls_back_to_native(monkeypatch, java_backend):
    _java_raises(monkeypatch)
    assert await dispatch.validate_resource("Organization", _DOC) == _NATIVE


async def test_system_error_without_fallback_is_503(monkeypatch, java_backend):
    monkeypatch.setattr(java_backend.java_validator, "fallback_to_native", False)
    _java_raises(monkeypatch)
    with pytest.raises(ValidatorUnavailableError) as exc:
        await dispatch.validate_resource("Organization", _DOC)
    assert exc.value.status_code == 503


async def test_validation_failure_never_falls_back(monkeypatch, java_backend):
    async def invalid(*a, **k):
        return _JAVA_INVALID

    monkeypatch.setattr(dispatch, "validate_via_java", invalid)
    assert await dispatch.validate_resource("Organization", _DOC) == _JAVA_INVALID


async def test_4xx_from_sidecar_propagates_not_fallback(monkeypatch, java_backend):
    async def bad_request(*a, **k):
        raise httpx.HTTPStatusError(
            "bad",
            request=httpx.Request("POST", "http://s"),
            response=httpx.Response(400),
        )

    monkeypatch.setattr(dispatch, "validate_via_java", bad_request)
    with pytest.raises(httpx.HTTPStatusError):
        await dispatch.validate_resource("Organization", _DOC)


async def test_master_switch_off_skips_everything(monkeypatch, java_backend):
    monkeypatch.setattr(java_backend, "enabled", False)

    async def must_not_run(*a, **k):
        raise AssertionError("validator was called")

    monkeypatch.setattr(dispatch, "validate_via_java", must_not_run)
    monkeypatch.setattr(dispatch, "validate_base_r4", must_not_run)
    assert await dispatch.validate_resource("Organization", _DOC) == []


async def test_native_backend_unaffected(monkeypatch, java_backend):
    monkeypatch.setattr(java_backend, "backend", "native")
    assert await dispatch.validate_resource("Organization", _DOC) == _NATIVE

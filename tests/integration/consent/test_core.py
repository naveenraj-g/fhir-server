"""Core consent endpoint coverage.

Consent is stored content-based (like Goal, Task, Flag, CarePlan and the other rebuilt
resources): the request body (genuine FHIR R4 Consent JSON) is validated and stored whole in
`content`, every response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the
FHIR R4 search parameters are indexed (https://www.hl7.org/fhir/R4/consent.html#search). The
search parameters read the top-level `provision` only: a nested `provision.provision` is kept in
`content` but not indexed.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`patient`, `performer`,
`organization`, `sourceReference`, `verification.verifiedWith`, every provision's actor and data
reference at any depth, and every identifier's `assigner`). Search lives in test_search.py.

R4 requires `status`, `scope` and `category`; the native validator checks `scope` and `category`
(it cannot see a missing primitive `status`, which only the `java_validator` backend rejects).
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.consent.conftest import CONSENT_PERMS
from tests.integration.consent.support import (
    ACTION,
    BASE,
    LOINC,
    PURPOSE,
    concept,
    consent_body,
    create_consent,
    create_document,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    document_body,
    full_body,
    observation_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=CONSENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    patient = await create_patient(client)
    organization = await create_organization(client)
    practitioner = await create_practitioner(client)
    document = await create_document(client, document_body())
    observation = await create_observation(client, observation_body(patient))
    body = full_body(patient, organization, practitioner, document, observation)
    return await create_consent(client, body), body


async def _created(client, patient_id=None, **extra) -> int:
    return (
        await client.post(BASE + "/", json=consent_body(patient_id, **extra))
    ).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=consent_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Consent" and data["status"] == "active"


async def test_create_full_round_trip(client):
    consent, body = await _full(client)
    data = (await client.get(f"{BASE}/{consent}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_the_whole_provision_tree_including_nested_provisions(
    client,
):
    """`provision.type`, `.class`, `.code`, `.dataPeriod`, `.actor.role`, `.data.meaning`,
    `policy`, `policyRule`, `verification` and the nested provision live only in `content`."""
    consent, _ = await _full(client)
    data = (await client.get(f"{BASE}/{consent}")).json()
    provision = data["provision"]
    assert provision["type"] == "permit"
    assert provision["class"][0]["code"] == "Observation"
    assert provision["dataPeriod"]["start"] == "2025-01-01"
    assert provision["data"][0]["meaning"] == "instance"
    assert provision["provision"][0]["type"] == "deny"
    assert provision["provision"][0]["actor"][0]["reference"]["reference"].startswith(
        "Organization/"
    )
    assert data["policy"][0]["uri"] == "http://example.org/policy"
    assert data["verification"][0]["verified"] is True


@pytest.mark.parametrize(
    "status",
    ["draft", "proposed", "active", "rejected", "inactive", "entered-in-error"],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=consent_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_source_attachment_round_trips(client):
    body = consent_body(
        sourceAttachment={"contentType": "application/pdf", "title": "signed consent"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["sourceAttachment"]["title"] == "signed consent"


async def test_create_ignores_server_managed_id_and_meta(client):
    body = consent_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"scope": "patient-privacy"},
        {"category": {"text": "x"}},
        {"patient": "Patient/1"},
        {"dateTime": "yesterday"},
        {"performer": {"reference": "Patient/1"}},
        {"organization": "Organization/1"},
        {"policy": {"uri": "x"}},
        {"policy": [{"uri": 5}]},
        {"verification": [{"verified": "yes"}]},
        {"provision": "permit"},
        {"provision": {"type": "maybe"}},
        {"provision": {"period": "now"}},
        {"provision": {"actor": {"reference": {"reference": "Patient/1"}}}},
        {"provision": {"data": [{"meaning": "everything"}]}},
        {"identifier": {"value": "x"}},
    ):
        resp = await client.post(BASE + "/", json=consent_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_missing_required_elements_rejected(client, native_validation):
    for missing in ("scope", "category"):
        body = consent_body()
        del body[missing]
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=consent_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"scope_text": "x"}, {"patient_id": 5}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=consent_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=consent_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=consent_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_patient_must_exist(client):
    patient = await create_patient(client)
    assert await _created(client, patient) == 201
    missing = {"patient": {"reference": "Patient/999999"}}
    assert await _created(client, **missing) == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert await _created(client, theirs) == 422


async def test_create_performer_organization_and_source_must_exist(client):
    patient = await create_patient(client)
    organization = await create_organization(client)
    document = await create_document(client, document_body())
    ok = {
        "performer": [{"reference": f"Patient/{patient}"}],
        "organization": [{"reference": f"Organization/{organization}"}],
        "sourceReference": {"reference": f"DocumentReference/{document}"},
    }
    assert await _created(client, **ok) == 201
    for bad in (
        {"performer": [{"reference": "Patient/999999"}]},
        {"organization": [{"reference": "Organization/999999"}]},
        {"sourceReference": {"reference": "DocumentReference/999999"}},
    ):
        assert await _created(client, **bad) == 422, bad


async def test_create_verified_with_must_exist(client):
    patient = await create_patient(client)
    ok = {
        "verification": [
            {"verified": True, "verifiedWith": {"reference": f"Patient/{patient}"}}
        ]
    }
    bad = {
        "verification": [
            {"verified": True, "verifiedWith": {"reference": "Patient/999999"}}
        ]
    }
    assert await _created(client, **ok) == 201
    assert await _created(client, **bad) == 422


async def test_create_provision_actor_and_data_must_exist_at_every_depth(client):
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    observation = await create_observation(client, observation_body(patient))

    def provision(actor, data, nested_actor=None):
        body = {
            "type": "permit",
            "actor": [
                {"role": concept(ACTION, "x"), "reference": {"reference": actor}}
            ],
            "data": [{"meaning": "instance", "reference": {"reference": data}}],
        }
        if nested_actor:
            body["provision"] = [
                {
                    "actor": [
                        {
                            "role": concept(ACTION, "x"),
                            "reference": {"reference": nested_actor},
                        }
                    ]
                }
            ]
        return {"provision": body}

    assert (
        await _created(
            client,
            **provision(f"Practitioner/{practitioner}", f"Observation/{observation}"),
        )
        == 201
    )
    assert (
        await _created(
            client, **provision("Practitioner/999999", f"Observation/{observation}")
        )
        == 422
    )
    assert (
        await _created(
            client, **provision(f"Practitioner/{practitioner}", "Observation/999999")
        )
        == 422
    )
    # a nested provision is checked too, though it is not indexed
    assert (
        await _created(
            client,
            **provision(
                f"Practitioner/{practitioner}",
                f"Observation/{observation}",
                "Practitioner/999999",
            ),
        )
        == 422
    )


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = [{"value": "1", "assigner": {"reference": f"Organization/{organization}"}}]
    bad = [{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    assert await _created(client, identifier=ok) == 201
    assert await _created(client, identifier=bad) == 422


async def test_create_unmodeled_targets_are_not_checked(client):
    """A Contract source and a Device actor are not resources here: stored as sent."""
    body = consent_body(
        sourceReference={"reference": "Contract/999999"},
        provision={
            "actor": [
                {
                    "role": concept(ACTION, "x"),
                    "reference": {"reference": "Device/999999"},
                }
            ]
        },
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["sourceReference"] == {"reference": "Contract/999999"}


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    body = consent_body(patient=None)
    body["patient"] = {"reference": absolute}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    body["patient"] = logical
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    consent, _ = await _full(client)
    resp = await client.get(f"{BASE}/{consent}")
    assert resp.status_code == 200 and resp.json()["id"] == str(consent)


async def test_get_is_fhir_regardless_of_accept(client):
    consent = await create_consent(client, consent_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{consent}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Consent"


async def test_xml_only_accept_is_406(client):
    consent = await create_consent(client, consent_body())
    resp = await client.get(
        f"{BASE}/{consent}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    consent, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{consent}", json={"status": "inactive", "dateTime": "2026-02-02"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive"
    assert resp.json()["dateTime"] == "2026-02-02"
    assert resp.json()["scope"]["coding"][0]["code"] == "patient-privacy"  # untouched
    assert resp.json()["provision"]["type"] == "permit"  # untouched


async def test_patch_reindexes_search(client):
    consent, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{consent}",
        json={
            "status": "inactive",
            "dateTime": "2027-03-03T00:00:00Z",
            "category": [concept(LOINC, "other")],
            "provision": {
                "type": "deny",
                "period": {"start": "2027-03-01"},
                "action": [concept(ACTION, "correct")],
                "purpose": [{"system": PURPOSE, "code": "HRESCH"}],
            },
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "active", "inactive"),
        ("category", "59284-0", "other"),
        ("action", "access", "correct"),
        ("purpose", "TREAT", "HRESCH"),
        ("date", "2026-01-15", "2027-03-03"),
        ("period", "2026-06-01", "ge2027-03-01"),
    ):
        got_old = _ids((await client.get(BASE + "/", params={param: old})).json())
        assert consent not in got_old or param == "period", param
        assert consent in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    consent, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{consent}",
        json={"identifier": [], "performer": [], "organization": []},
    )
    for gone in ("identifier", "performer", "organization"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "consentor", "organization"):
        assert consent in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_provision_and_source(client):
    consent, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{consent}", json={"provision": None, "sourceReference": None}
    )
    assert "provision" not in resp.json() and "sourceReference" not in resp.json()
    for param in ("action", "actor", "data", "period", "source-reference"):
        assert consent in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    consent = await create_consent(client, consent_body())
    resp = await client.patch(
        f"{BASE}/{consent}", json={"patient": {"reference": "Patient/999999"}}
    )
    assert resp.status_code == 422
    assert "patient" not in (await client.get(f"{BASE}/{consent}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    consent = await create_consent(client, consent_body())
    assert (
        await client.patch(f"{BASE}/{consent}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{consent}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    consent, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{consent}")).status_code == 204
    assert (await client.get(f"{BASE}/{consent}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "C-1001"),
        ("action", "access"),
        ("purpose", "TREAT"),
    ):
        assert consent not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["consent:read"])
    assert (await client.post(BASE + "/", json=consent_body())).status_code == 403


async def test_org_less_token_rejected(client):
    consent = await create_consent(client, consent_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": CONSENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=consent_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{consent}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    consent = await create_consent(client, consent_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{consent}"),
            await other_client.patch(f"{BASE}/{consent}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{consent}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_consent(
        client, consent_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_consent_is_checked_where_it_can_be_named(client):
    """Consent.sourceReference can be another Consent and DetectedIssue.implicated is
    Reference(Any): a relative Consent there must exist (422 otherwise)."""
    consent = await create_consent(client, consent_body())
    assert (
        await _created(client, sourceReference={"reference": f"Consent/{consent}"})
        == 201
    )
    assert (
        await _created(client, sourceReference={"reference": "Consent/999999"}) == 422
    )
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Consent/{consent}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Consent/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422

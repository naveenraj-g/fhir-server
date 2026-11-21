"""Core related-person endpoint coverage.

RelatedPerson is stored Medplum-style (like Patient, Appointment, Encounter and
the other content-based resources): the request body (genuine FHIR R4
RelatedPerson JSON) is validated and stored whole in `content`, every response is
FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4
search parameters are indexed
(https://www.hl7.org/fhir/R4/relatedperson.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), the existence checks on `patient` and
`identifier.assigner`, and the fact that a RelatedPerson is now a real target
for the references that name one (Appointment / AppointmentResponse actors,
Encounter participants, Patient.link). Search lives in test_search.py.

R4 requires `patient`, but only the `java_validator` backend enforces cardinality
minimums (the native structural check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.related_person.conftest import RELATED_PERSON_PERMS
from tests.integration.related_person.support import (
    API,
    BASE,
    appointment_body,
    create_appointment,
    create_organization,
    create_patient,
    create_related_person,
    full_body,
    participant,
    related_person_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=RELATED_PERSON_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=related_person_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "RelatedPerson"
    assert data["patient"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    org = await create_organization(client)
    body = full_body(patient, org)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`photo`, `period` and `communication` have no search parameter — they live only in `content`."""
    data = (
        await client.post(
            BASE + "/", json=full_body(patient, await create_organization(client))
        )
    ).json()
    assert data["photo"] == [
        {"contentType": "image/png", "url": "https://example.org/mary.png"}
    ]
    assert data["period"] == {"start": "2020-01-01"}
    assert data["communication"] == [
        {"language": {"coding": [{"code": "en"}]}, "preferred": True}
    ]


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = related_person_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_gender_rejected(client, patient):
    assert (
        await client.post(BASE + "/", json=related_person_body(patient, gender="robot"))
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=related_person_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in ({"birth_date": "1990-01-01"}, {"patient_id": 1}, {"org_id": "x"}):
        resp = await client.post(
            BASE + "/", json={**related_person_body(patient), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=related_person_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=related_person_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client):
    assert (
        await client.post(BASE + "/", json=related_person_body(999999))
    ).status_code == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=related_person_body(theirs))
    ).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = related_person_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_that_exists(client, patient):
    org = await create_organization(client)
    body = related_person_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_patient_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json={"patient": {"reference": absolute}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    resp = await client.post(BASE + "/", json={"patient": logical})
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical


# ── A RelatedPerson is now a real target of the references that name one ─────


async def test_references_to_a_related_person_are_checked_and_resolve(client, patient):
    rp = await create_related_person(client, related_person_body(patient))
    ref = f"RelatedPerson/{rp}"
    # Appointment.participant.actor, AppointmentResponse.actor, Encounter.participant.individual, Patient.link.other
    appointment = await create_appointment(
        client, appointment_body(patient, participant=[participant(ref)])
    )
    assert appointment
    ar = {
        "appointment": {"reference": f"Appointment/{appointment}"},
        "participantStatus": "accepted",
        "actor": {"reference": ref},
    }
    assert (
        await client.post(f"{API}/appointment-responses/", json=ar)
    ).status_code == 201
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "participant": [{"individual": {"reference": ref}}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 201
    link = {"link": [{"other": {"reference": ref}, "type": "seealso"}]}
    assert (await client.post(f"{API}/patients/", json=link)).status_code == 201


async def test_references_to_a_missing_related_person_are_rejected(client, patient):
    ref = "RelatedPerson/999999"
    resp = await client.post(
        f"{API}/appointments/",
        json=appointment_body(patient, participant=[participant(ref)]),
    )
    assert resp.status_code == 422, resp.text
    appointment = await create_appointment(client, appointment_body(patient))
    ar = {
        "appointment": {"reference": f"Appointment/{appointment}"},
        "participantStatus": "accepted",
        "actor": {"reference": ref},
    }
    assert (
        await client.post(f"{API}/appointment-responses/", json=ar)
    ).status_code == 422
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "participant": [{"individual": {"reference": ref}}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 422
    assert (
        await client.post(
            f"{API}/patients/",
            json={"link": [{"other": {"reference": ref}, "type": "seealso"}]},
        )
    ).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    rp = await create_related_person(
        client, full_body(patient, await create_organization(client))
    )
    resp = await client.get(f"{BASE}/{rp}")
    assert resp.status_code == 200 and resp.json()["id"] == str(rp)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    rp = await create_related_person(client, related_person_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{rp}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "RelatedPerson"


async def test_xml_only_accept_is_406(client, patient):
    rp = await create_related_person(client, related_person_body(patient))
    resp = await client.get(f"{BASE}/{rp}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    rp = await create_related_person(
        client, full_body(patient, await create_organization(client))
    )
    resp = await client.patch(f"{BASE}/{rp}", json={"active": False, "gender": "other"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["active"] is False and resp.json()["gender"] == "other"
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["name"][0]["family"] == "Windsor"
    assert resp.json()["communication"][0]["preferred"] is True


async def test_patch_reindexes_search(client, patient):
    rp = await create_related_person(
        client, full_body(patient, await create_organization(client))
    )
    await client.patch(
        f"{BASE}/{rp}", json={"gender": "male", "name": [{"family": "Fairfax"}]}
    )
    assert rp not in _ids(
        (await client.get(BASE + "/", params={"gender": "female"})).json()
    )
    assert rp in _ids((await client.get(BASE + "/", params={"gender": "male"})).json())
    assert rp not in _ids(
        (await client.get(BASE + "/", params={"name": "Windsor"})).json()
    )
    assert rp in _ids((await client.get(BASE + "/", params={"name": "Fairfax"})).json())


async def test_patch_patient_replaced_and_reindexed(client, patient):
    rp = await create_related_person(client, related_person_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{rp}", json={"patient": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert rp not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert rp in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    rp = await create_related_person(
        client, full_body(patient, await create_organization(client))
    )
    assert rp in _ids(
        (await client.get(BASE + "/", params={"phone": "555-9988"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{rp}",
        json={"telecom": [], "relationship": [], "address": [], "identifier": []},
    )
    for gone in ("telecom", "relationship", "address", "identifier"):
        assert gone not in resp.json()
    assert resp.json()["name"][0]["family"] == "Windsor"  # untouched
    for param, value in (
        ("phone", "555-9988"),
        ("relationship", "MTH"),
        ("address-city", "Boston"),
        ("identifier", "RP-1001"),
    ):
        assert rp not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_patch_birth_date_reindexed(client, patient):
    rp = await create_related_person(
        client, related_person_body(patient, birthDate="1965-04-12")
    )
    await client.patch(f"{BASE}/{rp}", json={"birthDate": "1980-01"})
    assert rp not in _ids(
        (await client.get(BASE + "/", params={"birthdate": "1965-04-12"})).json()
    )
    assert rp in _ids(
        (await client.get(BASE + "/", params={"birthdate": "1980"})).json()
    )
    resp = await client.patch(f"{BASE}/{rp}", json={"birthDate": None})
    assert "birthDate" not in resp.json()
    assert rp in _ids(
        (await client.get(BASE + "/", params={"birthdate:missing": "true"})).json()
    )


async def test_patch_nonexistent_patient_rejected_and_nothing_written(client, patient):
    rp = await create_related_person(client, related_person_body(patient))
    resp = await client.patch(
        f"{BASE}/{rp}", json={"patient": {"reference": "Patient/999999"}}
    )
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{rp}")).json()["patient"] == {
        "reference": f"Patient/{patient}"
    }


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    rp = await create_related_person(
        client, related_person_body(patient, gender="female")
    )
    assert (
        await client.patch(f"{BASE}/{rp}", json={"gender": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{rp}")).json()["gender"] == "female"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    rp = await create_related_person(
        client, full_body(patient, await create_organization(client))
    )
    assert (await client.delete(f"{BASE}/{rp}")).status_code == 204
    assert (await client.get(f"{BASE}/{rp}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "RP-1001"),
        ("phone", "555-9988"),
        ("name", "Windsor"),
        ("relationship", "MTH"),
    ):
        assert rp not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["related_person:read"])
    assert (
        await client.post(BASE + "/", json=related_person_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    rp = await create_related_person(client, related_person_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": RELATED_PERSON_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=related_person_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{rp}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    rp = await create_related_person(client, related_person_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{rp}"),
            await other_client.patch(f"{BASE}/{rp}", json={"active": False}),
            await other_client.delete(f"{BASE}/{rp}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_related_person(
        client,
        related_person_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()

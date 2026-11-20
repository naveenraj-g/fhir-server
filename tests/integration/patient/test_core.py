"""Core patient endpoint coverage.

Patient is stored Medplum-style (like Practitioner and the other content-based
resources): the request body (genuine FHIR R4 Patient JSON) is validated and
stored whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/patient.html#search). Like Practitioner it can be
linked to an end-user (`user_id`, set by `PUT /{id}/user` or at create time with
`?link_me=true`, never part of the FHIR resource) and has a `/me` route — see
PatientModel's docstring.

This file holds create, read, patch, delete, the existence checks on the
references a Patient holds, the end-user link, self-signup, `/me` and auth
(org-less token, missing scope, cross-org isolation). Search lives in
test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_fhir_patient, assert_operation_outcome
from tests.integration.patient.conftest import PATIENT_PERMS
from tests.integration.patient.support import (
    BASE,
    FULL,
    MINIMAL,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    link_user,
)


@pytest.fixture
def native_validation(monkeypatch):
    """configs/config.yaml may switch the base R4 validator off
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=PATIENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_patient_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert_fhir_patient(data, active=True)
    assert data["name"][0]["family"] == "Chalmers"


async def test_create_with_no_elements_at_all(client):
    resp = await client.post(BASE + "/", json={})
    assert resp.status_code == 201, resp.text
    assert resp.json()["resourceType"] == "Patient"


async def test_create_full_round_trip(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in FULL.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    got = await client.get(f"{BASE}/{data['id']}")
    assert got.status_code == 200
    assert got.json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    """maritalStatus, photo, contact.* and multipleBirth have no search
    parameter — they live only in `content`, and must still round-trip."""
    data = (await client.post(BASE + "/", json=FULL)).json()
    assert data["maritalStatus"]["text"] == "Married"
    assert data["photo"][0]["url"].endswith("patient.png")
    assert data["contact"][0]["name"]["given"] == ["Sarah"]
    assert data["multipleBirthBoolean"] is False
    assert data["communication"][0]["preferred"] is True


async def test_create_choice_elements(client):
    body = {**MINIMAL, "deceasedDateTime": "2020-03-01T10:00:00Z", "multipleBirthInteger": 2}
    data = (await client.post(BASE + "/", json=body)).json()
    assert data["deceasedDateTime"] == "2020-03-01T10:00:00Z" and data["multipleBirthInteger"] == 2
    assert "deceasedBoolean" not in data


async def test_create_partial_birth_dates_are_kept_as_written(client):
    for value in ("1990", "1990-05", "1990-05-12"):
        data = (await client.post(BASE + "/", json={**MINIMAL, "birthDate": value})).json()
        assert data["birthDate"] == value


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] != "999"
    assert not data["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json={**MINIMAL, "not_a_fhir_element": 1})
    assert resp.status_code == 422, resp.text


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"birth_date": "1974-12-25"}, {"user_id": "u1"}, {"org_id": "x"}, {"marital_status_text": "x"}):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Practitioner"})
    assert resp.status_code == 422, resp.text


async def test_create_bad_gender_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "gender": "robot"})
    assert resp.status_code == 422, resp.text


async def test_create_bad_link_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "link": [{"other": {"reference": "Patient/1"}, "type": "bogus"}]})
    assert resp.status_code == 422, resp.text


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── The references a Patient holds ───────────────────────────────────────────


async def test_managing_organization_must_exist(client):
    body = {**MINIMAL, "managingOrganization": {"reference": "Organization/999999"}}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_managing_organization_resolves(client):
    org = await create_organization(client)
    body = {**MINIMAL, "managingOrganization": {"reference": f"Organization/{org}", "display": "Hospital"}}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["managingOrganization"] == {"reference": f"Organization/{org}", "display": "Hospital"}


async def test_general_practitioner_must_exist_for_every_modeled_type(client):
    for ref in ("Practitioner/999999", "PractitionerRole/999999", "Organization/999999"):
        body = {**MINIMAL, "generalPractitioner": [{"reference": ref}]}
        assert (await client.post(BASE + "/", json=body)).status_code == 422, ref


async def test_general_practitioner_resolves_for_every_modeled_type(client):
    prac = await create_practitioner(client)
    role = await create_practitioner_role(client)
    org = await create_organization(client)
    refs = [{"reference": f"Practitioner/{prac}"}, {"reference": f"PractitionerRole/{role}"}, {"reference": f"Organization/{org}"}]
    resp = await client.post(BASE + "/", json={**MINIMAL, "generalPractitioner": refs})
    assert resp.status_code == 201, resp.text
    assert resp.json()["generalPractitioner"] == refs


async def test_link_other_patient_and_related_person_must_exist(client):
    body = {**MINIMAL, "link": [{"other": {"reference": "Patient/999999"}, "type": "seealso"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    body = {**MINIMAL, "link": [{"other": {"reference": "RelatedPerson/999999"}, "type": "seealso"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    owner = await create_patient(client)
    rp = await client.post(
        "/api/fhir/v1/related-persons/", json={"patient": {"reference": f"Patient/{owner}"}}
    )
    assert rp.status_code == 201, rp.text
    body = {**MINIMAL, "link": [{"other": {"reference": f"RelatedPerson/{rp.json()['id']}"}, "type": "seealso"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 201
    other = await create_patient(client)
    body = {**MINIMAL, "link": [{"other": {"reference": f"Patient/{other}"}, "type": "replaces"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_contact_organization_and_identifier_assigner_must_exist(client):
    body = {**MINIMAL, "contact": [{"organization": {"reference": "Organization/999999"}}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    body = {**MINIMAL, "identifier": [{"value": "1", "assigner": {"reference": "Organization/999999"}}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = {
        **MINIMAL,
        "contact": [{"organization": {"reference": f"Organization/{org}"}}],
        "identifier": [{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_absolute_and_logical_references_are_stored_not_resolved(client):
    absolute = "https://other.example.org/fhir/Organization/42"
    logical = {"identifier": {"system": "urn:external-gps", "value": "GP-77"}}
    body = {**MINIMAL, "managingOrganization": {"reference": absolute}, "generalPractitioner": [logical]}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["managingOrganization"]["reference"] == absolute
    assert resp.json()["generalPractitioner"] == [logical]


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        foreign = await create_organization(other_client)
    finally:
        _as_user()
    body = {**MINIMAL, "managingOrganization": {"reference": f"Organization/{foreign}"}}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_patient_by_id(client):
    pid = await create_patient(client, FULL)
    resp = await client.get(f"{BASE}/{pid}")
    assert resp.status_code == 200
    assert_fhir_patient(resp.json(), id=str(pid))


async def test_get_patient_is_fhir_regardless_of_accept(client):
    pid = await create_patient(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{pid}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Patient"


async def test_xml_only_accept_is_406(client):
    pid = await create_patient(client)
    resp = await client.get(f"{BASE}/{pid}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406
    assert resp.json()["resourceType"] == "OperationOutcome"


async def test_get_patient_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_patient_scalar(client):
    pid = await create_patient(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"active": False, "gender": "female"})
    assert resp.status_code == 200, resp.text
    assert_fhir_patient(resp.json(), active=False, gender="female")
    # Untouched elements survive.
    assert resp.json()["name"][0]["family"] == "Chalmers"
    assert resp.json()["contact"][0]["name"]["family"] == "Chalmers"


async def test_patch_reindexes_search(client):
    pid = await create_patient(client, FULL)
    await client.patch(
        f"{BASE}/{pid}",
        json={"name": [{"family": "Renamed"}], "birthDate": "2001-02-03", "deceasedDateTime": "2024-01-01T00:00:00Z"},
    )
    assert pid not in _ids((await client.get(BASE + "/", params={"family": "Chalmers"})).json())
    assert pid in _ids((await client.get(BASE + "/", params={"family": "Renamed"})).json())
    assert pid not in _ids((await client.get(BASE + "/", params={"birthdate": "1974-12-25"})).json())
    assert pid in _ids((await client.get(BASE + "/", params={"birthdate": "2001-02-03"})).json())
    assert pid in _ids((await client.get(BASE + "/", params={"deceased": "true"})).json())


async def test_patch_replaces_list_wholesale_and_empty_clears(client):
    pid = await create_patient(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": [{"system": "phone", "value": "111"}]})
    assert [t["value"] for t in resp.json()["telecom"]] == ["111"]
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": []})
    assert "telecom" not in resp.json()
    assert pid not in _ids((await client.get(BASE + "/", params={"phone": "111"})).json())


async def test_patch_contact_and_communication_persist(client):
    pid = await create_patient(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}",
        json={
            "contact": [{"name": {"family": "Smith"}}],
            "communication": [{"language": {"coding": [{"code": "fr"}]}}],
        },
    )
    assert resp.json()["contact"][0]["name"]["family"] == "Smith"
    assert resp.json()["photo"][0]["url"].endswith("patient.png")
    assert pid not in _ids((await client.get(BASE + "/", params={"language": "en"})).json())
    assert pid in _ids((await client.get(BASE + "/", params={"language": "fr"})).json())


async def test_patch_references_reindex(client):
    prac = await create_practitioner(client)
    org = await create_organization(client)
    pid = await create_patient(client, {**MINIMAL, "generalPractitioner": [{"reference": f"Practitioner/{prac}"}]})
    assert pid in _ids((await client.get(BASE + "/", params={"general-practitioner": f"Practitioner/{prac}"})).json())
    await client.patch(
        f"{BASE}/{pid}", json={"generalPractitioner": [], "managingOrganization": {"reference": f"Organization/{org}"}}
    )
    assert pid not in _ids((await client.get(BASE + "/", params={"general-practitioner": f"Practitioner/{prac}"})).json())
    assert pid in _ids((await client.get(BASE + "/", params={"organization": str(org)})).json())


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    pid = await create_patient(client)
    resp = await client.patch(f"{BASE}/{pid}", json={"managingOrganization": {"reference": "Organization/999999"}})
    assert resp.status_code == 422
    assert "managingOrganization" not in (await client.get(f"{BASE}/{pid}")).json()


async def test_patch_patient_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    pid = await create_patient(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"gender": "robot"})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{pid}")).json()["gender"] == "male"


# ── End-user link (user_id) ──────────────────────────────────────────────────
# user_id is not a FHIR element: it is set by PUT /{id}/user (or by
# `?link_me=true` at create time), never by a body field, and never appears in
# the resource.


async def test_create_starts_unlinked(client):
    pid = await create_patient(client, FULL)
    resp = await client.get(f"{BASE}/{pid}/user")
    assert resp.status_code == 200
    assert resp.json() == {"patient_id": pid, "user_id": None}


async def test_link_get_and_unlink(client):
    pid = await create_patient(client)
    linked = await link_user(client, pid, "user-abc")
    assert linked.status_code == 200, linked.text
    assert linked.json() == {"patient_id": pid, "user_id": "user-abc"}
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] == "user-abc"
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 204
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] is None
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 204  # idempotent


async def test_link_is_not_part_of_the_resource(client):
    pid = await create_patient(client, FULL)
    await link_user(client, pid, "user-abc")
    body = (await client.get(f"{BASE}/{pid}")).json()
    assert "user-abc" not in str(body)
    assert "extension" not in body


async def test_relinking_replaces_the_user_and_same_user_is_a_noop(client):
    pid = await create_patient(client)
    await link_user(client, pid, "first")
    assert (await link_user(client, pid, "first")).status_code == 200
    assert (await link_user(client, pid, "second")).json()["user_id"] == "second"


async def test_a_user_can_be_only_one_patient_per_org(client):
    a = await create_patient(client)
    b = await create_patient(client)
    assert (await link_user(client, a, "same-user")).status_code == 200
    resp = await link_user(client, b, "same-user")
    assert resp.status_code == 422, resp.text
    await client.delete(f"{BASE}/{a}/user")  # unlinking the first frees the user
    assert (await link_user(client, b, "same-user")).status_code == 200


async def test_link_needs_its_own_permission(client):
    pid = await create_patient(client)
    _as_user(permissions=[p for p in PATIENT_PERMS if p != "patient:link"])
    assert (await link_user(client, pid)).status_code == 403
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 403
    assert (await client.get(f"{BASE}/{pid}/user")).status_code == 200  # read is enough to look


async def test_link_rejects_empty_or_unknown_fields(client):
    pid = await create_patient(client)
    assert (await client.put(f"{BASE}/{pid}/user", json={"user_id": ""})).status_code == 422
    assert (await client.put(f"{BASE}/{pid}/user", json={})).status_code == 422
    assert (await client.put(f"{BASE}/{pid}/user", json={"user_id": "u", "x": 1})).status_code == 422


async def test_link_not_found(client):
    for resp in (await link_user(client, 999999), await client.delete(f"{BASE}/999999/user")):
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_link_cross_org_returns_404(client, other_client):
    _as_user()
    pid = await create_patient(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await link_user(other_client, pid),
            await other_client.delete(f"{BASE}/{pid}/user"),
            await other_client.get(f"{BASE}/{pid}/user"),
        ):
            assert resp.status_code == 404, resp.text
    finally:
        _as_user()


async def test_the_same_user_can_be_linked_in_different_orgs(client, other_client):
    _as_user()
    mine = await create_patient(client)
    assert (await link_user(client, mine, "shared-user")).status_code == 200
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
        assert (await link_user(other_client, theirs, "shared-user")).status_code == 200
    finally:
        _as_user()


async def test_patch_cannot_set_the_link_through_an_extension(client):
    pid = await create_patient(client)
    ext = [{"url": "https://fhir-server.dev/fhir/StructureDefinition/user-id", "valueString": "u-test"}]
    assert (await client.patch(f"{BASE}/{pid}", json={"extension": ext})).status_code == 200
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] is None
    assert pid not in _ids((await client.get(BASE + "/me")).json())


async def test_patch_and_delete_leave_the_link_alone(client):
    pid = await create_patient(client, FULL)
    await link_user(client, pid, "user-abc")
    await client.patch(f"{BASE}/{pid}", json={"active": False, "name": [{"family": "Renamed"}]})
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] == "user-abc"


# ── Self-signup: ?link_me=true ───────────────────────────────────────────────


async def test_link_me_links_the_new_record_to_the_caller(client):
    resp = await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)
    assert resp.status_code == 201, resp.text
    pid = int(resp.json()["id"])
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] == "u-test"
    assert _ids((await client.get(BASE + "/me")).json()) == {pid}
    assert "u-test" not in str({k: v for k, v in resp.json().items() if k != "meta"})  # not in the resource


async def test_without_link_me_the_record_stays_unlinked(client):
    pid = await create_patient(client)
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] is None
    resp = await client.post(BASE + "/", params={"link_me": "false"}, json=MINIMAL)
    assert (await client.get(f"{BASE}/{resp.json()['id']}/user")).json()["user_id"] is None


async def test_link_me_twice_is_rejected_and_writes_nothing(client):
    first = await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)
    assert first.status_code == 201
    before = (await client.get(BASE + "/", params={"_summary": "count"})).json()["total"]
    second = await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)
    assert second.status_code == 422, second.text
    assert (await client.get(BASE + "/", params={"_summary": "count"})).json()["total"] == before


async def test_link_me_does_not_need_the_link_permission(client):
    """Self-signup: a user who may create patients links only themselves."""
    _as_user(permissions=["patient:create", "patient:read"])
    resp = await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert _ids((await client.get(BASE + "/me")).json()) == {int(resp.json()["id"])}


async def test_link_me_is_per_org(client, other_client):
    _as_user()
    assert (await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)).status_code == 201
    _as_user(sub="u-test", org_id="org-other")
    try:
        assert (await other_client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)).status_code == 201
    finally:
        _as_user()


async def test_link_me_cannot_steal_a_user_linked_by_staff(client):
    pid = await create_patient(client)
    await link_user(client, pid, "u-test")
    resp = await client.post(BASE + "/", params={"link_me": "true"}, json=MINIMAL)
    assert resp.status_code == 422


# ── /me ──────────────────────────────────────────────────────────────────────


async def test_me_returns_only_records_linked_to_the_caller(client):
    mine = await create_patient(client)
    await link_user(client, mine, "u-test")  # u-test is the caller's `sub`
    other = await create_patient(client)
    await link_user(client, other, "someone-else")
    await create_patient(client)  # never linked
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {mine}
    assert resp.json()["total"] == 1


async def test_me_follows_the_link(client):
    pid = await create_patient(client)
    assert _ids((await client.get(BASE + "/me")).json()) == set()
    await link_user(client, pid, "u-test")
    assert _ids((await client.get(BASE + "/me")).json()) == {pid}
    await client.delete(f"{BASE}/{pid}/user")
    assert _ids((await client.get(BASE + "/me")).json()) == set()


async def test_me_supports_search_parameters(client):
    a = await create_patient(client, {"name": [{"family": "Alpha"}]})
    await link_user(client, a, "u-test")
    assert _ids((await client.get(BASE + "/me", params={"family": "Beta"})).json()) == set()
    resp = await client.get(BASE + "/me", params={"family": "Alpha"})
    assert _ids(resp.json()) == {a}
    assert resp.json()["link"][0]["url"].split("?")[0].endswith("/patients/me")


async def test_me_is_not_shadowed_by_the_id_route(client):
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "Bundle"


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_patient(client):
    prac = await create_practitioner(client)
    pid = await create_patient(client, {**FULL, "generalPractitioner": [{"reference": f"Practitioner/{prac}"}]})
    assert (await client.delete(f"{BASE}/{pid}")).status_code == 204
    assert (await client.get(f"{BASE}/{pid}")).status_code == 404
    # Its index rows are gone with it.
    assert pid not in _ids((await client.get(BASE + "/", params={"family": "Chalmers"})).json())
    assert pid not in _ids((await client.get(BASE + "/", params={"general-practitioner": f"Practitioner/{prac}"})).json())


async def test_delete_patient_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_patient_no_permission(client):
    _as_user(permissions=["patient:read"])
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403


async def test_org_less_token_rejected(client):
    pid = await create_patient(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": PATIENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{pid}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()
    pid = await create_patient(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{pid}"),
            await other_client.patch(f"{BASE}/{pid}", json={"active": False}),
            await other_client.delete(f"{BASE}/{pid}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_patient(client, {"name": [{"family": "TenantAOnly"}]})
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"family": "TenantAOnly"})).json()
        assert bundle["total"] == 0
        assert "entry" not in bundle
    finally:
        _as_user()

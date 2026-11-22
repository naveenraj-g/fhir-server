"""Core care team endpoint coverage.

CareTeam is stored Medplum-style (like Patient, Encounter, Condition, Procedure, Specimen, Group
and the other content-based resources): the request body (genuine FHIR R4 CareTeam JSON) is
validated and stored whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/careteam.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`,
`participant.member` / `.onBehalfOf`, `reasonReference`, `managingOrganization`, note authors and
every identifier's `assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.care_team.conftest import CARE_TEAM_PERMS
from tests.integration.care_team.support import (
    BASE,
    SCT,
    care_team_body,
    concept,
    condition_body,
    create_care_team,
    create_condition,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    encounter_body,
    full_body,
    group_body,
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


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=CARE_TEAM_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    body = full_body(organization, patient, practitioner, encounter, condition)
    return await create_care_team(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_empty_is_valid(client):
    """R4 requires nothing on a CareTeam."""
    resp = await client.post(BASE + "/", json=care_team_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "CareTeam"


async def test_create_full_round_trip(client):
    care_team, body = await _full(client)
    data = (await client.get(f"{BASE}/{care_team}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`name`, `participant.role` / `.onBehalfOf` / `.period`, `reasonCode`, `reasonReference`,
    `managingOrganization`, `telecom` and `note` live only in `content`."""
    care_team, _ = await _full(client)
    data = (await client.get(f"{BASE}/{care_team}")).json()
    assert data["name"] == "Cardiology care team"
    assert data["participant"][0]["role"][0]["coding"][0]["code"] == "17561000"
    assert data["participant"][0]["period"] == {"start": "2026-01-01"}
    assert data["reasonCode"][0]["coding"][0]["code"] == "84114007"
    assert data["telecom"][0]["value"] == "+1-555-0100"
    assert data["note"][0]["text"] == "Weekly review."
    assert data["managingOrganization"][0]["reference"].startswith("Organization/")


@pytest.mark.parametrize(
    "status", ["proposed", "active", "suspended", "inactive", "entered-in-error"]
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=care_team_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = care_team_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "retired"},
        {"name": 5},
        {"category": {"text": "x"}},
        {"category": ["x"]},
        {"subject": "Patient/1"},
        {"encounter": "Encounter/1"},
        {"period": "2026"},
        {"identifier": {"value": "x"}},
        {"participant": {"member": {"reference": "Patient/1"}}},
        {"participant": [{"member": "Patient/1"}]},
        {"participant": [{"role": {"text": "x"}}]},
        {"reasonCode": {"text": "x"}},
        {"reasonReference": {"reference": "Condition/1"}},
        {"managingOrganization": {"reference": "Organization/1"}},
        {"telecom": {"value": "x"}},
        {"note": {"text": "x"}},
    ):
        resp = await client.post(BASE + "/", json=care_team_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=care_team_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"subject_id": 1}, {"org_id": "x"}, {"user_id": "x"}):
        resp = await client.post(BASE + "/", json={**care_team_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=care_team_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=care_team_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    for ref in (f"Patient/{patient}", f"Group/{group}"):
        body = care_team_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in ("Patient/999999", "Group/999999"):
        body = care_team_body(subject={"reference": missing})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_encounter_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    ok = care_team_body(encounter={"reference": f"Encounter/{encounter}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = care_team_body(encounter={"reference": "Encounter/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_participant_members_must_exist(client):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    organization = await create_organization(client)
    first = await create_care_team(client, care_team_body())
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"RelatedPerson/{related}",
        f"Patient/{patient}",
        f"Organization/{organization}",
        f"CareTeam/{first}",
    ):
        body = care_team_body(participant=[{"member": {"reference": ref}}])
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "RelatedPerson/999999",
        "Patient/999999",
        "Organization/999999",
        "CareTeam/999999",
    ):
        body = care_team_body(participant=[{"member": {"reference": missing}}])
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_on_behalf_of_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    participant = {
        "member": {"reference": f"Practitioner/{practitioner}"},
        "onBehalfOf": {"reference": f"Organization/{organization}"},
    }
    ok = care_team_body(participant=[participant])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    participant["onBehalfOf"] = {"reference": "Organization/999999"}
    bad = care_team_body(participant=[participant])
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reason_reference_must_exist(client):
    patient = await create_patient(client)
    condition = await create_condition(client, condition_body(patient))
    ok = care_team_body(reasonReference=[{"reference": f"Condition/{condition}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = care_team_body(reasonReference=[{"reference": "Condition/999999"}])
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_managing_organizations_must_exist(client):
    organization = await create_organization(client)
    ok = care_team_body(
        managingOrganization=[{"reference": f"Organization/{organization}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = care_team_body(
        managingOrganization=[
            {"reference": f"Organization/{organization}"},
            {"reference": "Organization/999999"},
        ]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_note_author_must_exist(client):
    practitioner = await create_practitioner(client)
    ok = care_team_body(
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
                "text": "x",
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = care_team_body(
        note=[{"authorReference": {"reference": "Practitioner/999999"}, "text": "x"}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_every_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = care_team_body(
        identifier=[
            {
                "system": "urn:t",
                "value": "1",
                "assigner": {"reference": f"Organization/{organization}"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = care_team_body(
        identifier=[
            {
                "system": "urn:t",
                "value": "1",
                "assigner": {"reference": "Organization/999999"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = care_team_body(subject={"reference": f"Patient/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_and_logical_references_not_resolved(client):
    body = care_team_body(
        subject={"reference": "https://other.example.org/fhir/Patient/1"},
        encounter={"identifier": {"system": "urn:enc", "value": "E-1"}},
        participant=[
            {"member": {"reference": "https://other.example.org/fhir/Practitioner/9"}},
            {"member": {"identifier": {"system": "urn:pr", "value": "P-9"}}},
        ],
        managingOrganization=[
            {"reference": "https://other.example.org/fhir/Organization/7"}
        ],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["participant"][1]["member"]["identifier"]["value"] == "P-9"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    care_team, _ = await _full(client)
    resp = await client.get(f"{BASE}/{care_team}")
    assert resp.status_code == 200 and resp.json()["id"] == str(care_team)


async def test_get_is_fhir_regardless_of_accept(client):
    care_team = await create_care_team(client, care_team_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{care_team}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "CareTeam"


async def test_xml_only_accept_is_406(client):
    care_team = await create_care_team(client, care_team_body())
    resp = await client.get(
        f"{BASE}/{care_team}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    care_team, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{care_team}", json={"status": "inactive", "name": "Retired team"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive" and resp.json()["name"] == "Retired team"
    assert resp.json()["category"][0]["coding"][0]["code"] == "LA27976-2"  # untouched
    assert resp.json()["note"][0]["text"] == "Weekly review."


async def test_patch_reindexes_search(client):
    care_team, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{care_team}",
        json={
            "status": "suspended",
            "category": [concept(SCT, "999")],
            "period": {"start": "2030-01-01"},
            "subject": {"reference": f"Patient/{patient}"},
            "participant": [],
        },
    )
    for param, old, new in (
        ("status", "active", "suspended"),
        ("category", "LA27976-2", "999"),
        ("date", "eq2026-03-01", "ge2031-01-01"),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert care_team not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert care_team in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert care_team in _ids(
        (await client.get(BASE + "/", params={"participant:missing": "true"})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client):
    care_team, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{care_team}",
        json={"identifier": [], "category": [], "participant": []},
    )
    for gone in ("identifier", "category", "participant"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "category", "participant"):
        assert care_team in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_subject_and_missing_follows(client):
    patient = await create_patient(client)
    care_team = await create_care_team(
        client, care_team_body(subject={"reference": f"Patient/{patient}"})
    )
    resp = await client.patch(f"{BASE}/{care_team}", json={"subject": None})
    assert "subject" not in resp.json()
    assert care_team in _ids(
        (await client.get(BASE + "/", params={"subject:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    care_team = await create_care_team(client, care_team_body())
    resp = await client.patch(
        f"{BASE}/{care_team}",
        json={"participant": [{"member": {"reference": "Practitioner/999999"}}]},
    )
    assert resp.status_code == 422
    assert "participant" not in (await client.get(f"{BASE}/{care_team}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    care_team = await create_care_team(client, care_team_body(status="active"))
    assert (
        await client.patch(f"{BASE}/{care_team}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{care_team}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"name": "x"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    care_team, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{care_team}")).status_code == 204
    assert (await client.get(f"{BASE}/{care_team}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "CT-1001"),
        ("category", "LA27976-2"),
        ("status", "active"),
    ):
        assert care_team not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["care_team:read"])
    assert (await client.post(BASE + "/", json=care_team_body())).status_code == 403


async def test_org_less_token_rejected(client):
    care_team = await create_care_team(client, care_team_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": CARE_TEAM_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=care_team_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{care_team}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    care_team = await create_care_team(client, care_team_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{care_team}"),
            await other_client.patch(f"{BASE}/{care_team}", json={"name": "x"}),
            await other_client.delete(f"{BASE}/{care_team}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_care_team(
        client,
        care_team_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_care_team_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative CareTeam there must exist."""
    care_team = await create_care_team(client, care_team_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"CareTeam/{care_team}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "CareTeam/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422

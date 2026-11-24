"""Core observation endpoint coverage.

Observation is stored Medplum-style (like Patient, Encounter, Condition, Procedure, DiagnosticReport,
RiskAssessment and the other content-based resources): the request body (genuine FHIR R4
Observation JSON) is validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search parameters are
indexed (https://www.hl7.org/fhir/R4/observation.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`, `basedOn`,
`partOf`, `performer`, `hasMember`, `derivedFrom`, note authors, `identifier.assigner`). Search lives
in test_search.py.

R4 requires `status` and `code` (and rules obs-3, obs-6, obs-7), but only the `java_validator`
backend enforces cardinality minimums and invariants (the native structural check does not), so
that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.observation.conftest import OBSERVATION_PERMS
from tests.integration.observation.support import (
    BASE,
    blood_pressure,
    concept,
    create_encounter,
    create_immunization,
    create_location,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_related_person,
    encounter_body,
    full_body,
    immunization_body,
    loinc,
    observation_body,
    procedure_body,
    quantity,
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


def _as_user(sub="u-test", org_id="org-test", permissions=OBSERVATION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    member = await create_observation(client, observation_body(patient))
    procedure = await create_procedure(client, procedure_body(patient))
    body = full_body(patient, encounter, practitioner, organization, member, procedure)
    return await create_observation(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=observation_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Observation" and data["status"] == "final"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_without_a_subject(client):
    resp = await client.post(BASE + "/", json=observation_body())
    assert resp.status_code == 201, resp.text
    assert "subject" not in resp.json()


async def test_create_full_round_trip(client, patient):
    observation, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{observation}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`issued`, `interpretation`, `note`, `bodySite`, `referenceRange` and a component's
    interpretation / range live only in `content`."""
    observation, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{observation}")).json()
    assert data["issued"] == "2023-01-15T09:35:00Z"
    assert data["interpretation"][0]["coding"][0]["code"] == "H"
    assert data["note"][0]["authorString"] == "Nurse Joy"
    assert data["bodySite"]["coding"][0]["code"] == "368208006"
    assert data["referenceRange"][0]["high"]["value"] == 140
    assert data["component"][0]["referenceRange"] == [{"high": quantity(140)}]


async def test_create_blood_pressure_round_trips(client, patient):
    body = blood_pressure(patient, 142, 91)
    data = (await client.post(BASE + "/", json=body)).json()
    assert [c["valueQuantity"]["value"] for c in data["component"]] == [142, 91]


@pytest.mark.parametrize(
    "value",
    [
        {"valueQuantity": quantity(5)},
        {
            "valueCodeableConcept": concept(
                "http://snomed.info/sct", "260385009", "Negative"
            )
        },
        {"valueString": "positive"},
        {"valueBoolean": False},
        {"valueInteger": 7},
        {"valueRange": {"low": quantity(1), "high": quantity(2)}},
        {
            "valueRatio": {
                "numerator": quantity(1, "mg", "mg"),
                "denominator": quantity(2, "mL", "mL"),
            }
        },
        {
            "valueSampledData": {
                "origin": quantity(0),
                "period": 10,
                "dimensions": 1,
                "data": "1 2 3",
            }
        },
        {"valueTime": "09:30:00"},
        {"valueDateTime": "2023-01"},
        {"valuePeriod": {"start": "2023-01-01", "end": "2023-06-01"}},
    ],
    ids=[
        "quantity",
        "concept",
        "string",
        "boolean",
        "integer",
        "range",
        "ratio",
        "sampled",
        "time",
        "dateTime",
        "period",
    ],
)
async def test_create_each_value_choice_round_trips(client, patient, value):
    resp = await client.post(BASE + "/", json=observation_body(patient, **value))
    assert resp.status_code == 201, resp.text
    for key, expected in value.items():
        assert resp.json()[key] == expected


@pytest.mark.parametrize(
    "effective",
    [
        {"effectiveDateTime": "2023-01"},
        {"effectivePeriod": {"start": "2023-01-01", "end": "2023-06-01"}},
        {"effectiveInstant": "2023-01-15T09:30:00Z"},
        {
            "effectiveTiming": {
                "event": ["2023-01-01T08:00:00Z", "2023-01-03T08:00:00Z"]
            }
        },
    ],
    ids=["dateTime", "period", "instant", "timing"],
)
async def test_create_each_effective_choice_round_trips(client, patient, effective):
    resp = await client.post(BASE + "/", json=observation_body(patient, **effective))
    assert resp.status_code == 201, resp.text
    for key, value in effective.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "status",
    [
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=observation_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = observation_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"effectiveDateTime": "yesterday"},
        {"code": "x"},
        {"category": {"text": "x"}},
        {"performer": {"reference": "Practitioner/1"}},
        {"component": {"code": {"text": "x"}}},
        {"component": [{"code": "x"}]},
        {"valueQuantity": "5"},
        {"valueQuantity": {"value": "high"}},
        {"valueBoolean": "yes"},
        {"valueInteger": "7"},
        {"issued": 5},
        {"interpretation": "H"},
        {"referenceRange": {"text": "x"}},
        {"identifier": {"value": "x"}},
        {"note": {"text": "x"}},
        {"hasMember": {"reference": "Observation/1"}},
    ):
        resp = await client.post(BASE + "/", json=observation_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/",
            json={"status": "final", "code": {"text": "x"}, "subject": "Patient/1"},
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=observation_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in ({"code_text": "x"}, {"value_quantity_value": 5}, {"org_id": "x"}):
        resp = await client.post(
            BASE + "/", json={**observation_body(patient), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=observation_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=observation_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_subject_must_exist(client):
    assert (
        await client.post(BASE + "/", json=observation_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=observation_body(theirs))
    ).status_code == 422


async def test_create_subject_is_checked_for_a_patient_or_location_only(client):
    location = await create_location(client)
    ok = {
        "status": "final",
        "code": {"text": "x"},
        "subject": {"reference": f"Location/{location}"},
    }
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {
        "status": "final",
        "code": {"text": "x"},
        "subject": {"reference": "Location/999999"},
    }
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    # a Group is checked (Group/430001 is seeded); a Device is not rebuilt: stored as sent
    group_missing = {
        "status": "final",
        "code": {"text": "x"},
        "subject": {"reference": "Group/999999"},
    }
    assert (await client.post(BASE + "/", json=group_missing)).status_code == 422
    for stored in ("Group/430001", "Device/999999"):
        body = {
            "status": "final",
            "code": {"text": "x"},
            "subject": {"reference": stored},
        }
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 201, (stored, resp.text)
        assert resp.json()["subject"] == {"reference": stored}


async def test_create_encounter_must_exist(client, patient):
    encounter = await create_encounter(client, encounter_body())
    ok = observation_body(patient, encounter={"reference": f"Encounter/{encounter}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    resp = await client.post(
        BASE + "/",
        json=observation_body(patient, encounter={"reference": "Encounter/999999"}),
    )
    assert resp.status_code == 422


async def test_create_performer_is_checked_for_rebuilt_types(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    related = await create_related_person(client, related_person_body(patient))
    ok = observation_body(
        patient,
        performer=[
            {"reference": f"Practitioner/{practitioner}"},
            {"reference": f"PractitionerRole/{role}"},
            {"reference": f"Organization/{organization}"},
            {"reference": f"Patient/{patient}"},
            {"reference": f"RelatedPerson/{related}"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Organization/999999",
        "Patient/999999",
        "RelatedPerson/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=observation_body(patient, performer=[{"reference": missing}]),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_has_member_and_derived_from_check_observations(client, patient):
    member = await create_observation(client, observation_body(patient))
    ok = observation_body(
        patient,
        hasMember=[
            {"reference": f"Observation/{member}"},
            {"reference": "MolecularSequence/999999"},
        ],
        derivedFrom=[
            {"reference": f"Observation/{member}"},
            {"reference": "Media/999999"},
        ],
    )
    assert (
        await client.post(BASE + "/", json=ok)
    ).status_code == 201  # not rebuilt: stored as sent
    for element in ("hasMember", "derivedFrom"):
        # Observation and QuestionnaireResponse are rebuilt resources: a dangling one is a 422
        for missing in ("Observation/999999", "QuestionnaireResponse/999999"):
            resp = await client.post(
                BASE + "/",
                json=observation_body(patient, **{element: [{"reference": missing}]}),
            )
            assert resp.status_code == 422, (element, missing, resp.text)


async def test_create_part_of_is_checked_for_a_procedure_or_immunization(
    client, patient
):
    procedure = await create_procedure(client, procedure_body(patient))
    immunization = await create_immunization(client, immunization_body(patient))
    ok = observation_body(
        patient,
        partOf=[
            {"reference": f"Procedure/{procedure}"},
            {"reference": f"Immunization/{immunization}"},
            {"reference": "Device/999999"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "Procedure/999999",
        "Immunization/999999",
        "MedicationAdministration/999999",
        "MedicationStatement/999999",
    ):
        resp = await client.post(
            BASE + "/", json=observation_body(patient, partOf=[{"reference": missing}])
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_based_on_focus_and_device_are_not_checked(client, patient):
    body = observation_body(
        patient,
        basedOn=[{"reference": "DeviceRequest/999999"}],
        focus=[{"reference": "Device/999999"}],
        device={"reference": "Device/999999"},
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_note_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = observation_body(
        patient,
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = observation_body(
        patient,
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}],
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = observation_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = observation_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(
        BASE + "/",
        json={
            "status": "final",
            "code": {"text": "x"},
            "subject": {"reference": absolute},
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = observation_body(
        None,
        subject=logical,
        performer=[{"reference": "https://other.example.org/fhir/Practitioner/7"}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["performer"] == [
        {"reference": "https://other.example.org/fhir/Practitioner/7"}
    ]


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    observation, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{observation}")
    assert resp.status_code == 200 and resp.json()["id"] == str(observation)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    observation = await create_observation(client, observation_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{observation}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Observation"


async def test_xml_only_accept_is_406(client, patient):
    observation = await create_observation(client, observation_body(patient))
    resp = await client.get(
        f"{BASE}/{observation}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    observation, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{observation}",
        json={"status": "amended", "valueQuantity": quantity(118)},
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "amended"
        and resp.json()["valueQuantity"]["value"] == 118
    )
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert len(resp.json()["component"]) == 2


async def test_patch_reindexes_search(client, patient):
    observation, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{observation}",
        json={
            "effectiveDateTime": "2024-05-01",
            "code": loinc("1234-5", "Other"),
            "valueQuantity": quantity(80),
            "status": "amended",
            "component": [{"code": loinc("9999-9"), "valueQuantity": quantity(3)}],
        },
    )
    for param, old, new in (
        ("date", "2023-01-15", "2024-05-01"),
        ("code", "85354-9", "1234-5"),
        ("value-quantity", "120", "80"),
        ("status", "final", "amended"),
        ("component-code", "8480-6", "9999-9"),
        ("component-value-quantity", "142", "3"),
    ):
        assert observation not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert observation in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    observation = await create_observation(client, observation_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{observation}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert observation not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert observation in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    observation, _ = await _full(client, patient)
    assert observation in _ids(
        (await client.get(BASE + "/", params={"identifier": "OBS-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{observation}",
        json={
            "identifier": [],
            "category": [],
            "performer": [],
            "component": [],
            "hasMember": [],
            "note": [],
        },
    )
    for gone in (
        "identifier",
        "category",
        "performer",
        "component",
        "hasMember",
        "note",
    ):
        assert gone not in resp.json()
    assert resp.json()["valueQuantity"]["value"] == 120  # untouched
    assert observation not in _ids(
        (await client.get(BASE + "/", params={"identifier": "OBS-1001"})).json()
    )
    for param in (
        "category",
        "performer",
        "has-member",
        "component-code",
        "component-value-quantity",
    ):
        assert observation in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_a_value_and_missing_follows(client, patient):
    observation = await create_observation(
        client, observation_body(patient, valueQuantity=quantity(5))
    )
    resp = await client.patch(f"{BASE}/{observation}", json={"valueQuantity": None})
    assert "valueQuantity" not in resp.json()
    assert observation in _ids(
        (await client.get(BASE + "/", params={"value-quantity:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    observation = await create_observation(client, observation_body(patient))
    resp = await client.patch(
        f"{BASE}/{observation}",
        json={"hasMember": [{"reference": "Observation/999999"}]},
    )
    assert resp.status_code == 422
    assert "hasMember" not in (await client.get(f"{BASE}/{observation}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    observation = await create_observation(client, observation_body(patient, "final"))
    assert (
        await client.patch(f"{BASE}/{observation}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{observation}")).json()["status"] == "final"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "amended"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    observation, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{observation}")).status_code == 204
    assert (await client.get(f"{BASE}/{observation}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "OBS-1001"),
        ("code", "85354-9"),
        ("value-quantity", "120"),
        ("component-code", "8480-6"),
    ):
        assert observation not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["observation:read"])
    assert (
        await client.post(BASE + "/", json=observation_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    observation = await create_observation(client, observation_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": OBSERVATION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=observation_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{observation}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    observation = await create_observation(client, observation_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{observation}"),
            await other_client.patch(
                f"{BASE}/{observation}", json={"status": "amended"}
            ),
            await other_client.delete(f"{BASE}/{observation}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_observation(
        client,
        observation_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_create_specimen_must_exist(client, patient):
    ok = observation_body(patient, specimen={"reference": "Specimen/310001"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = observation_body(patient, specimen={"reference": "Specimen/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_based_on_service_request_must_exist(client, patient):
    ok = observation_body(patient, basedOn=[{"reference": "ServiceRequest/80001"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = observation_body(
        patient, basedOn=[{"reference": "ServiceRequest/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_based_on_medication_request_must_exist(client, patient):
    from tests.helpers.medication_requests import create_minimal_medication_request

    existing = await create_minimal_medication_request(client)
    ok = observation_body(
        patient, basedOn=[{"reference": f"MedicationRequest/{existing}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = observation_body(
        patient, basedOn=[{"reference": "MedicationRequest/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422

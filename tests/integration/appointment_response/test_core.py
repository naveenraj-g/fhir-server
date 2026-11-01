from tests.integration.appointment_response.support import (
    BASE,
    FHIR_ACCEPT,
    PLAIN_ACCEPT,
    appointment_response_with_fallbacks,
    create_parent_appointment,
)


async def test_create_appointment_response_with_reference_identifier_fallbacks(client):
    appt_id = await create_parent_appointment(client)
    payload = appointment_response_with_fallbacks(appt_id)

    resp = await client.post(BASE + "/", json=payload, headers=PLAIN_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # Plain response verification
    assert data["participant_status"] == "accepted"
    assert data["appointment_id"] == appt_id
    assert data["appointment"] == f"Appointment/{appt_id}"

    # Assigner identifier fallback
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["assigner_display"] == "External Scheduling Service"
    assert data["identifier"][0]["assigner_identifier_system"] == "http://agencies.example.org"
    assert data["identifier"][0]["assigner_identifier_value"] == "SCHED-AGENCY-9"

    # Actor identifier fallback
    assert data["actor_display"] == "Dr. External Provider"
    assert data["actor_identifier_system"] == "http://npi.example.org"
    assert data["actor_identifier_value"] == "NPI-887766"

    resp_id = data["id"]

    # FHIR response verification
    fhir_resp = await client.get(f"{BASE}/{resp_id}", headers=FHIR_ACCEPT)
    assert fhir_resp.status_code == 200, fhir_resp.text
    fhir_data = fhir_resp.json()

    assert fhir_data["resourceType"] == "AppointmentResponse"
    assert fhir_data["id"] == str(resp_id)
    assert fhir_data["appointment"]["reference"] == f"Appointment/{appt_id}"

    # Assigner fallback in FHIR
    assert fhir_data["identifier"][0]["assigner"]["display"] == "External Scheduling Service"
    assert fhir_data["identifier"][0]["assigner"]["identifier"]["system"] == "http://agencies.example.org"
    assert fhir_data["identifier"][0]["assigner"]["identifier"]["value"] == "SCHED-AGENCY-9"

    # Actor fallback in FHIR
    assert fhir_data["actor"]["display"] == "Dr. External Provider"
    assert fhir_data["actor"]["identifier"]["system"] == "http://npi.example.org"
    assert fhir_data["actor"]["identifier"]["value"] == "NPI-887766"


async def test_patch_appointment_response(client):
    appt_id = await create_parent_appointment(client)
    payload = appointment_response_with_fallbacks(appt_id)
    create_resp = await client.post(BASE + "/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    resp_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"{BASE}/{resp_id}",
        json={"comment": "Tentative attendance due to travel"},
        headers=PLAIN_ACCEPT,
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["comment"] == "Tentative attendance due to travel"


async def test_delete_appointment_response(client):
    appt_id = await create_parent_appointment(client)
    payload = appointment_response_with_fallbacks(appt_id)
    create_resp = await client.post(BASE + "/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    resp_id = create_resp.json()["id"]

    del_resp = await client.delete(f"{BASE}/{resp_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{resp_id}")
    assert get_resp.status_code == 404

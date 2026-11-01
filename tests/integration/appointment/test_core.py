from tests.integration.appointment.support import (
    BASE,
    FHIR_ACCEPT,
    PLAIN_ACCEPT,
    appointment_with_fallbacks,
)


async def test_create_appointment_with_reference_identifier_fallbacks(client):
    payload = appointment_with_fallbacks()
    resp = await client.post(BASE + "/", json=payload, headers=PLAIN_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # Plain response verification
    assert data["status"] == "booked"
    assert data["description"] == "Consultation with external provider"

    # Assigner fallback on identifier
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["assigner_display"] == "Regional Health Authority"
    assert data["identifier"][0]["assigner_identifier_system"] == "http://gov.example.org/agencies"
    assert data["identifier"][0]["assigner_identifier_value"] == "RHA-101"

    # Participant actor fallback
    assert len(data["participant"]) == 1
    assert data["participant"][0]["actor_display"] == "Dr. External Attender"
    assert data["participant"][0]["actor_identifier_system"] == "http://npi.example.org"
    assert data["participant"][0]["actor_identifier_value"] == "NPI-555666"

    # Reason reference fallback
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0]["reference_display"] == "External Diagnosis"
    assert data["reason_reference"][0]["reference_identifier_system"] == "http://diagnoses.example.org"
    assert data["reason_reference"][0]["reference_identifier_value"] == "DIAG-1234"

    # Supporting information fallback
    assert len(data["supporting_information"]) == 1
    assert data["supporting_information"][0]["reference_display"] == "External Chart Summary"
    assert data["supporting_information"][0]["reference_identifier_value"] == "REC-987"

    # Based on fallback
    assert len(data["based_on"]) == 1
    assert data["based_on"][0]["reference_display"] == "External Service Request"
    assert data["based_on"][0]["reference_identifier_value"] == "SR-4455"

    appt_id = data["id"]

    # FHIR response verification
    fhir_resp = await client.get(f"{BASE}/{appt_id}", headers=FHIR_ACCEPT)
    assert fhir_resp.status_code == 200, fhir_resp.text
    fhir_data = fhir_resp.json()

    assert fhir_data["resourceType"] == "Appointment"
    assert fhir_data["id"] == str(appt_id)

    # FHIR assigner identifier fallback
    assert fhir_data["identifier"][0]["assigner"]["display"] == "Regional Health Authority"
    assert fhir_data["identifier"][0]["assigner"]["identifier"]["system"] == "http://gov.example.org/agencies"
    assert fhir_data["identifier"][0]["assigner"]["identifier"]["value"] == "RHA-101"

    # FHIR participant actor identifier fallback
    assert fhir_data["participant"][0]["actor"]["display"] == "Dr. External Attender"
    assert fhir_data["participant"][0]["actor"]["identifier"]["system"] == "http://npi.example.org"
    assert fhir_data["participant"][0]["actor"]["identifier"]["value"] == "NPI-555666"

    # FHIR reasonReference fallback
    assert fhir_data["reasonReference"][0]["display"] == "External Diagnosis"
    assert fhir_data["reasonReference"][0]["identifier"]["value"] == "DIAG-1234"

    # FHIR supportingInformation fallback
    assert fhir_data["supportingInformation"][0]["display"] == "External Chart Summary"
    assert fhir_data["supportingInformation"][0]["identifier"]["value"] == "REC-987"

    # FHIR basedOn fallback
    assert fhir_data["basedOn"][0]["display"] == "External Service Request"
    assert fhir_data["basedOn"][0]["identifier"]["value"] == "SR-4455"


async def test_patch_appointment(client):
    payload = appointment_with_fallbacks()
    create_resp = await client.post(BASE + "/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    appt_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"{BASE}/{appt_id}",
        json={"comment": "Updated comment"},
        headers=PLAIN_ACCEPT,
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["comment"] == "Updated comment"


async def test_delete_appointment(client):
    payload = appointment_with_fallbacks()
    create_resp = await client.post(BASE + "/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    appt_id = create_resp.json()["id"]

    del_resp = await client.delete(f"{BASE}/{appt_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{appt_id}")
    assert get_resp.status_code == 404

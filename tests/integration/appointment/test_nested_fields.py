"""Nested appointment payload coverage.

Appointment has most of its complexity in one large create payload rather than
separate child endpoints. These tests focus on mapper correctness and reference
validation for those nested structures.
"""

from tests.helpers.assertions import (
    assert_fhir_appointment,
    assert_operation_outcome,
    assert_plain_appointment,
)
from tests.integration.appointment.support import BASE, FHIR_ACCEPT, build_full_payload


async def test_create_appointment_full_plain_mapping(client):
    """The rich payload should preserve representative nested data in plain JSON."""
    resp = await client.post(BASE + "/", json=await build_full_payload(client))
    assert resp.status_code == 200

    data = resp.json()
    assert_plain_appointment(
        data,
        status="booked",
        priority=5,
        comment="Patient prefers video visits.",
        patient_instruction="Log in 10 minutes early",
    )

    # Check one representative assertion from each nested section instead of duplicating every nullable field.
    assert data["identifier"][0]["value"] == "APT-001"
    assert data["service_category"][0]["coding_code"] == "gp"
    assert data["service_type"][0]["coding_code"] == "tele"
    assert data["specialty"][0]["coding_code"] == "408443003"
    assert data["reason_code"][0]["coding_code"] == "386661006"
    assert data["reason_reference"][0]["reference_type"] == "Condition"
    assert data["supporting_information"][0]["reference_type"] == "DocumentReference"
    assert data["slot"][0]["reference_type"] == "Slot"
    assert data["based_on"][0]["reference_type"] == "ServiceRequest"
    assert data["participant"][0]["reference_type"] == "Patient"
    assert data["participant"][0]["required"] == "required"
    assert data["participant"][1]["types"][0]["coding_code"] == "ATND"
    assert data["requested_period"][0]["period_start"].startswith("2026-06-02T09:00:00")
    assert data["recurrence_template"]["weekly_template"]["monday"] is True


async def test_create_appointment_full_fhir_mapping(client):
    """FHIR mapping should reconstruct references and camelCase fields correctly."""
    resp = await client.post(BASE + "/", json=await build_full_payload(client), headers=FHIR_ACCEPT)
    assert resp.status_code == 200

    data = resp.json()
    assert_fhir_appointment(data, status="booked", description="Telehealth follow-up for ongoing symptoms")
    assert data["priority"] == 5
    assert data["comment"] == "Patient prefers video visits."
    assert data["patientInstruction"] == "Log in 10 minutes early"
    assert data["serviceType"][0]["coding"][0]["code"] == "tele"
    assert data["reasonCode"][0]["coding"][0]["code"] == "386661006"
    assert data["reasonReference"][0]["reference"] == "Condition/12345"
    assert data["supportingInformation"][0]["reference"] == "DocumentReference/456"
    assert data["slot"][0]["reference"] == "Slot/501"
    assert data["basedOn"][0]["reference"] == "ServiceRequest/80001"
    assert data["participant"][0]["actor"]["reference"].startswith("Patient/")
    assert data["participant"][0]["required"] == "required"
    assert data["participant"][1]["type"][0]["coding"][0]["code"] == "ATND"
    assert data["requestedPeriod"][0]["start"].startswith("2026-06-02T09:00:00")
    # recurrenceTemplate is operational, not a real R4/R5 element — must not appear in FHIR-format output.
    assert "recurrenceTemplate" not in data
    # subject/encounter/class/account/note/virtualService/replaces don't exist in R4 — must never be emitted.
    assert "subject" not in data
    assert "encounter" not in data
    assert "class" not in data
    assert "account" not in data
    assert "note" not in data
    assert "virtualService" not in data
    assert "replaces" not in data


async def test_create_appointment_invalid_reason_reference_rejected(client):
    """Closed-set reasonReference types must reject unsupported resource kinds."""
    payload = await build_full_payload(client)
    payload["reason_reference"][0]["reference"] = "Patient/123"
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_appointment_invalid_supporting_information_reference_rejected(client):
    """Open references still need the `ResourceType/id` shape."""
    payload = await build_full_payload(client)
    payload["supporting_information"][0]["reference"] = "bad-reference"
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_appointment_invalid_participant_reference_rejected(client):
    """Participant actor references are enum-validated and should reject unknown actor types."""
    payload = await build_full_payload(client)
    payload["participant"][0]["reference"] = "Organization/123"
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_appointment_requires_at_least_one_participant(client):
    """Participant is the one hard cardinality requirement on the create payload."""
    payload = await build_full_payload(client)
    payload["participant"] = []
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=400, response_status=resp.status_code)

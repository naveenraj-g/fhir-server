"""Real MedicationRequests for the tests of the resources that point at one.

`DetectedIssue.implicated` (a Reference(Any)), `ServiceRequest.basedOn` and `.supportingInfo`,
`Observation.basedOn` and `DiagnosticReport.basedOn` are existence-checked against the
MedicationRequest table. Those suites refer to medication requests by literal public ids
(`MedicationRequest/90001`, ...); each integration test runs on its own empty database and the
MedicationRequest public-id sequence starts at 90000, so creating a few MedicationRequests first
makes exactly those ids real. (The suite simulates sequences with a process-wide counter in
tests/conftest.py that keeps counting across tests, so the helper resets the MedicationRequest
counter first - safe because every test has a fresh database.) A test that needs a
MedicationRequest that does *not* exist uses a far-away id such as `MedicationRequest/999999`.
"""

MEDICATION_REQUESTS_URL = "/api/fhir/v1/medication-requests/"
SEEDED_FIRST_ID = 90000

MINIMAL = {
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {"text": "Aspirin"},
    "subject": {"reference": "https://other.example.org/fhir/Patient/1"},
}


async def create_minimal_medication_request(client) -> int:
    """Create one minimal MedicationRequest and return its public id. Needs
    `medication_request:create` on the current test user."""
    resp = await client.post(MEDICATION_REQUESTS_URL, json=MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def seed_medication_requests(client, count: int = 5) -> list[int]:
    """Create `count` minimal MedicationRequests (public ids 90000 .. 90000 + count - 1 on a
    fresh database) and return their ids."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("medication_request_pub_seq", None)
    ids = [await create_minimal_medication_request(client) for _ in range(count)]
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

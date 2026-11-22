"""Real ServiceRequests for the tests of the resources that point at one.

`Observation.basedOn`, `DiagnosticReport.basedOn`, `Procedure.basedOn`, `Encounter.basedOn`,
`Appointment.basedOn` and `Specimen.request` are existence-checked against the ServiceRequest
table. Those suites refer to service requests by literal public ids (`ServiceRequest/80001`, ...);
each integration test runs on its own empty database and the ServiceRequest public-id sequence
starts at 80000, so creating a few ServiceRequests first makes exactly those ids real. (The suite
simulates sequences with a process-wide counter in tests/conftest.py that keeps counting across
tests, so the helper resets the ServiceRequest counter first - safe because every test has a fresh
database.) A test that needs a ServiceRequest that does *not* exist uses a far-away id such as
`ServiceRequest/999999`.
"""

SERVICE_REQUESTS_URL = "/api/fhir/v1/service-requests/"
SEEDED_FIRST_ID = 80000


async def seed_service_requests(client, count: int = 5) -> list[int]:
    """Create `count` minimal ServiceRequests (public ids 80000 .. 80000 + count - 1 on a fresh
    database) and return their ids. Needs `service_request:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("service_request_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(
            SERVICE_REQUESTS_URL,
            json={
                "status": "active",
                "intent": "order",
                "subject": {"reference": "https://other.example.org/fhir/Patient/1"},
            },
        )
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

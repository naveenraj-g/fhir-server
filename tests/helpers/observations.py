"""Real Observations for the tests of the resources that point at one.

`DiagnosticReport.result`, `Immunization.reaction`, `reasonReference` and the like are
existence-checked against the Observation table. Those suites were written when an Observation
reference was stored as sent, so they refer to Observations by literal public ids
(`Observation/160001`, `Observation/160009`, ...). Each integration test runs on its own empty
database, and the Observation public-id sequence starts at 160000, so creating a handful of
Observations first makes exactly those ids real. (The suite simulates sequences with a
process-wide counter in tests/conftest.py that keeps counting across tests, so the helper resets
the Observation counter first — safe because every test has a fresh database.) A test that needs
an Observation that does *not* exist uses a far-away id such as `Observation/999999`.
"""

OBSERVATIONS_URL = "/api/fhir/v1/observations/"
SEEDED_FIRST_ID = 160000


async def seed_observations(client, count: int = 10) -> list[int]:
    """Create `count` minimal Observations (public ids 160000 .. 160000 + count - 1 on a fresh
    database) and return their ids. Needs `observation:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("observation_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(
            OBSERVATIONS_URL,
            json={"status": "final", "code": {"text": "Seeded observation"}},
        )
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

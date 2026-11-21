"""Real Specimens for the tests of the resources that point at one.

`Observation.specimen` and `DiagnosticReport.specimen` are existence-checked against the Specimen
table. Those suites refer to specimens by literal public ids (`Specimen/310001`, ...); each
integration test runs on its own empty database and the Specimen public-id sequence starts at
310000, so creating a few Specimens first makes exactly those ids real. (The suite simulates
sequences with a process-wide counter in tests/conftest.py that keeps counting across tests, so
the helper resets the Specimen counter first — safe because every test has a fresh database.) A
test that needs a Specimen that does *not* exist uses a far-away id such as `Specimen/999999`.
"""

SPECIMENS_URL = "/api/fhir/v1/specimens/"
SEEDED_FIRST_ID = 310000


async def seed_specimens(client, count: int = 5) -> list[int]:
    """Create `count` empty Specimens (public ids 310000 .. 310000 + count - 1 on a fresh
    database) and return their ids. Needs `specimen:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("specimen_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(SPECIMENS_URL, json={"status": "available"})
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

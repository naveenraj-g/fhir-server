"""Real Encounters for the tests of the resources that point at one with a literal public id.

A relative `Encounter/<id>` is existence-checked on write (see app/repository/_reference_check.py).
The Appointment suite refers to `Encounter/20001` in `supportingInformation`; each integration test
runs on its own empty database and the Encounter public-id sequence starts at 20000, so creating a
few Encounters first makes exactly that id real. (The suite simulates sequences with a process-wide
counter in tests/conftest.py that keeps counting across tests, so the helper resets the Encounter
counter first - safe because every test has a fresh database.) A test that needs an Encounter that
does *not* exist uses a far-away id such as `Encounter/999999`.
"""

ENCOUNTERS_URL = "/api/fhir/v1/encounters/"
SEEDED_FIRST_ID = 20000


async def seed_encounters(client, count: int = 3) -> list[int]:
    """Create `count` minimal Encounters (public ids 20000 .. 20000 + count - 1 on a fresh
    database) and return their ids. Needs `encounter:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("encounter_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(
            ENCOUNTERS_URL,
            json={
                "status": "in-progress",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                },
            },
        )
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

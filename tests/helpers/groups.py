"""Real Groups for the tests of the resources that can have a Group as their subject.

A relative `Group/<id>` is existence-checked on write (see app/repository/_reference_check.py). Those
suites refer to groups by the literal public id `Group/430001`; each integration test runs on its own
empty database and the Group public-id sequence starts at 430000, so creating a few Groups first makes
exactly those ids real. (The suite simulates sequences with a process-wide counter in
tests/conftest.py that keeps counting across tests, so the helper resets the Group counter first -
safe because every test has a fresh database.) A test that needs a Group that does *not* exist uses a
far-away id such as `Group/999999`.
"""

GROUPS_URL = "/api/fhir/v1/groups/"
SEEDED_FIRST_ID = 430000


async def seed_groups(client, count: int = 3) -> list[int]:
    """Create `count` minimal Groups (public ids 430000 .. 430000 + count - 1 on a fresh database)
    and return their ids. Needs `group:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("group_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(GROUPS_URL, json={"type": "person", "actual": True})
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

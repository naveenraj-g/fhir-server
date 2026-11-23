"""Real EpisodeOfCares for the tests of the resources that can point at one.

A relative `EpisodeOfCare/<id>` is existence-checked on write (see app/repository/_reference_check.py).
Encounter's suites refer to episodes by the literal public id `EpisodeOfCare/350001`; each integration
test runs on its own empty database and the EpisodeOfCare public-id sequence starts at 350000, so
creating a few episodes first makes exactly those ids real. (The suite simulates sequences with a
process-wide counter in tests/conftest.py that keeps counting across tests, so the helper resets the
counter first - safe because every test has a fresh database.) A test that needs an episode that does
*not* exist uses a far-away id such as `EpisodeOfCare/999999`.
"""

EPISODES_URL = "/api/fhir/v1/episodes-of-care/"
SEEDED_FIRST_ID = 350000


async def seed_episodes_of_care(client, count: int = 3) -> list[int]:
    """Create `count` minimal EpisodeOfCares (public ids 350000 .. 350000 + count - 1 on a fresh
    database) and return their ids. Needs `episode_of_care:create` on the current test user."""
    from tests.conftest import _seq_counters

    _seq_counters.pop("episode_of_care_pub_seq", None)
    ids = []
    for _ in range(count):
        resp = await client.post(
            EPISODES_URL,
            json={
                "status": "active",
                "patient": {"reference": "https://other.example.org/fhir/Patient/1"},
            },
        )
        assert resp.status_code == 201, resp.text
        ids.append(int(resp.json()["id"]))
    assert ids[0] == SEEDED_FIRST_ID, ids
    return ids

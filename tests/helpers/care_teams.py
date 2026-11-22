"""CareTeam as a performer, for the tests of the resources that can point at one.

`DiagnosticReport.performer` / `.resultsInterpreter`, `Observation.performer`,
`ServiceRequest.performer` and `MedicationRequest.performer` (searched as `intended-performer`)
are existence-checked against the CareTeam table, and the engine follows the reference
(`<param>:CareTeam.status=`, `_include=<Type>:<param>`, and `CareTeam?_revinclude=<Type>:<param>`).
Needs `care_team:create` and `care_team:read` on the current test user.
"""

CARE_TEAMS_URL = "/api/fhir/v1/care-teams/"


async def create_minimal_care_team(client, status: str = "active") -> int:
    """Create a CareTeam with the given status and return its public id."""
    resp = await client.post(CARE_TEAMS_URL, json={"status": status})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


def _match_ids(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


async def exercise_care_team_performer(
    client, *, route: str, rtype: str, param: str, body_with
):
    """Check CareTeam as a performer of `rtype` (served at `route`, e.g. `/api/fhir/v1/observations`)
    through the search parameter `param`. `body_with(reference)` builds a valid body of that
    resource whose performer element holds `{"reference": reference}`."""
    team = await create_minimal_care_team(client)
    other = await create_minimal_care_team(client, status="inactive")
    url = route.rstrip("/") + "/"

    # existence-checked on write
    ok = await client.post(url, json=body_with(f"CareTeam/{team}"))
    assert ok.status_code == 201, ok.text
    resource = ok.json()["id"]
    missing = await client.post(url, json=body_with("CareTeam/999999"))
    assert missing.status_code == 422, missing.text

    def ids(bundle):
        return _match_ids(bundle, rtype, "match")

    # searched by type and id, and chained into the CareTeam registry
    found = (await client.get(url, params={param: f"CareTeam/{team}"})).json()
    assert ids(found) == {resource}
    assert (
        ids((await client.get(url, params={param: f"CareTeam/{other}"})).json())
        == set()
    )
    chained = await client.get(url, params={f"{param}:CareTeam.status": "active"})
    assert chained.status_code == 200 and ids(chained.json()) == {resource}
    other_status = await client.get(
        url, params={f"{param}:CareTeam.status": "inactive"}
    )
    assert ids(other_status.json()) == set()

    # `_include` brings the care team in; `CareTeam?_revinclude` brings the resource in
    included = (
        await client.get(url, params={"_id": resource, "_include": f"{rtype}:{param}"})
    ).json()
    assert _match_ids(included, "CareTeam", "include") == {str(team)}
    reverse = (
        await client.get(
            CARE_TEAMS_URL, params={"_id": team, "_revinclude": f"{rtype}:{param}"}
        )
    ).json()
    assert _match_ids(reverse, rtype, "include") == {resource}

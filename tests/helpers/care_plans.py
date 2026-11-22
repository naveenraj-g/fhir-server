"""CarePlan as the target of `basedOn`, for the tests of the resources that can point at one.

`Observation.basedOn`, `DiagnosticReport.basedOn`, `Procedure.basedOn` and `ServiceRequest.basedOn`
(and `MedicationRequest.basedOn`, which has no `based-on` search parameter) are existence-checked
against the CarePlan table; for the first four the engine also follows the reference
(`based-on:CarePlan.status=`, `_include=<Type>:based-on`, and `CarePlan?_revinclude=<Type>:based-on`).
Needs `care_plan:create` and `care_plan:read` on the current test user. (Encounter and Appointment
cannot carry a CarePlan: R4 limits their `basedOn` to ServiceRequest.)
"""

CARE_PLANS_URL = "/api/fhir/v1/care-plans/"


async def create_minimal_care_plan(client, status: str = "active") -> int:
    """Create a CarePlan (an absolute subject is not existence-checked) and return its id."""
    resp = await client.post(
        CARE_PLANS_URL,
        json={
            "status": status,
            "intent": "plan",
            "subject": {"reference": "https://other.example.org/fhir/Patient/1"},
        },
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


def _match_ids(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


async def exercise_based_on_care_plan(client, *, route: str, rtype: str, body_with):
    """Check CarePlan as a `basedOn` target of `rtype` (served at `route`, e.g.
    `/api/fhir/v1/procedures`). `body_with(based_on)` builds a valid body of that resource with
    the given `basedOn` list."""
    plan = await create_minimal_care_plan(client)
    other = await create_minimal_care_plan(client, status="completed")
    url = route.rstrip("/") + "/"

    # existence-checked on write
    ok = await client.post(url, json=body_with([{"reference": f"CarePlan/{plan}"}]))
    assert ok.status_code == 201, ok.text
    resource = ok.json()["id"]
    missing = await client.post(url, json=body_with([{"reference": "CarePlan/999999"}]))
    assert missing.status_code == 422, missing.text

    def ids(bundle):
        return {
            e["resource"]["id"]
            for e in bundle.get("entry") or []
            if e["search"]["mode"] == "match"
        }

    # searched by type and id, and chained into the CarePlan registry
    found = (await client.get(url, params={"based-on": f"CarePlan/{plan}"})).json()
    assert ids(found) == {resource}
    assert (await client.get(url, params={"based-on": f"CarePlan/{other}"})).json().get(
        "total"
    ) == 0
    chained = await client.get(url, params={"based-on:CarePlan.status": "active"})
    assert chained.status_code == 200 and ids(chained.json()) == {resource}
    other_status = await client.get(
        url, params={"based-on:CarePlan.status": "completed"}
    )
    assert ids(other_status.json()) == set()

    # `_include` brings the care plan in; `CarePlan?_revinclude` brings the resource in
    included = (
        await client.get(url, params={"_id": resource, "_include": f"{rtype}:based-on"})
    ).json()
    assert _match_ids(included, "CarePlan", "include") == {str(plan)}
    reverse = (
        await client.get(
            CARE_PLANS_URL, params={"_id": plan, "_revinclude": f"{rtype}:based-on"}
        )
    ).json()
    assert _match_ids(reverse, rtype, "include") == {resource}

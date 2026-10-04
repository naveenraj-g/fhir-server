"""Base R4 structural validation (app.fhir.validation.validate_base_r4),
wired into OrganizationService.create_organization/patch_organization.

This layer catches what Pydantic's own CreateSchema/PatchSchema can't:
structural rules expressed only in HL7's fhir.schema.json, not in this
project's input types. The clearest example — and what these tests exercise
— is FHIR's `dateTime` primitive, which requires a timezone offset whenever
a time-of-day is present; Python's `datetime` type (what period_start/
period_end are typed as) has no such requirement, so a timezone-naive
instant sails through Pydantic but fails the FHIR schema once converted.
"""

from tests.integration.organization.support import BASE, MINIMAL, create_organization


async def test_create_rejects_naive_datetime_period(client):
    """period_start with no UTC offset passes Pydantic's `datetime` type but
    violates FHIR's dateTime primitive pattern — the base R4 validator must
    catch it before anything is written."""
    payload = {
        **MINIMAL,
        "identifier": [
            {
                "system": "http://example.org/ids",
                "value": "123",
                "period_start": "2024-01-01T00:00:00",
            }
        ],
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["resourceType"] == "OperationOutcome"
    assert any(
        "identifier.0.period.start" in issue.get("expression", [])
        for issue in body["issue"]
    )


async def test_create_accepts_tz_aware_datetime_period(client):
    """Same field, with a UTC offset, must pass."""
    payload = {
        **MINIMAL,
        "identifier": [
            {
                "system": "http://example.org/ids",
                "value": "123",
                "period_start": "2024-01-01T00:00:00+00:00",
            }
        ],
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text


async def test_patch_rejects_naive_datetime_period(client):
    """A PATCH that only supplies the offending field must be caught too —
    exercises the merge-onto-current-state path, not just full-payload
    CREATE validation."""
    org_id = await create_organization(client)
    resp = await client.patch(
        f"{BASE}/{org_id}",
        json={
            "identifier": [
                {
                    "system": "http://example.org/ids",
                    "value": "123",
                    "period_start": "2024-01-01T00:00:00",
                }
            ]
        },
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["resourceType"] == "OperationOutcome"


async def test_patch_unrelated_field_unaffected_by_validation(client):
    """A normal partial update that doesn't touch anything invalid must
    still succeed — the merge must not accidentally drag in unrelated
    validation failures."""
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"name": "Renamed Hospital"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed Hospital"

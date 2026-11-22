"""The shared write-time reference check, run against every rebuilt resource.

A relative `Type/<id>` reference to a rebuilt resource must exist in the caller's org, wherever it
sits in the document. The same probe is used on every resource: its valid minimal body plus an
`extension` carrying `valueReference` (a Reference every DomainResource may have), pointing at an id
that does not exist. If a resource's write path did not run the shared check, it would be stored.

See app/repository/_reference_check.py for the rule, and cases.py for the per-resource bodies.
"""

import pytest

from app.repository._reference_check import checkable_types
from tests.integration.reference_check.cases import CASES

PROBE_URL = "https://fhir-server.dev/fhir/StructureDefinition/reference-check-probe"


def with_reference(body: dict, reference: str) -> dict:
    """`body` with one more extension holding `{"reference": reference}`."""
    probe = {"url": PROBE_URL, "valueReference": {"reference": reference}}
    return {**body, "extension": [*(body.get("extension") or []), probe]}


def test_every_checkable_type_has_a_case():
    """Adding a rebuilt resource without a minimal body here would leave it untested."""
    assert set(CASES) == set(checkable_types())


@pytest.mark.parametrize("resource_type", sorted(CASES))
async def test_a_dangling_reference_is_rejected_on_create(client, resource_type):
    route, make = CASES[resource_type]
    url = route + "/"

    # the probe body is valid on its own, so a 422 below is about the reference
    baseline = await client.post(url, json=await make(client))
    assert baseline.status_code == 201, baseline.text

    for target in sorted(checkable_types()):
        body = with_reference(await make(client), f"{target}/999999")
        resp = await client.post(url, json=body)
        assert resp.status_code == 422, (target, resp.text)
        assert f"{target}/999999 does not exist" in resp.text, (target, resp.text)


@pytest.mark.parametrize("resource_type", sorted(CASES))
async def test_a_reference_to_an_existing_resource_is_accepted_and_patch_is_checked(
    client, resource_type
):
    """The resource's own type, which it can always create: an existing target is accepted on
    create, and a dangling one is rejected on patch too (the stored document is left alone)."""
    route, make = CASES[resource_type]
    url = route + "/"
    first = (await client.post(url, json=await make(client))).json()["id"]

    ok = await client.post(
        url, json=with_reference(await make(client), f"{resource_type}/{first}")
    )
    assert ok.status_code == 201, ok.text

    patch = {"extension": with_reference({}, f"{resource_type}/999999")["extension"]}
    resp = await client.patch(f"{route}/{first}", json=patch)
    assert resp.status_code == 422, resp.text
    stored = (await client.get(f"{route}/{first}")).json()
    assert "extension" not in stored

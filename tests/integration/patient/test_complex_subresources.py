"""Patient sub-resource coverage for the richer/complex child types."""

from tests.integration.patient.support import BASE, FHIR_ACCEPT, MINIMAL, create_patient, get_first_child_id


async def test_add_and_list_photo(client):
    patient_id = await create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/photos",
        json={
            "content_type": "image/png",
            "language": "en",
            "data": "ZmFrZS1pbWFnZS1kYXRh",
            "url": "https://example.com/photo.png",
            "size": 15,
            "hash": "ZmFrZS1oYXNo",
            "title": "Profile photo",
            "creation": "2025-01-02T03:04:05",
        },
    )
    assert resp.status_code == 200
    list_resp = await client.get(f"{BASE}/{patient_id}/photos")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["content_type"] == "image/png"
    assert data["data"][0]["title"] == "Profile photo"


async def test_list_patient_photos_fhir(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/photos",
        json={"content_type": "image/jpeg", "title": "FHIR photo", "url": "https://example.com/fhir-photo.png"},
    )
    resp = await client.get(f"{BASE}/{patient_id}/photos", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["contentType"] == "image/jpeg"
    assert data["data"][0]["title"] == "FHIR photo"


async def test_delete_patient_photo(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/photos",
        json={"title": "Delete Me", "url": "https://example.com/delete-me.png"},
    )
    photo_id = await get_first_child_id(client, f"{BASE}/{patient_id}/photos")
    assert (await client.delete(f"{BASE}/{patient_id}/photos/{photo_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/photos")).json()["total"] == 0


async def test_add_and_list_contact(client):
    patient_id = await create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/contacts",
        json={
            "relationship": [
                {
                    "coding_system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                    "coding_code": "N",
                    "coding_display": "Next-of-kin",
                    "text": "Next-of-kin",
                }
            ],
            "name_use": "official",
            "name_family": "Caregiver",
            "name_given": ["Casey"],
            "telecom": [{"system": "phone", "value": "+1-555-1111", "use": "mobile"}],
            "address_use": "home",
            "address_type": "physical",
            "address_line": ["1 Contact St"],
            "address_city": "Seattle",
            "address_state": "WA",
            "address_postal_code": "98101",
            "address_country": "US",
            "gender": "female",
        },
    )
    assert resp.status_code == 200
    list_resp = await client.get(f"{BASE}/{patient_id}/contacts")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    contact = data["data"][0]
    assert contact["name_family"] == "Caregiver"
    assert contact["relationship"][0]["coding_code"] == "N"
    assert contact["telecom"][0]["value"] == "+1-555-1111"


async def test_list_patient_contacts_fhir(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/contacts",
        json={
            "name_family": "FHIRContact",
            "name_given": ["Taylor"],
            "address_type": "physical",
            "address_city": "Seattle",
            "address_state": "WA",
            "address_postal_code": "98101",
            "address_country": "US",
        },
    )
    resp = await client.get(f"{BASE}/{patient_id}/contacts", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["name"]["family"] == "FHIRContact"


async def test_delete_patient_contact(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/contacts",
        json={
            "name_family": "Delete Contact",
            "address_type": "physical",
            "address_city": "Seattle",
            "address_state": "WA",
            "address_postal_code": "98101",
            "address_country": "US",
        },
    )
    contact_id = await get_first_child_id(client, f"{BASE}/{patient_id}/contacts")
    assert (await client.delete(f"{BASE}/{patient_id}/contacts/{contact_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/contacts")).json()["total"] == 0


async def test_add_and_list_communication(client):
    patient_id = await create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/communications",
        json={
            "language_system": "urn:ietf:bcp:47",
            "language_code": "en",
            "language_display": "English",
            "language_text": "English",
            "preferred": True,
        },
    )
    assert resp.status_code == 200
    list_resp = await client.get(f"{BASE}/{patient_id}/communications")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["language_code"] == "en"
    assert data["data"][0]["preferred"] is True


async def test_list_patient_communications_fhir(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/communications",
        json={"language_system": "urn:ietf:bcp:47", "language_code": "fr", "language_display": "French"},
    )
    resp = await client.get(f"{BASE}/{patient_id}/communications", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["language"]["coding"][0]["code"] == "fr"


async def test_delete_patient_communication(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/communications",
        json={"language_system": "urn:ietf:bcp:47", "language_code": "de", "language_display": "German"},
    )
    comm_id = await get_first_child_id(client, f"{BASE}/{patient_id}/communications")
    assert (await client.delete(f"{BASE}/{patient_id}/communications/{comm_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/communications")).json()["total"] == 0


async def test_add_and_list_general_practitioner(client):
    # Uses the identifier-fallback path (no reference_type/reference_id) since
    # this test suite only holds patient:* permissions — there's no
    # Practitioner/Organization/PractitionerRole resource to resolve a real
    # reference against. This is the documented fallback for a reference to a
    # resource that isn't (yet) modeled in this system.
    patient_id = await create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={
            "reference_display": "Dr. Green",
            "reference_identifier_system": "http://hl7.org/fhir/sid/us-npi",
            "reference_identifier_value": "9999999999",
        },
    )
    assert resp.status_code == 200
    list_resp = await client.get(f"{BASE}/{patient_id}/general-practitioners")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["reference_display"] == "Dr. Green"
    assert data["data"][0]["reference_identifier_value"] == "9999999999"


async def test_list_patient_general_practitioners_fhir(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={
            "reference_display": "External GP",
            "reference_identifier_system": "http://hl7.org/fhir/sid/us-npi",
            "reference_identifier_value": "8888888888",
        },
    )
    resp = await client.get(f"{BASE}/{patient_id}/general-practitioners", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["display"] == "External GP"
    assert data["data"][0]["identifier"]["value"] == "8888888888"


async def test_delete_patient_general_practitioner(client):
    patient_id = await create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={
            "reference_display": "Delete Me GP",
            "reference_identifier_system": "http://hl7.org/fhir/sid/us-npi",
            "reference_identifier_value": "7777777777",
        },
    )
    gp_id = await get_first_child_id(client, f"{BASE}/{patient_id}/general-practitioners")
    assert (await client.delete(f"{BASE}/{patient_id}/general-practitioners/{gp_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/general-practitioners")).json()["total"] == 0


async def test_add_and_list_link(client):
    patient_id = await create_patient(client)
    other_id = await create_patient(client, {**MINIMAL, "user_id": "u-link-other-1"})
    resp = await client.post(
        f"{BASE}/{patient_id}/links",
        json={"other_type": "Patient", "other_id": other_id, "other_display": "Linked patient", "type": "seealso"},
    )
    assert resp.status_code == 200
    list_resp = await client.get(f"{BASE}/{patient_id}/links")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["other_type"] == "Patient"
    assert data["data"][0]["other_id"] == other_id
    assert data["data"][0]["type"] == "seealso"


async def test_list_patient_links_fhir(client):
    patient_id = await create_patient(client)
    other_id = await create_patient(client, {**MINIMAL, "user_id": "u-link-other-2"})
    await client.post(f"{BASE}/{patient_id}/links", json={"other_type": "Patient", "other_id": other_id, "type": "refer"})
    resp = await client.get(f"{BASE}/{patient_id}/links", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["other"]["reference"] == f"Patient/{other_id}"
    assert data["data"][0]["type"] == "refer"


async def test_delete_patient_link(client):
    patient_id = await create_patient(client)
    other_id = await create_patient(client, {**MINIMAL, "user_id": "u-link-other-3"})
    await client.post(f"{BASE}/{patient_id}/links", json={"other_type": "Patient", "other_id": other_id, "type": "replaces"})
    link_id = await get_first_child_id(client, f"{BASE}/{patient_id}/links")
    assert (await client.delete(f"{BASE}/{patient_id}/links/{link_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/links")).json()["total"] == 0

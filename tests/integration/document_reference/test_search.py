"""FHIR R4 search over DocumentReference (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/documentreference.html#search).

One block per search parameter - `status` a code, `date` an instant, `period` a Period,
`description` a string, `location` a uri, the token parameters (`type`, `category`,
`security-label`, `event`, `facility`, `setting`, `format`, `identifier`, and the code-only
`contenttype` / `language`), the references (`subject`, `patient`, `author`, `authenticator`,
`custodian`, `encounter`, `related`, `relatesto`) and the `relation` / `relationship` pair - then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search.
"""

import pytest

from tests.integration.document_reference.support import (
    ACT_CODE,
    API,
    BASE,
    CONFIDENTIALITY,
    DOC_IDS,
    FORMAT,
    FORMAT_SYSTEM,
    LOINC,
    RELATION_SYSTEM,
    SCT,
    STATUS_SYSTEM,
    V2_0203,
    concept,
    condition_body,
    content_entry,
    create_condition,
    create_document,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    document_body,
    encounter_body,
    group_body,
    related_person_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


async def _create_episode(client) -> int:
    resp = await client.post(
        f"{API}/episodes-of-care/",
        json={
            "status": "active",
            "patient": {"reference": "https://other.example.org/fhir/Patient/1"},
        },
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


@pytest.fixture
async def world(client):
    """An organization pair, a practitioner, a role, two patients, a related person, a group, a
    condition, an encounter and an episode of care, plus five documents with distinct, searchable
    values. Returns {key: id}.

      a  current, LOINC type 34133-9, category report, identifier DOC-A (master identifier
         urn:oid:master-a), patient 1, 2026-02-01, authors a practitioner and org 1, authenticated
         by the practitioner, custodian org 1, "Discharge summary", label N, one pdf in English
         with a url and a format, encounter 1, event AMB, a Period, facility, setting, related to
         a condition, relatesTo b with `replaces`
      b  superseded, type 11488-4, patient 2, 2025-06-01, author patient 2, "Consult note", one
         text/plain in French, episode of care, no relatesTo
      c  current, subject the group, 2024, author a role, custodian org 2, "Radiology report",
         two contents (a png and a pdf), relatesTo a with `transforms` and b with `appends`
      d  entered-in-error, subject a practitioner, logical author and custodian, no date, no
         description
      e  only what makes it a document
    """
    w = {}
    w["org1"] = await create_organization(client, name="Providing Org")
    w["org2"] = await create_organization(client, name="Other Hospital")
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{w['pr']}"}}
    )
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["rel"] = await create_related_person(client, related_person_body(w["p1"]))
    w["grp"] = await create_group(client, group_body(type="person"))
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["enc"] = await create_encounter(client, encounter_body())
    w["eoc"] = await _create_episode(client)

    w["e"] = await create_document(
        client, document_body(content=[content_entry("text/html")])
    )
    w["d"] = await create_document(
        client,
        document_body(
            status="entered-in-error",
            subject={"reference": f"Practitioner/{w['pr']}"},
            author=[{"identifier": {"system": "urn:pr", "value": "P-LOGICAL"}}],
            custodian={"identifier": {"system": "urn:org", "value": "O-LOGICAL"}},
            content=[content_entry("application/pdf")],
        ),
    )
    w["b"] = await create_document(
        client,
        document_body(
            status="superseded",
            type=concept(LOINC, "11488-4", "Consult note"),
            subject={"reference": f"Patient/{w['p2']}"},
            date="2025-06-01T09:00:00Z",
            author=[{"reference": f"Patient/{w['p2']}"}],
            description="Consult note",
            content=[
                content_entry(
                    "text/plain", language="fr", url="https://docs.example.org/b.txt"
                )
            ],
            context={"encounter": [{"reference": f"EpisodeOfCare/{w['eoc']}"}]},
        ),
    )
    w["a"] = await create_document(
        client,
        document_body(
            masterIdentifier={
                "system": "urn:ietf:rfc:3986",
                "value": "urn:oid:master-a",
            },
            identifier=[
                {
                    "system": DOC_IDS,
                    "value": "DOC-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "ACSN"}],
                        "text": "Accession number",
                    },
                }
            ],
            type=concept(LOINC, "34133-9", "Summarization of episode note"),
            category=[concept(LOINC, "LP173421-1", "Report")],
            subject={"reference": f"Patient/{w['p1']}"},
            date="2026-02-01T10:00:00Z",
            author=[
                {"reference": f"Practitioner/{w['pr']}"},
                {"reference": f"Organization/{w['org1']}"},
            ],
            authenticator={"reference": f"Practitioner/{w['pr']}"},
            custodian={"reference": f"Organization/{w['org1']}"},
            description="Discharge summary",
            securityLabel=[concept(CONFIDENTIALITY, "N", "normal")],
            content=[
                {
                    "attachment": {
                        "contentType": "application/pdf",
                        "language": "en",
                        "url": "https://docs.example.org/a.pdf",
                    },
                    "format": {
                        "system": FORMAT_SYSTEM,
                        "code": FORMAT,
                        "display": "H&P note",
                    },
                }
            ],
            context={
                "encounter": [{"reference": f"Encounter/{w['enc']}"}],
                "event": [concept(ACT_CODE, "AMB", "ambulatory")],
                "period": {"start": "2026-01-30", "end": "2026-02-01"},
                "facilityType": concept(SCT, "22232009", "Hospital"),
                "practiceSetting": concept(
                    SCT, "408443003", "General medical practice"
                ),
                "related": [{"reference": f"Condition/{w['cond']}"}],
            },
            relatesTo=[
                {
                    "code": "replaces",
                    "target": {"reference": f"DocumentReference/{w['b']}"},
                }
            ],
        ),
    )
    w["c"] = await create_document(
        client,
        document_body(
            subject={"reference": f"Group/{w['grp']}"},
            date="2024-03-15T12:00:00Z",
            author=[{"reference": f"PractitionerRole/{w['role']}"}],
            custodian={"reference": f"Organization/{w['org2']}"},
            description="Radiology report",
            content=[
                content_entry("image/png", url="https://docs.example.org/c1.png"),
                content_entry(
                    "application/pdf", url="https://docs.example.org/files/c2.pdf"
                ),
            ],
            relatesTo=[
                {
                    "code": "transforms",
                    "target": {"reference": f"DocumentReference/{w['a']}"},
                },
                {
                    "code": "appends",
                    "target": {"reference": f"DocumentReference/{w['b']}"},
                },
            ],
        ),
    )
    return w


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    ids = _ids(await _search(client, **params))
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in ids}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


async def _other(client, path: str, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    both = f"{world['a']},{world['b']}"
    assert await _keys(client, world, _id=both) == {"a", "b"}
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}
    assert await _keys(client, world, _id="999999") == set()


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# -- status ---------------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="superseded") == {"b"}
    assert await _keys(client, world, status="entered-in-error") == {"d"}
    assert await _keys(client, world, status="current") == {"a", "c", "e"}
    assert await _keys(client, world, status="superseded,entered-in-error") == {
        "b",
        "d",
    }
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|current") == {
        "a",
        "c",
        "e",
    }
    assert await _keys(client, world, status="http://wrong|current") == set()
    assert await _keys(client, world, status="|current") == set()
    assert await _keys(client, world, status="retired") == set()  # unknown code
    assert await _keys(client, world, **{"status:not": "current"}) == {"b", "d"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


# -- date (an instant) / period (a Period) --------------------------------------------------


async def test_date(client, world):
    assert await _keys(client, world, date="2026-02-01") == {"a"}
    assert await _keys(client, world, date="2026") == {"a"}
    assert await _keys(client, world, date="ge2025-01-01") == {"a", "b"}
    assert await _keys(client, world, date="lt2025-01-01") == {"c"}
    assert await _keys(client, world, date="gt2025-06-01T09:00:00Z") == {"a"}
    assert await _keys(client, world, date="le2025-06-01T09:00:00Z") == {"b", "c"}
    assert await _keys(client, world, date=["ge2024-01-01", "lt2026-01-01"]) == {
        "b",
        "c",
    }
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {"a", "b", "c"}


async def test_period_is_a_period_search(client, world):
    # only a has a context period (2026-01-30 .. 2026-02-01)
    assert await _keys(client, world, period="2026") == {
        "a"
    }  # the year holds the period
    assert (
        await _keys(client, world, period="2026-01-30") == set()
    )  # a day cannot hold it
    assert await _keys(client, world, period="ge2026-01-31") == {"a"}
    assert await _keys(client, world, period="le2026-01-30") == {"a"}
    assert await _keys(client, world, period="gt2026-02-05") == set()
    assert await _keys(client, world, period="sa2026-01-01") == {"a"}
    assert await _keys(client, world, period="eb2026-01-01") == set()
    assert await _keys(client, world, **{"period:missing": "true"}) == ALL - {"a"}


# -- description (a string) -----------------------------------------------------------------


async def test_description(client, world):
    assert await _keys(client, world, description="Discharge") == {"a"}
    assert await _keys(client, world, description="discharge sum") == {
        "a"
    }  # case-insensitive
    assert (
        await _keys(client, world, description="summary") == set()
    )  # starts-with, not contains
    assert await _keys(client, world, **{"description:contains": "summary"}) == {"a"}
    assert await _keys(client, world, **{"description:exact": "Consult note"}) == {"b"}
    assert await _keys(client, world, **{"description:exact": "consult note"}) == set()
    assert await _keys(client, world, description="Consult,Radiology") == {"b", "c"}
    assert await _keys(client, world, **{"description:missing": "true"}) == {"d", "e"}


# -- identifier (masterIdentifier and identifier) / tokens ----------------------------------


async def test_identifier_reads_master_identifier_and_identifier(client, world):
    assert await _keys(client, world, identifier="DOC-A") == {"a"}
    assert await _keys(client, world, identifier="urn:oid:master-a") == {"a"}
    assert await _keys(client, world, identifier=f"{DOC_IDS}|DOC-A") == {"a"}
    assert await _keys(
        client, world, identifier="urn:ietf:rfc:3986|urn:oid:master-a"
    ) == {"a"}
    assert await _keys(client, world, identifier="http://wrong|DOC-A") == set()
    assert await _keys(client, world, identifier=f"{DOC_IDS}|") == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|DOC-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|MR|DOC-A"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "Accession"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "DOC-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {"a"}


async def test_type(client, world):
    assert await _keys(client, world, type="34133-9") == {"a"}
    assert await _keys(client, world, type=f"{LOINC}|11488-4") == {"b"}
    assert await _keys(client, world, type="34133-9,11488-4") == {"a", "b"}
    assert await _keys(client, world, type="http://wrong|34133-9") == set()
    assert await _keys(client, world, type=f"{LOINC}|") == {"a", "b"}
    assert await _keys(client, world, **{"type:text": "Consult"}) == {"b"}
    assert await _keys(client, world, **{"type:not": "34133-9"}) == ALL - {"a"}
    assert await _keys(client, world, **{"type:missing": "true"}) == {"c", "d", "e"}


async def test_category_security_label_event_facility_setting(client, world):
    assert await _keys(client, world, category="LP173421-1") == {"a"}
    assert await _keys(client, world, **{"category:missing": "true"}) == ALL - {"a"}
    assert await _keys(client, world, **{"security-label": f"{CONFIDENTIALITY}|N"}) == {
        "a"
    }
    assert await _keys(client, world, **{"security-label": "R"}) == set()
    assert await _keys(client, world, event="AMB") == {"a"}
    assert await _keys(client, world, **{"event:text": "ambul"}) == {"a"}
    assert await _keys(client, world, facility="22232009") == {"a"}
    assert await _keys(client, world, setting=f"{SCT}|408443003") == {"a"}
    assert await _keys(client, world, **{"setting:missing": "true"}) == ALL - {"a"}


async def test_format_is_a_coding_on_the_content(client, world):
    assert await _keys(client, world, format=FORMAT) == {"a"}
    assert await _keys(client, world, format=f"{FORMAT_SYSTEM}|{FORMAT}") == {"a"}
    assert await _keys(client, world, format="http://wrong|" + FORMAT) == set()
    assert await _keys(client, world, **{"format:text": "H&P"}) == {"a"}
    assert await _keys(client, world, **{"format:missing": "true"}) == ALL - {"a"}


async def test_contenttype_and_language_match_the_code_only(client, world):
    assert await _keys(client, world, contenttype="application/pdf") == {"a", "c", "d"}
    assert await _keys(client, world, contenttype="text/plain,image/png") == {"b", "c"}
    assert await _keys(client, world, contenttype="text/html") == {"e"}
    # a code of this kind has no system: a system|code value never matches
    assert await _keys(client, world, contenttype="urn:x|application/pdf") == set()
    assert await _keys(client, world, **{"contenttype:not": "application/pdf"}) == {
        "b",
        "e",
    }
    assert await _keys(client, world, language="en") == {"a"}
    assert await _keys(client, world, language="fr") == {"b"}
    assert await _keys(client, world, **{"language:missing": "true"}) == {"c", "d", "e"}


async def test_every_content_entry_is_searched(client, world):
    # c has two contents: a png and a pdf (its second one has its own url)
    assert await _keys(client, world, contenttype="image/png") == {"c"}
    assert await _keys(
        client, world, location="https://docs.example.org/files/c2.pdf"
    ) == {"c"}
    assert await _keys(client, world, location="https://docs.example.org/c1.png") == {
        "c"
    }


# -- location (a uri) -----------------------------------------------------------------------


async def test_location_is_a_uri_search(client, world):
    assert await _keys(client, world, location="https://docs.example.org/a.pdf") == {
        "a"
    }
    assert (
        await _keys(client, world, location="https://docs.example.org/A.pdf") == set()
    )
    assert await _keys(
        client, world, **{"location:below": "https://docs.example.org/"}
    ) == {
        "a",
        "b",
        "c",
    }
    assert await _keys(
        client, world, **{"location:below": "https://docs.example.org/files"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"location:above": "https://docs.example.org/b.txt/page/2"}
    ) == {"b"}
    assert await _keys(client, world, **{"location:missing": "true"}) == {"d", "e"}


# -- subject / patient / author / authenticator / custodian ---------------------------------


async def test_subject_is_multi_target(client, world):
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"c"}
    assert await _keys(client, world, subject=f"Practitioner/{world['pr']}") == {"d"}
    assert await _keys(client, world, **{"subject:Group": str(world["grp"])}) == {"c"}
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    # a Group or Practitioner subject counts as missing it
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b"}


async def test_author_is_multi_target_and_repeats(client, world):
    assert await _keys(client, world, author=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, author=f"Organization/{world['org1']}") == {"a"}
    assert await _keys(client, world, author=f"PractitionerRole/{world['role']}") == {
        "c"
    }
    assert await _keys(client, world, **{"author:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, **{"author:identifier": "urn:pr|P-LOGICAL"}) == {
        "d"
    }
    assert await _status(client, author=str(world["pr"])) == 400
    assert await _keys(client, world, **{"author:missing": "true"}) == {"e"}


async def test_authenticator_and_custodian(client, world):
    assert await _keys(client, world, authenticator=f"Practitioner/{world['pr']}") == {
        "a"
    }
    assert await _keys(client, world, **{"authenticator:missing": "true"}) == ALL - {
        "a"
    }
    # custodian has one target, so a bare id works
    assert await _keys(client, world, custodian=str(world["org1"])) == {"a"}
    assert await _keys(client, world, custodian=f"Organization/{world['org2']}") == {
        "c"
    }
    assert await _keys(
        client, world, **{"custodian:identifier": "urn:org|O-LOGICAL"}
    ) == {"d"}
    assert await _keys(client, world, **{"custodian:missing": "true"}) == {"b", "e"}


# -- encounter / related --------------------------------------------------------------------


async def test_encounter_has_two_targets_and_repeats(client, world):
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, encounter=f"EpisodeOfCare/{world['eoc']}") == {
        "b"
    }
    assert await _keys(
        client, world, **{"encounter:EpisodeOfCare": str(world["eoc"])}
    ) == {"b"}
    assert await _status(client, encounter=str(world["enc"])) == 400
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_related_is_reference_any(client, world):
    assert await _keys(client, world, related=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(client, world, **{"related:Condition": str(world["cond"])}) == {
        "a"
    }
    assert await _status(client, related=str(world["cond"])) == 400
    assert await _keys(client, world, **{"related:missing": "true"}) == ALL - {"a"}


# -- relatesTo: relatesto / relation / relationship -----------------------------------------


async def test_relatesto_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, relatesto=str(world["b"])) == {"a", "c"}
    assert await _keys(client, world, relatesto=f"DocumentReference/{world['a']}") == {
        "c"
    }
    assert await _keys(client, world, **{"relatesto:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_relation(client, world):
    assert await _keys(client, world, relation="replaces") == {"a"}
    assert await _keys(client, world, relation="transforms,appends") == {"c"}
    assert await _keys(client, world, relation=f"{RELATION_SYSTEM}|replaces") == {"a"}
    assert await _keys(client, world, relation="http://wrong|replaces") == set()
    assert await _keys(client, world, relation="|replaces") == set()
    assert await _keys(client, world, relation="signs") == set()
    assert await _keys(client, world, relation="deletes") == set()  # unknown code
    assert await _keys(client, world, **{"relation:missing": "true"}) == {"b", "d", "e"}


async def test_relationship_pairs_the_target_with_its_code(client, world):
    a, b = world["a"], world["b"]
    assert await _keys(client, world, relationship=f"{b}$replaces") == {"a"}
    assert await _keys(
        client, world, relationship=f"DocumentReference/{b}$appends"
    ) == {"c"}
    assert await _keys(client, world, relationship=f"{a}$transforms") == {"c"}
    # c names b (appends) and a (transforms), but not b with `transforms`, nor a with `appends`
    assert await _keys(client, world, relationship=f"{b}$transforms") == set()
    assert await _keys(client, world, relationship=f"{a}$appends") == set()
    # the two separate parameters would match across entries - the composite must not
    assert await _keys(client, world, relatesto=str(b), relation="transforms") == {"c"}
    assert await _keys(client, world, relationship=f"{b}$replaces,{b}$appends") == {
        "a",
        "c",
    }
    assert await _keys(client, world, relationship=f"{b}$bogus") == set()


async def test_relationship_is_a_composite_with_no_modifiers_and_bad_values_are_400(
    client, world
):
    assert await _status(client, relationship="nodollar") == 400
    assert await _status(client, relationship=f"{world['b']}$") == 400
    assert await _status(client, relationship=f"a$b$c") == 400
    assert await _status(client, **{"relationship:missing": "true"}) == 400
    assert await _status(client, _sort="relationship") == 400


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"c"}
    assert await _keys(client, world, **{"subject:Practitioner.family": "Careful"}) == {
        "d"
    }
    assert await _keys(client, world, **{"author:Practitioner.family": "Careful"}) == {
        "a"
    }
    assert await _keys(client, world, **{"author:Patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"author:Organization.name": "Providing"}) == {
        "a"
    }
    assert await _keys(client, world, **{"custodian.name": "Other"}) == {"c"}
    assert await _keys(
        client, world, **{"authenticator:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"encounter:Encounter.status": "in-progress"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"encounter:EpisodeOfCare.status": "active"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"related:Condition.patient": str(world["p1"])}
    ) == {"a"}
    # relatesto chains back into DocumentReference itself
    assert await _keys(client, world, **{"relatesto.status": "superseded"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"relatesto.description": "Discharge"}) == {"c"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"author.family": "x"}) == 400
    assert await _status(client, **{"type.x": "y"}) == 400  # a token cannot be chained
    assert await _status(client, **{"date.x": "y"}) == 400
    assert await _status(client, **{"location.x": "y"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "author",
        "authenticator",
        "category",
        "contenttype",
        "custodian",
        "date",
        "description",
        "encounter",
        "event",
        "facility",
        "format",
        "identifier",
        "language",
        "location",
        "patient",
        "period",
        "related",
        "relatesto",
        "relation",
        "security-label",
        "setting",
        "status",
        "subject",
        "type",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
        assert (await _search(client, _sort=f"-{key}"))["total"] == 5, key


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "current"
    assert "description" not in resource and "type" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="DocumentReference:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="DocumentReference:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    bundle = await _search(client, _id=ids, _include="DocumentReference:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="DocumentReference:author")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org1"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}
    bundle = await _search(client, _id=ids, _include="DocumentReference:authenticator")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    bundle = await _search(client, _id=ids, _include="DocumentReference:custodian")
    assert _of_type(bundle, "Organization", "include") == {
        str(world["org1"]),
        str(world["org2"]),
    }
    bundle = await _search(client, _id=ids, _include="DocumentReference:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["eoc"])}
    bundle = await _search(client, _id=ids, _include="DocumentReference:related")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}


async def test_include_relatesto(client, world):
    # c is not a target of anything; it names a and b, which are matches too - so match only c
    bundle = await _search(
        client, _id=str(world["c"]), _include="DocumentReference:relatesto"
    )
    assert _of_type(bundle, "DocumentReference", "include") == {
        str(world["a"]),
        str(world["b"]),
    }


async def test_revinclude_on_the_resources_a_document_points_at(client, world):
    for path, key, param, expected in (
        ("patients", "p1", "DocumentReference:patient", {"a"}),
        ("patients", "p1", "DocumentReference:subject", {"a"}),
        ("patients", "p2", "DocumentReference:author", {"b"}),
        ("practitioners", "pr", "DocumentReference:subject", {"d"}),
        ("practitioners", "pr", "DocumentReference:authenticator", {"a"}),
        ("practitioners", "pr", "DocumentReference:author", {"a"}),
        ("practitioner-roles", "role", "DocumentReference:author", {"c"}),
        ("organizations", "org1", "DocumentReference:custodian", {"a"}),
        ("organizations", "org2", "DocumentReference:custodian", {"c"}),
        ("organizations", "org1", "DocumentReference:author", {"a"}),
        ("groups", "grp", "DocumentReference:subject", {"c"}),
        ("encounters", "enc", "DocumentReference:encounter", {"a"}),
        ("episodes-of-care", "eoc", "DocumentReference:encounter", {"b"}),
    ):
        bundle = await _other(client, path, _id=str(world[key]), _revinclude=param)
        got = _of_type(bundle, "DocumentReference", "include")
        assert got == {str(world[k]) for k in expected}, (path, param)


async def test_revinclude_relatesto_on_documents_themselves(client, world):
    bundle = await _search(
        client, _id=str(world["b"]), _revinclude="DocumentReference:relatesto"
    )
    assert _of_type(bundle, "DocumentReference", "include") == {
        str(world["a"]),
        str(world["c"]),
    }


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="current", type="34133-9") == {"a"}
    assert await _keys(client, world, status="current", type="11488-4") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), contenttype="application/pdf"
    ) == {"a"}
    assert (
        await _keys(client, world, contenttype="application/pdf", language="fr")
        == set()
    )


async def test_content_entry_values_are_not_paired_across_params(client, world):
    # contenttype and language are separate parameters: each matches any content entry
    assert await _keys(client, world, contenttype="text/plain", language="fr") == {"b"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, date="notadate") == 400
    assert await _status(client, period="notadate") == 400
    assert await _status(client, **{"patient:Group": "1"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"description:below": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 has no `docstatus`, `name` or `account` search parameter on DocumentReference
    for name in ("docstatus", "name", "account"):
        assert (
            await client.get(
                BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
            )
        ).status_code == 400, name


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "superseded", "contenttype": "text/plain"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="DOC-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/document-references/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "DocumentReference"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle

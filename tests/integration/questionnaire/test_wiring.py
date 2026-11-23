"""Questionnaire <-> QuestionnaireResponse.

`QuestionnaireResponse.questionnaire` is a canonical URL (a string, not a Reference object), so it
is not existence-checked on write; but now that Questionnaire is a resource here it chains
(`questionnaire.name=`), is `_include`d (`_include=QuestionnaireResponse:questionnaire`) and has
the reverse `Questionnaire?_revinclude=QuestionnaireResponse:questionnaire`. The canonical is
resolved against the Questionnaire's own `url`: an unversioned canonical finds it, so does
`url|version`, and so does a relative `Questionnaire/<id>`.
"""

import pytest

from tests.integration.questionnaire.support import (
    BASE,
    URL,
    create_questionnaire,
    create_questionnaire_response,
    questionnaire_body,
    questionnaire_response_body,
)

RESPONSES = "/api/fhir/v1/questionnaire-responses"
GAD = "https://fhir-server.dev/fhir/Questionnaire/gad-7"


def _ids(bundle: dict, rtype: str, mode: str = "match") -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


@pytest.fixture
async def world(client) -> dict:
    phq = await create_questionnaire(
        client,
        questionnaire_body(url=URL, version="1.0", name="PHQ9", title="Patient Health"),
    )
    gad = await create_questionnaire(
        client, questionnaire_body(url=GAD, version="2.0", name="GAD7", title="Anxiety")
    )
    other = await create_questionnaire(client, questionnaire_body(name="Unrelated"))
    by_url = await create_questionnaire_response(
        client, questionnaire_response_body(questionnaire=URL)
    )
    by_version = await create_questionnaire_response(
        client, questionnaire_response_body(questionnaire=f"{GAD}|2.0")
    )
    by_id = await create_questionnaire_response(
        client, questionnaire_response_body(questionnaire=f"Questionnaire/{other}")
    )
    nothing = await create_questionnaire_response(client, questionnaire_response_body())
    unresolved = await create_questionnaire_response(
        client,
        questionnaire_response_body(questionnaire="https://elsewhere.example.org/Q/9"),
    )
    return {
        "phq": phq,
        "gad": gad,
        "other": other,
        "by_url": by_url,
        "by_version": by_version,
        "by_id": by_id,
        "nothing": nothing,
        "unresolved": unresolved,
    }


async def _responses(client, **params) -> set[int]:
    resp = await client.get(RESPONSES + "/", params=params)
    assert resp.status_code == 200, resp.text
    return {int(i) for i in _ids(resp.json(), "QuestionnaireResponse")}


async def test_chain_through_the_canonical_url(client, world):
    assert await _responses(client, **{"questionnaire.name": "PHQ"}) == {
        world["by_url"]
    }
    # a versioned canonical resolves to the Questionnaire with that url
    assert await _responses(client, **{"questionnaire.name": "GAD"}) == {
        world["by_version"]
    }
    assert await _responses(client, **{"questionnaire.title": "Anx"}) == {
        world["by_version"]
    }
    # a relative Questionnaire/<id> resolves by id
    assert await _responses(client, **{"questionnaire.name": "Unrelated"}) == {
        world["by_id"]
    }
    assert await _responses(client, **{"questionnaire.name": "nomatch"}) == set()
    assert await _responses(
        client, **{"questionnaire.status": "active", "questionnaire.name": "PHQ"}
    ) == {world["by_url"]}


async def test_chain_with_an_explicit_type(client, world):
    assert await _responses(client, **{"questionnaire:Questionnaire.name": "PHQ"}) == {
        world["by_url"]
    }


async def test_include_the_questionnaire(client, world):
    resp = await client.get(
        RESPONSES + "/",
        params={
            "_id": f"{world['by_url']},{world['by_version']},{world['by_id']},{world['nothing']}",
            "_include": "QuestionnaireResponse:questionnaire",
        },
    )
    assert resp.status_code == 200, resp.text
    bundle = resp.json()
    assert _ids(bundle, "Questionnaire", "include") == {
        str(world["phq"]),
        str(world["gad"]),
        str(world["other"]),
    }


async def test_unversioned_canonical_includes_every_stored_version(client, world):
    await create_questionnaire(
        client, questionnaire_body(url=URL, version="2.0", name="PHQ9-v2")
    )
    resp = await client.get(
        RESPONSES + "/",
        params={
            "_id": str(world["by_url"]),
            "_include": "QuestionnaireResponse:questionnaire",
        },
    )
    assert len(_ids(resp.json(), "Questionnaire", "include")) == 2


async def test_revinclude_the_responses(client, world):
    resp = await client.get(
        BASE + "/",
        params={
            "_id": f"{world['phq']},{world['gad']},{world['other']}",
            "_revinclude": "QuestionnaireResponse:questionnaire",
        },
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json(), "QuestionnaireResponse", "include") == {
        str(world["by_url"]),
        str(world["by_version"]),
        str(world["by_id"]),
    }
    only = await client.get(
        BASE + "/",
        params={
            "_id": str(world["gad"]),
            "_revinclude": "QuestionnaireResponse:questionnaire",
        },
    )
    assert _ids(only.json(), "QuestionnaireResponse", "include") == {
        str(world["by_version"])
    }


async def test_a_response_without_a_resolvable_canonical_is_still_stored(client, world):
    resp = await client.get(f"{RESPONSES}/{world['unresolved']}")
    assert resp.status_code == 200
    assert resp.json()["questionnaire"] == "https://elsewhere.example.org/Q/9"
    assert await _responses(
        client, questionnaire="https://elsewhere.example.org/Q/9"
    ) == {world["unresolved"]}

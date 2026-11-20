# Add Tests for a FHIR Resource (content-based / Medplum-style)

Checklist for the tests of a resource built per `/new-fhir-resource`. Reference implementations (newest and most complete first): `tests/integration/encounter/` and `tests/conformance/test_encounter_fhir.py` (quantity, Period, multi-target, bare Coding), `tests/integration/related_person/` (a compact one, plus cross-resource wiring), `tests/integration/appointment*/`, `tests/integration/patient/` (`/me`, `user` link), then `organization/` and `practitioner/`. The old normalized-resource test guide (plain + FHIR formats, `/me`, child routes) is preserved in `docs/legacy/add-resource-tests-normalized.md`.

Stack: **pytest-asyncio** (`asyncio_mode = "auto"`), **httpx AsyncClient** against the real app, **SQLite in-memory**. `tests/conftest.py` provides the `client` / `other_client` fixtures, `make_test_user`, and SQLite shims for Postgres-only things (arrays, JSONB, `near` math). The resource package adds only auth overrides, payloads and test modules.

Aim: every endpoint at least once, every search parameter and every modifier it declares, and the high-risk negative paths (cross-org, org-less token, missing scope, bad values). Comments should say *why* a test exists.

## ARGUMENTS: $RESOURCE

---

## Before starting — read these

- `app/repository/<resource>/search.py` — the registry: it is the list of what must be tested (every `SearchParam`, its `modifiers`, `sort`, includes).
- `app/repository/<resource>/_indexer.py` — what each stored shape turns into in the index.
- `app/routers/<resource>/core.py` — routes, `/me` if present.
- The R4 resource page's **Search Parameters** table (`https://www.hl7.org/fhir/R4/<resource>.html#search`) and `https://www.hl7.org/fhir/R4/search.html` for what each type must match (string = case/accent-insensitive **starts-with**, `:exact`, `:contains`; token forms; reference forms; date prefixes).
- `configs/config.yaml` — `routes.enabled` must list the resource or every request 404s; `fhir_validation.enabled` is a local switch (it can be `false`, which skips base R4 validation).

## Files

```
tests/integration/<resource>/__init__.py      (empty)
tests/integration/<resource>/conftest.py      autouse permission override
tests/integration/<resource>/support.py       BASE, MINIMAL, FULL, create_<resource>()
tests/integration/<resource>/test_core.py     create / read / patch / delete / auth (+ /me, immutability)
tests/integration/<resource>/test_search.py   one block per parameter, then result params
tests/conformance/test_<resource>_fhir.py     mapper output vs google-fhir-r4
tests/helpers/assertions.py                   assert_fhir_<resource>(data, **expected)   (optional: only if the tests call it)
tests/unit/test_<matcher>.py                  only when you add an engine matcher (e.g. test_quantity_match.py)
tests/integration/capability/test_metadata.py add the resource to the `expected` map
```

### `conftest.py`
Autouse fixture overriding `get_current_user` with `make_test_user(permissions=["<resource>:create", ":read", ":update", ":delete"])` (plus `<resource>:link` for resources with an end-user link) and restoring the default afterwards (copy Practitioner's).

### `support.py`
- `BASE = "/api/fhir/v1/<resources>"`.
- Payloads are **genuine FHIR R4 JSON** (camelCase, nested datatypes); responses are FHIR too. `MINIMAL`, and a `FULL` that exercises every element the registry indexes **plus** elements nothing searches on (they must round-trip).
- `create_<resource>(client, payload=None) -> int` asserting 201 and returning `int(resp.json()["id"])`.
- Avoid fixture values that make the Java validator sidecar do slow remote lookups: omit `system` on `urn:ietf:bcp:47` language codings and omit `Attachment.contentType`; use `https://fhir-server.dev/fhir/...` for identifier systems, never `http://example.org/...`.

### `test_core.py` must cover
- **Create:** minimal; full round trip (stored body == sent body minus `resourceType`/`id`/`meta`, and GET returns the same); elements nothing searches on survive; sent `id`/`meta` are ignored; audit `meta` extensions come from the actor; wrong `resourceType` → 422; a bad required-binding code → 422; **non-FHIR key and stale flat fields → 422 (needs the validator on — see below)**; a local reference that doesn't exist → 422, an absolute URL is stored unresolved.
- **Read:** by id; always `application/fhir+json` whatever `Accept` says (`None`, `application/json`, `*/*`); XML-only `Accept` / `_format=xml` → 406 OperationOutcome; not found → 404 OperationOutcome.
- **Patch:** scalar update; untouched elements survive; **search index is rebuilt** (old value no longer found, new value found); a supplied list replaces wholesale and `[]` clears (and the index follows); an invalid value → 422 and nothing written; not found → 404; resource business rules (e.g. Organization's circular `partOf`).
- **Delete:** 204, then 404, and its index rows are gone from search.
- **End-user link / `/me`** (resources with a `user_id`): create starts unlinked; `PUT/GET/DELETE /{id}/user` (link, show, unlink — idempotent, replace on re-link, one user per org → 422, same user allowed in different orgs, own `<resource>:link` permission → 403 without it, 404 cross-org, 422 on empty body); the link never appears in the resource or `content`; patch/delete of the record leave it alone; `/me` returns only records linked to the caller's `sub`, follows link/unlink, supports every search parameter, and isn't shadowed by `/{id}`.
- **Auth:** missing scope → 403; org-less token → 403 on create/search/read (override `get_current_user` with an `async def _no_org(request: Request)` — **annotate `request: Request`** or FastAPI treats it as a query parameter); cross-org GET/PATCH/DELETE → 404 (never 403); cross-tenant search isolation.

### The validator switch
`configs/config.yaml`'s `fhir_validation.enabled` is a switch that may be `false` locally, which skips base R4 validation entirely. A test that asserts "a non-FHIR key / bad datatype is rejected" must turn it on itself:

```python
@pytest.fixture
def native_validation(monkeypatch):
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")
```
Request it only in the tests that need it. (A test that passes only because validation is off, or fails only because it is off, is a bug in the test.)

### `test_search.py` must cover
Seed a small fixture (a `people`-style fixture of 4 records with **distinct** values) and write helpers `_search(client, params)`, `_ids(bundle)` (match entries only), `_found(client, people, **params)` returning the keys found.

- **One block per parameter**, using a value that can actually match (a test that searches a non-matching value and expects 0 results proves nothing): the default form, each modifier the registry lists, and the negatives (`:not` includes records with no value; `:missing=true/false`; wrong system → no match; unknown code → no match, not a 500).
- **String:** starts-with (not contains) — `address=Erewhon` must **not** match the line `534 Erewhon St`; case-insensitive; accent-insensitive (`muller` finds `Müller`); `:exact` is case- and accent-sensitive; `:contains`.
- **Token:** `code`, `system|code`, `|code`, `system|`; comma OR; `:not`; `:text`; `:of-type` (identifier); `:in`/`:below`/`:above` when the registry lists them (seed the terminology tables as Organization's `test_search.py` does).
- **Reference:** `id`, `Type/id`, absolute URL of this server, absolute URL elsewhere (raw match), `:[type]`, `:identifier`, chaining, `:above`/`:below` where declared.
- **Multi-target reference** (`Schedule.actor`): a bare id with no type is a 400; `Type/id` and `:Type=id` work for every type — including types that aren't resources on this server; the type is part of the match (`Patient/N` never matches `Location/N`; also test the reverse `_revinclude` with a clashing number); chaining needs a typed actor (`actor:Practitioner.family=`) and is a 400 for an untyped or unsearchable type; `_include=X:param` brings in every modeled target and `X:param:Type` just one.
- **Quantity** (`Encounter.length`): `5` matches at the precision written (`4.5`–`5.4` yes, `5.5` no), `gt/lt/ge/le/sa/eb/ne/ap`, `number|system|code`, `||code` also matching the unit text, a wrong system → no match, a malformed number → 400. The pure semantics live in `tests/unit/test_quantity_match.py`.
- **String matched against a line** (`address`): starts-with means `address=Main` does **not** find the line `1 Main St`; search `1 Main`.
- **Date:** each prefix and precision; `_lastUpdated`. For a **Period** parameter (e.g. PractitionerRole `date`) test the range semantics with periods that are closed, open-ended, open-started and absent: the default `eq` means the search range wholly contains the period (a year-long period never fits inside a month), `gt/lt/ge/le` overlap, `sa/eb` entirely after/before, `ne`, `ap`, `:missing`, and that a row with no period never matches. The pure semantics are pinned in `tests/unit/test_period_match.py`.
- **Combination:** comma = OR; repeated parameter = AND; different parameters AND; `\,` is a literal comma.
- **Result parameters:** `_sort` (asc/desc, multi-value rule, an unsupported sort → 400), `_count` (capped at `pagination.max_limit`; `0` = count only, no `entry`), `_offset`, `_total=none`, links (`self/first/next/previous/last`), `_summary`, `_elements` (SUBSETTED tag), `_include`/`_revinclude` + `:iterate` for every declared target.
- **Handling:** unknown parameter → ignored with an `outcome` entry; **400** under `Prefer: handling=strict`; known parameter with a bad modifier or malformed value → 400; unimplemented common parameters (`_tag`, `_has`, ...) → ignored (200); `_query` → 400; a parameter with an empty value is ignored (R4).
- **Bundle:** `resourceType`, `type=searchset`, `total`, `entry[].fullUrl` ends with `/<resources>/<id>`, `search.mode`; XML-only `Accept` → 406 on search too.
- **POST `/_search`:** form-encoded body; query-string and body are combined.

### `tests/conformance/test_<resource>_fhir.py`
The mapper just stamps `id`/`meta` onto `content`, so the oracle (`google-fhir-r4`, dev-only) checks that **what we store and return is valid R4**. Build `<Resource>Model(...)` rows with `content=` documents (one parametrized case per stored shape: minimal, each optional element, every BackboneElement fully populated, the full payload, `updated_by`/`updated_at`), call `to_fhir_<resource>`, and `assert_valid(<resource>_pb2.<Resource>, ...)`. Include `test_mapper_serves_content_unchanged` and a `test_validator_rejects_invalid_fhir` of deliberately broken payloads (wrong types, misspelled element, bad required-binding code, missing required child) so a library bump that stops validating can't pass silently. Only include a guard case the oracle really rejects — it does **not** reject a single-element array for a 0..1 element or an unknown code for a required binding (drop those cases and say so in a comment; the integration tests cover them). Feed JSON **text**, not floats (`assert_valid` in `tests/conformance/support.py` does this).

### `tests/helpers/assertions.py`
Optional. If the integration tests use `assert_fhir_<resource>(data, **expected)`, it asserts `resourceType`, `id` present, and each expected field (there is no plain-format assertion). Newer suites (Encounter, AppointmentResponse, RelatedPerson) assert on the response body directly; don't add a helper nothing calls.

### Rebuilding a resource other resources already reference
When the new resource becomes an existence-checked reference target in resources that were built earlier (RelatedPerson → Patient `link`, Appointment/AppointmentResponse actors, Encounter participants):
- Those resources' `conftest.py` permission lists gain `<new>:create` and `<new>:read`.
- Tests that used a made-up id for that type must create a real row (through the new resource's router, or `tests/helpers/seed.py`) — and gain a "missing target → 422" test plus a "present target → 201" test.
- Add chaining (`actor:RelatedPerson.name=`), `_include` and `_revinclude` tests on **both** sides, and assert a clashing id of another type does not match.
- Re-run every one of those resources' folders; this is where regressions appear.

### Regression tests worth copying
- **`:missing` on a narrowed multi-target parameter** (`patient:missing=true`) with a record that holds only a logical-identifier reference — it must be reported as having the value (see Encounter / AppointmentResponse).
- **A stale field from the old API** is a 422; build the body as `{**body(), **stale}` so a helper can't swallow the key.
- **A partial date** (`1990`, `1990-05`) round-trips and is matched by range, not by equality.
- **A text-only CodeableConcept** is findable by `:text` and has a code-less index row.

### `tests/integration/capability/test_metadata.py`
Add `"<resource>": ("<Resource>", <resource>_search())` to the `expected` map: the statement must list exactly the registry's parameters.

## Run

```bash
uv run pytest tests/integration/<resource> tests/conformance/test_<resource>_fhir.py tests/integration/capability -q
```
Integration suites are slow (each test builds a fresh engine and seeds the profile tables; a resource's `test_search.py` can take ~3 minutes, the wide regression about an hour): run a resource's folder while iterating, use `run_in_background` for anything over two minutes and wait for the completion notification. `pytest tests` as a whole fails at collection (pre-existing) — always pass directories. Before committing, run the sibling content-based resources too — a change to `app/fhir/search/` or `app/repository/_content_index.py` affects all of them. Pre-existing failures that exist only because `fhir_validation.enabled` is `false` (Organization's "non-FHIR key" tests) are not caused by your change; don't "fix" them by touching the engine.

## Key invariants

- Every test creates its own data; never depend on another test's rows.
- Assert on the **index** through search (`_found`) after create **and** after patch/delete — the index is where the bugs hide, not the stored document.
- Cross-org access is **404, never 403**; an org-less token is 403.
- Use values that can match; assert both the positive and the negative.
- No sleeps, no real network; the Java validator sidecar and `tx.fhir.org` are not available in tests.

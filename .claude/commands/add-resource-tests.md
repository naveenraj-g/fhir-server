# Add Tests for a FHIR Resource (content-based / Medplum-style)

Checklist for the tests of a resource built per `/new-fhir-resource`. Reference implementations: `tests/integration/organization/`, `tests/integration/practitioner/`, `tests/conformance/test_practitioner_fhir.py`. The old normalized-resource test guide (plain + FHIR formats, `/me`, child routes) is preserved in `docs/legacy/add-resource-tests-normalized.md`.

Stack: **pytest-asyncio** (`asyncio_mode = "auto"`), **httpx AsyncClient** against the real app, **SQLite in-memory**. `tests/conftest.py` provides the `client` / `other_client` fixtures, `make_test_user`, and SQLite shims for Postgres-only things (arrays, JSONB, `near` math). The resource package adds only auth overrides, payloads and test modules.

Aim: every endpoint at least once, every search parameter and every modifier it declares, and the high-risk negative paths (cross-org, org-less token, missing scope, bad values). Comments should say *why* a test exists.

## ARGUMENTS: $RESOURCE

---

## Before starting — read these

- `app/repository/<resource>/search.py` — the registry: it is the list of what must be tested (every `SearchParam`, its `modifiers`, `sort`, includes).
- `app/repository/<resource>/_indexer.py` — what each stored shape turns into in the index.
- `app/routers/<resource>/core.py` — routes, `/me` if present.
- The R4 resource page's **Search Parameters** table (`https://www.hl7.org/fhir/R4/<resource>.html#search`) and `https://www.hl7.org/fhir/R4/search.html` for what each type must match (string = case/accent-insensitive **starts-with**, `:exact`, `:contains`; token forms; reference forms; date prefixes).
- `configs/config.yaml` — `routes.enabled` must list the resource or every request 404s; `fhir_validation.enabled` ships `false`.

## Files

```
tests/integration/<resource>/__init__.py      (empty)
tests/integration/<resource>/conftest.py      autouse permission override
tests/integration/<resource>/support.py       BASE, MINIMAL, FULL, create_<resource>()
tests/integration/<resource>/test_core.py     create / read / patch / delete / auth (+ /me, immutability)
tests/integration/<resource>/test_search.py   one block per parameter, then result params
tests/conformance/test_<resource>_fhir.py     mapper output vs google-fhir-r4
tests/helpers/assertions.py                   assert_fhir_<resource>(data, **expected)
tests/integration/capability/test_metadata.py add the resource to the `expected` map
```

### `conftest.py`
Autouse fixture overriding `get_current_user` with `make_test_user(permissions=["<resource>:create", ":read", ":update", ":delete"])` and restoring the default afterwards (copy Practitioner's).

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
- **Record-state extension / `/me`** (end-user scoped resources): `/me` returns only the caller's own records and supports every search parameter; the route isn't shadowed by `/{id}`; the extension can't be changed, dropped, or added after create (422); an unrelated patch leaves it intact.
- **Auth:** missing scope → 403; org-less token → 403 on create/search/read (override `get_current_user` with an `async def _no_org(request: Request)` — **annotate `request: Request`** or FastAPI treats it as a query parameter); cross-org GET/PATCH/DELETE → 404 (never 403); cross-tenant search isolation.

### The validator switch
`configs/config.yaml` ships `fhir_validation.enabled: false`, which skips base R4 validation. A test that asserts "a non-FHIR key / bad datatype is rejected" must turn it on itself:

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
- **Date:** each prefix and precision; `_lastUpdated`.
- **Combination:** comma = OR; repeated parameter = AND; different parameters AND; `\,` is a literal comma.
- **Result parameters:** `_sort` (asc/desc, multi-value rule, an unsupported sort → 400), `_count` (capped at `pagination.max_limit`; `0` = count only, no `entry`), `_offset`, `_total=none`, links (`self/first/next/previous/last`), `_summary`, `_elements` (SUBSETTED tag), `_include`/`_revinclude` + `:iterate` for every declared target.
- **Handling:** unknown parameter → ignored with an `outcome` entry; **400** under `Prefer: handling=strict`; known parameter with a bad modifier or malformed value → 400; unimplemented common parameters (`_tag`, `_has`, ...) → ignored (200); `_query` → 400; a parameter with an empty value is ignored (R4).
- **Bundle:** `resourceType`, `type=searchset`, `total`, `entry[].fullUrl` ends with `/<resources>/<id>`, `search.mode`; XML-only `Accept` → 406 on search too.
- **POST `/_search`:** form-encoded body; query-string and body are combined.

### `tests/conformance/test_<resource>_fhir.py`
The mapper just stamps `id`/`meta` onto `content`, so the oracle (`google-fhir-r4`, dev-only) checks that **what we store and return is valid R4**. Build `<Resource>Model(...)` rows with `content=` documents (one parametrized case per stored shape: minimal, each optional element, every BackboneElement fully populated, the full payload, `updated_by`/`updated_at`), call `to_fhir_<resource>`, and `assert_valid(<resource>_pb2.<Resource>, ...)`. Include `test_mapper_serves_content_unchanged` and a `test_validator_rejects_invalid_fhir` of deliberately broken payloads (wrong types, misspelled element, bad required-binding code, missing required child) so a library bump that stops validating can't pass silently. Feed JSON **text**, not floats (`assert_valid` in `tests/conformance/support.py` does this).

### `tests/helpers/assertions.py`
`assert_fhir_<resource>(data, **expected)`: asserts `resourceType`, `id` present, and each expected field. There is no plain-format assertion.

### `tests/integration/capability/test_metadata.py`
Add `"<resource>": ("<Resource>", <resource>_search())` to the `expected` map: the statement must list exactly the registry's parameters.

## Run

```bash
uv run pytest tests/integration/<resource> tests/conformance/test_<resource>_fhir.py tests/integration/capability -q
```
Integration suites are slow (each test builds a fresh engine and seeds the profile tables): run a resource's folder, not the whole tree, while iterating. Before committing, run the sibling content-based resources too — a change to `app/fhir/search/` or `app/repository/_content_index.py` affects all of them. Pre-existing failures that exist only because `fhir_validation.enabled` is `false` (Organization's "non-FHIR key" tests) are not caused by your change; don't "fix" them by touching the engine.

## Key invariants

- Every test creates its own data; never depend on another test's rows.
- Assert on the **index** through search (`_found`) after create **and** after patch/delete — the index is where the bugs hide, not the stored document.
- Cross-org access is **404, never 403**; an org-less token is 403.
- Use values that can match; assert both the positive and the negative.
- No sleeps, no real network; the Java validator sidecar and `tx.fhir.org` are not available in tests.

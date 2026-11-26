# Edit a Rebuilt FHIR Resource

Checklist for changing a resource that is **already rebuilt** per `/new-fhir-resource` (its whole document is in `content`, only search-parameter values are indexed): a new or changed search parameter, a new reference to another resource, a changed storage type, a new `_include`/`_revinclude`, or a fix to the engine it runs on. Building a resource from scratch, or rebuilding an old normalized one, is `/new-fhir-resource`; the modelling rules are `/fhir-db-model`; the tests are `/add-resource-tests`.

**Always work from the HL7 R4 documentation, never memory, never R5**: the resource page (`https://www.hl7.org/fhir/R4/<resource>.html#search`), `search.html`, `searchparameter-registry.html`.

## 1. What kind of change is it?

| Change | What it takes |
|---|---|
| An element **no** search parameter reads (a new field in `content`) | **Nothing.** It is stored and returned already. The request/response models are generated from HL7's definition and already include it - re-run `scripts/generate_fhir_resources.py` only if the generator itself changed. |
| A new **searchable** element | Index column or child table in `app/models/<resource>/`, filled in `app/repository/<resource>/_indexer.py`, a `SearchParam` in `search.py`, a **migration that backfills it from `content`**, tests. Decide the storage with `/fhir-db-model` (token → shared token table with `param`; Period → half-open `*_start/_end`; reference → columns or the shared reference table; required-binding `code` → enum, audit it). |
| A new `SearchParam` on an existing resource | Also re-run `uv run python scripts/generate_fhir_resources.py`: each element's "Search parameters" hint in `app/schemas/fhir_resources/<resource>.py` is read from the registry. |
| A parameter's semantics change (matching, targets, a different element) | Edit the `SearchParam`; if the stored shape changes, a migration that re-derives it from `content`. |
| The resource now **references another resource** (or a new type is allowed in an element) | See section 3: it is mostly automatic. |
| **Another resource now references this one** | Declare the `_revinclude` on this resource's registry (shared helpers `app/repository/_<x>_revinclude.py`) and add its tests; existence checks, chaining and `_include` need nothing (section 3). |
| A route / sequence block / parameter count | Update `docs/resource-status.md` and the CLAUDE.md paragraph. |
| Shared engine code (`app/fhir/search/`, `_content_index.py`, `_reference_shared.py`, `app/core/`, `tests/conftest.py`) | Everything depends on it. If it only *adds* something no resource calls yet, the resource-level run is enough; if it changes existing behavior, run every resource suite (the owner decides when the full regression runs). |

## 2. Changing the search index

1. `app/models/<resource>/` - column or index table (no audit columns on index rows, no FK to the target of a reference, `BigInteger` ids, reference type is a plain string).
2. `app/repository/<resource>/_indexer.py` - the only place that maps a document to the index; use the builders in `app/repository/_content_index.py`.
3. `app/repository/<resource>/search.py` - the `SearchParam` (and `summary_elements`, `includes`, `revincludes` if affected). Every condition reads **only index columns**.
4. **Migration** (`migrations/versions/`): one-way (the downgrade is not implemented), derives the new index data **from `content`**, never from the old tables when `content` already holds it. Give a new child table no constraint R4 does not require.
5. **Verify the migration on a scratch database only** - never the dev database. Create a scratch DB on the same server, point `FHIR_DATABASE_URL` at it for that command only (do not print `.env` or the password), `uv run alembic upgrade head`, check the new rows against `content`, then **drop the scratch DB**. For a data-bearing change, seed a few documents first and confirm the backfill.
6. `uv run python scripts/audit_hl7_live.py` exits 0, and `tests/unit/test_hl7_alignment.py` passes (a new required-binding `code` parameter goes in `REQUIRED_CODE_STORAGE`).

## 3. References between resources are derived, not listed

Read the "Cross-resource targets" notes in `/new-fhir-resource` Step E. In short:

- **Existence check** on write is shared and automatic for every relative `Type/<id>` to a rebuilt resource (`app/repository/_reference_check.py`, driven by `RESOURCE_REGISTRY`). A new row in `tests/integration/reference_check/cases.py` is only needed for a new *resource*.
- **Chaining and `_include`** follow `[t for t in targets if t in _MODELED]`, where `_MODELED = MODELED` is derived (`app/repository/_search_targets.py`). Do not add a type to a dict. If a type is not followed, either it is not in the element's `targets` (the spec's list, a constant in `app/models/<resource>/`) or the element builds its include list from a hand-written tuple - fix that tuple.
- **A Reference(Any) element** takes `targets=ANY_RESOURCE_TYPES` (alias it in the model package; `is_any()` checks identity, never copy the tuple). If you add one, add it to the expected set in `tests/unit/test_search_targets.py`.
- **The "is this type allowed here" check** for a known reference is `modifier in param.targets` (`parser.py`) and `reference_target` (`sql.py`). Never loosen it for a known reference.
- **`_revinclude`** is the one piece still declared by hand, on the referenced side.

## 4. Tests - run what the change can affect

`uv run python scripts/affected_tests.py` reads `git diff` and prints the pytest command. Rules of thumb (CLAUDE.md, "Which tests to run"):

- the resource's own folder `tests/integration/<resource>/`, `tests/conformance/test_<resource>_fhir.py`, `tests/integration/capability`, `tests/unit`;
- plus every resource whose files you edited;
- run **one folder at a time, in the background** (low memory; one `test_search.py` takes about 3 minutes); never `pytest tests` as a whole (collection fails, pre-existing); the full regression is the owner's call.

A test that used a made-up id for a now-rebuilt type gets a 422: create or seed a real row (`tests/helpers/<type>s.py`) and add the new resource's `create`/`read` scopes to that suite's `conftest.py`.

## 5. Documentation, in the same commit

- `docs/resource-status.md`: edit the affected rows and the existence-check table, close or add items in section 3, add a row to section 4 for a new engine capability, bump "Last updated", check the parameter count (command at the bottom of that file).
- `CLAUDE.md`: the resource's paragraph (parameters, storage, chaining, includes, what is checked on write, what is stored as sent).
- `docs/search-architecture/pending-search-capabilities.md` when the parameter set changes.
- Record any gap you find and leave open in the tracker; never leave it only in a code comment.
- Update these skills when the *process* changes.

## 6. Commit

- Stage only the files of the change; format only those paths (`uv run ruff format <paths>`), never the whole tree.
- Commit message: what changed and why, **no co-author line**, and never the words "Medplum-style" (or Medplum).
- Do not rewrite history unless asked. The commit hash goes into the tracker in a **follow-up commit** (replace `_pending_`).
- Push to `origin main` only when asked.

## 7. The GraphQL half

A change that alters an input or response shape, a search parameter, an include or a route also needs fhir-gql's `uv run python scripts/sync_schemas.py` (`/new-fhir-resource` Phase G), its tests, and `scripts/live_check.py --only <resource>` on both connectors.

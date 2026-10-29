# Roll Out Direct JWT/RBAC Auth to a Resource

**As of this writing, every currently-built FHIR resource in this codebase already validates JWTs directly and enforces RBAC** — there is no resource left on the old plain/gateway-trusted pattern (see CLAUDE.md's "Multi-Tenancy & Ownership", specifically its "History" subsection for how that got here: Patient/Practitioner/Organization first, then eight more, then Questionnaire converted after being built the other way, then QuestionnaireResponse/ServiceRequest/MedicationRequest/Observation/DiagnosticReport in one final pass). `/new-fhir-resource` now builds a brand-new resource auth-rolled-out from the start — **this skill is for the narrower case of converting an already-built plain-pattern resource after the fact**, which only comes up if a resource was deliberately built on the old pattern (or one shows up some other way) and now needs converting. Don't run this against a resource that's already auth-rolled-out — check `app/routers/<resource>/core.py` for `require_permission(...)` first.

## ARGUMENTS: $RESOURCE

Steps use `$RESOURCE` = the resource name and `$resource` = its snake_case form. This assumes `app/auth/` already exists (JWKS verification, `require_permission`, `AuthUser`/`actor.sub`/`actor.org_id`) — it does, shared across every existing rollout. You are not building the auth *infrastructure*, only converting one resource that was built without it.

---

## What changes vs. the plain (gateway-trusted) pattern

| | Plain pattern (none currently in use) | JWT/RBAC pattern (every current resource) |
|---|---|---|
| `org_id` | Plain input field, gateway-forwarded | Derived from verified JWT's `activeOrganizationId` claim — **not** a request field |
| `created_by`/`updated_by` | Plain input fields, gateway-forwarded | Derived from verified JWT's `sub` claim — **not** request fields |
| `user_id` | Plain input field | **Unchanged** — still a plain gateway-forwarded field where this resource has one at all (see Standard Columns for which resources dropped it entirely) |
| Existence check | `resolve_<resource>()` dep — 404 if missing, no ownership check | No `resolve_<resource>()` dep at all — routes call service methods directly |
| Cross-org access | Not enforced at this layer (gateway's problem) | 404 (never 403 — avoids leaking existence) on any `patch`/`delete`/sub-resource op where the caller's `org_id` doesn't match the stored row |
| Missing org claim | N/A | 403 — **no org-less/super-admin bypass**; every operation requires an org-scoped actor |
| Route gate | None | `Depends(require_permission("<resource>", "create"|"read"|"update"|"delete"))` on every route |

---

## Step 1 — Strip `org_id`/`created_by`/`updated_by` from schemas

In `<Resource>CreateSchema`/`<Resource>PatchSchema` (and every one of its sub-resource Create/Patch schemas, if any accept these): remove the fields entirely. With `extra="forbid"` already in place, a caller who still sends them gets a clean 422 rather than the value being silently accepted and ignored.

`user_id` is **not** touched — it keeps behaving exactly as it does for every other resource that has one.

## Step 2 — Add org-scoped repository/service methods

Add a shared "get-scoped" helper on the service's core mixin (mirror any existing resource's `get_<resource>_scoped()` — e.g. `app/services/observation/core.py`):

```python
async def get_<resource>_scoped(self, resource_id: int, org_id: str | None) -> <Resource>Model:
    if not org_id:
        raise PermissionDeniedError("<Resource> operation requires an org-scoped token")
    model = await self.repository.get_by_<resource>_id_in_org(resource_id, org_id)
    if not model:
        raise NotFoundError("<Resource> not found")
    return model
```

Add the matching repository methods:
- `get_by_<resource>_id_in_org(resource_id, org_id) -> <Resource>Model | None` — full lookup (with sub-resources) scoped to `org_id`
- `<resource>_belongs_to_org(resource_id, org_id) -> bool`

Every `patch`/`patch_full`/`delete`/sub-resource method routes through one of these first — never raise 403 for a cross-org mismatch, always 404, so the caller can't distinguish "doesn't exist" from "exists in another org." Also rename the `list()`/`get_me()`/`_apply_list_filters()` parameter from `tenant_id` to `org_id` throughout the repository (purely a naming consistency choice matching every other rolled-out resource — the underlying column is still `tenant_id`).

`create`/`create_full` don't need the scoped-lookup helper (nothing to scope against yet) but **must** reject a request whose `actor.org_id` is `None` — no org-less bypass, ever. `create_full`/`patch_full` in the repository take `org_id`/`created_by`/`updated_by` as **explicit parameters** now (not read off `payload.tenant_id`/`payload.created_by`/`payload.updated_by`, which no longer exist on the schema) — this means a mechanical find-and-replace of `payload.tenant_id` → `org_id` and `payload.created_by` → `created_by` throughout `create_full`'s body, and adding `updated_by` as an explicit `patch_full` parameter. **Don't forget to explicitly set `model.updated_by = updated_by` on the main row inside `patch_full`** — the generic `setattr(model, field, value)` loop that applies every other PATCH field only sees fields still present in `data` (from `payload.model_dump(exclude_unset=True)`), and `updated_by` isn't a schema field anymore, so that loop silently stops updating it unless you add the explicit line. (This exact bug was found live in Questionnaire's own `patch_full()` — it had been converted without this line and nothing ever caught it, since nothing asserts on the main row's own `updated_by` after a PATCH in the test suite.)

## Step 3 — Wire `actor.sub`/`actor.org_id` through the router

Every route handler takes `actor: AuthUser = Depends(require_permission("<resource>", "<action>"))` (not a bare `Depends(get_current_user)` — `require_permission` already calls through to the verified `request.state.user` and returns a typed `AuthUser`) instead of a `resolve_<resource>` dependency. Read `org_id` from `actor.org_id`, `created_by`/`updated_by` from `actor.sub`.

`/me` scopes to `actor.sub` + `actor.org_id` — same shape as every other resource's `/me`, just actor-derived instead of query-param-derived. Drop any `tenant_id`/`user_id` *filter* query params from `GET /` and `GET /me` — org scoping is no longer client-suppliable, and user_id scoping (where this resource has `user_id` at all) only happens via `/me`'s own `actor.sub`, never a generic list filter.

Delete `app/deps/<resource>_deps.py` entirely — there's no `resolve_<resource>()` dependency left to keep.

## Step 4 — Update the fhir-gql half too

This resource's connector translators and GraphQL resolvers currently pass `tenant_id`/`user_id`/`created_by` into `to_wire_create()` and `updated_by` into `to_wire_patch()` as extra keyword-only arguments (the "default/gateway-trusted" shape). Once fhir-server's schema no longer accepts those as body fields, drop them:
- Both connectors' `to_wire_create(self, data: dict)` / `to_wire_patch(self, data: dict)` lose the extra keyword-only arguments — fhir-server (internal connector) now derives everything from the forwarded JWT itself (`InternalConnector` already always forwards `actor.token` as the `Authorization` header on every call, `inject_audit=False` or not); Medplum's translator never needed them in the first place, so this is a pure signature simplification there.
- Also drop `tenant_id`/`user_id` from `list_params()` on both translators, and from the GraphQL query's own `tenant_id`/`user_id` arguments — org scoping is derived from the caller's JWT now, not a client-suppliable filter.
- `app.gql.<resource>.mutations`'s `create_fhir_<resource>`/`update_fhir_<resource>` call sites simplify to `translator.to_wire_create(data)` / `translator.to_wire_patch(data)` (no more `tenant_id=actor.org_id, user_id=actor.sub, created_by=actor.sub` / `updated_by=actor.sub` kwargs) — keep `inject_audit=False` on the `connector.post`/`.patch` calls themselves, since the body still shouldn't carry `created_by`/`updated_by`.

## Step 5 — Verify end-to-end with a real JWT

`app.dependency_overrides[get_current_user] = ...` does work for `get_current_user` itself (it's wired as a plain router-level `Depends()`, and tests/conftest.py's own fixtures rely on exactly this) — but it's still worth verifying with **real signed JWTs**, not just the test suite's override, because this resource's own test suite (if it has one) may not exist yet and won't catch a wiring mistake in `require_permission`'s own call chain. Stand up a minimal real JWKS server:

1. Generate an RSA keypair (`cryptography` — already a project dependency) and **persist it to a file** — if you regenerate the keypair in a fresh Python process (e.g. a separate script that mints tokens) without reusing the exact same key the JWKS server is serving, every token's signature verification fails with a confusing generic error. Load-if-exists / generate-and-save-once avoids this.
2. Serve the public key as a real JWKS document (`{"keys": [{"kty": "RSA", "kid": ..., "n": ..., "e": ..., ...}]}`) on a local port.
3. Point `IAM_JWKS_URL`/`IAM_ISSUER` at it via real env vars when starting fhir-server (`IAM_JWKS_URL=http://localhost:<port>/jwks IAM_ISSUER=http://localhost:<port> uv run uvicorn app.main:app ...`) — don't edit `.env` for this, just set the env vars for that one process.
4. Sign tokens directly with the private key (`pyjwt`, RS256, `kid` header matching the JWKS entry) — no need for a live `/mint` HTTP endpoint, minting in-process in your own test script is simpler.
5. **Restart fhir-server itself if you ever regenerate the keypair** — `PyJWKClient` is a module-level singleton that caches the fetched key by `kid`; if you reuse the same `kid` with a new key, a long-running fhir-server process keeps verifying against the stale cached key and every token fails with a generic `401 Invalid token` that looks like a signing bug but isn't.
6. Hit the real endpoints with `httpx` and genuinely signed tokens — covering: org-less create (403, not 401 — the token itself is valid, just missing the org claim), happy-path create (201)/get/patch/delete (200/204), cross-org get/patch/delete (404, not 403 or a stale client-side check), and org-less list (403).

## Step 6 — Update CLAUDE.md

If this resource is being converted and that now means **every** currently-built resource is on the JWT/RBAC pattern, update CLAUDE.md's "Multi-Tenancy & Ownership" section to say exactly that (a single current-state statement, not a growing named list) — see that section's own "History" subsection for why it's written this way now. If it's *not* every resource yet (some other plain-pattern resource still exists), name the ones still remaining instead of claiming the rollout is complete.

---

## Checklist

- [ ] `org_id`/`created_by`/`updated_by` removed from Create/Patch schemas (all levels, including sub-resources) — `user_id` untouched
- [ ] `get_<resource>_scoped()`, `get_by_<resource>_id_in_org()`, and `<resource>_belongs_to_org()` added
- [ ] `create_full`/`patch_full` take `org_id`/`created_by`/`updated_by` as explicit parameters, not read off the payload
- [ ] Main row's `updated_by` is explicitly set inside `patch_full` (not left to the generic setattr loop)
- [ ] `create`/`create_full` reject a missing `actor.org_id` (403, no bypass)
- [ ] `patch`/`patch_full`/`delete`/every sub-resource method raises `NotFoundError` (404) on cross-org, never 403
- [ ] No `resolve_<resource>()` dependency remains for this resource — `app/deps/<resource>_deps.py` deleted, routes call `require_permission(...)` + service methods directly
- [ ] Every route gated with `require_permission("<resource>", "<action>")`
- [ ] `/me` scopes to `actor.sub` + `actor.org_id`, declared before `/{id}`; `tenant_id`/`user_id` filter params dropped from `GET /`/`GET /me`
- [ ] fhir-gql: both connectors' `to_wire_create`/`to_wire_patch` lose their extra keyword-only arguments; `list_params()` and the GraphQL query args lose `tenant_id`/`user_id`; mutation call sites simplified
- [ ] End-to-end verified with real signed JWTs (not just `dependency_overrides`) — happy path, cross-org 404, org-less 403
- [ ] CLAUDE.md's Multi-Tenancy & Ownership section updated to reflect the new current state

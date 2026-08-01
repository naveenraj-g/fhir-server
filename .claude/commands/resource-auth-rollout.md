# Roll Out Direct JWT/RBAC Auth to a Resource

This server has no authentication of its own for ~32 of 35 resources — a GraphQL gateway (`fhir-gql`) validates JWTs and forwards `user_id`/`org_id`/`created_by`/`updated_by` as plain request fields. **Patient, Practitioner, and Organization are the exception**: they validate JWTs directly via `app/auth/` and derive `org_id`/`created_by`/`updated_by` from the verified token instead of trusting the request body.

**Only do this for a resource if explicitly asked.** It is a deliberate, rare deviation from the default pattern (see CLAUDE.md's "Multi-Tenancy & Ownership"), not something to apply automatically when adding a new resource — most new resources should use the plain `resolve_<resource>()` dep from `/new-fhir-resource` instead.

## ARGUMENTS: $RESOURCE

Steps use `$RESOURCE` = the resource name and `$resource` = its snake_case form. This assumes `app/auth/` already exists (JWKS verification, `require_permission`, `AuthUser`/`actor.sub`/`actor.org_id`) — it does, shared across all three existing rollouts. You are not building the auth *infrastructure*, only wiring an additional resource into it.

---

## What changes vs. the plain (gateway-trusted) pattern

| | Plain pattern (~32 resources) | JWT/RBAC pattern (Patient/Practitioner/Organization) |
|---|---|---|
| `org_id` | Plain input field, gateway-forwarded | Derived from verified JWT's `activeOrganizationId` claim — **not** a request field |
| `created_by`/`updated_by` | Plain input fields, gateway-forwarded | Derived from verified JWT's `sub` claim — **not** request fields |
| `user_id` | Plain input field | **Unchanged** — still a plain gateway-forwarded field even under this pattern |
| Existence check | `resolve_<resource>()` dep — 404 if missing, no ownership check | No `resolve_<resource>()` dep at all — routes call service methods directly |
| Cross-org access | Not enforced at this layer (gateway's problem) | 404 (never 403 — avoids leaking existence) on any `patch`/`delete`/sub-resource op where the caller's `org_id` doesn't match the stored row |
| Missing org claim | N/A | 403 — **no org-less/super-admin bypass**; every operation requires an org-scoped actor |
| Route gate | None | `Depends(require_permission("<resource>", "create"|"read"|"update"|"delete"))` on every route |

---

## Step 1 — Strip `org_id`/`created_by`/`updated_by` from schemas

In `<Resource>CreateSchema`/`<Resource>PatchSchema` (and every one of its sub-resource Create/Patch schemas, if any accept these): remove the fields entirely. With `extra="forbid"` already in place, a caller who still sends them gets a clean 422 rather than the value being silently accepted and ignored.

`user_id` is **not** touched — it keeps behaving exactly as it does for every other resource.

## Step 2 — Add org-scoped repository/service methods

Add a shared "get-scoped" helper on the service's core mixin (mirror `get_patient_scoped()`/`get_practitioner_scoped()`/`get_organization_scoped()`):

```python
async def get_<resource>_scoped(self, resource_id: int, org_id: str) -> <Resource>Model:
    model = await self.repository.get_by_<resource>_id(resource_id)
    if model is None or not await self.repository.<resource>_belongs_to_org(resource_id, org_id):
        raise NotFoundError(f"<Resource> {resource_id} not found")
    return model
```

Add the matching `<resource>_belongs_to_org(resource_id, org_id) -> bool` repository check. Every `patch`/`patch_full`/`delete`/sub-resource method routes through `get_<resource>_scoped()` first — never raise 403 for a cross-org mismatch, always 404, so the caller can't distinguish "doesn't exist" from "exists in another org."

`create`/`create_full` don't need this helper (nothing to scope against yet) but **must** reject a request whose `actor.org_id` is `None` — no org-less bypass, ever.

## Step 3 — Wire `actor.sub`/`actor.org_id` through the router

Every route handler takes `actor: AuthUser = Depends(get_current_user)` (or however the existing three resources name it — check `app/routers/patient/core.py` for the exact signature) instead of a `resolve_<resource>` dependency. Read `org_id` from `actor.org_id`, `created_by`/`updated_by` from `actor.sub`. Gate every route with `Depends(require_permission("<resource>", "<action>"))`.

`/me` scopes to `actor.sub` + `actor.org_id` — same shape as every other resource's `/me`, just actor-derived instead of query-param-derived.

## Step 4 — Verify end-to-end with a real JWT

Because `app.dependency_overrides` doesn't reliably intercept a JWKS-verified dependency wired via `include_router(..., dependencies=[...])` in this codebase (hit this exact issue during the Patient/Practitioner/Organization rollout — a FastAPI/Starlette dependency-ordering quirk, root cause not fully chased down), don't try to bypass auth for a smoke test. Instead stand up a minimal real JWKS server:

1. Generate an RSA keypair (`cryptography` — already a project dependency).
2. Serve a real JWKS document + a `/mint` endpoint that signs JWTs with arbitrary claims (`sub`, `activeOrganizationId`, `permissions`).
3. Point `IAM_JWKS_URL`/`IAM_ISSUER` at it (already configurable via `.env`).
4. Hit the real endpoints with `httpx.AsyncClient` and genuinely signed tokens — covering: create (with `<resource>:create` scope), get/list/me (200s, not 401), patch/delete (200/204s, not 401/422 from a stray `created_by`/`org_id` field), cross-org access (404, not 403 or a stale client-side check), and a token with no `activeOrganizationId` claim (403 on every operation).

## Step 5 — Update CLAUDE.md

Add the new resource's name everywhere "Patient, Practitioner, and Organization" is listed as the auth-rollout set (Tech Stack table, Multi-Tenancy & Ownership section, Standard Columns section, Environment section) — do **not** describe it as a separate exception; fold it into the existing three-resource list so the document stays a single accurate set, not a growing list of special cases scattered across sections.

---

## Checklist

- [ ] `org_id`/`created_by`/`updated_by` removed from Create/Patch schemas (all levels, including sub-resources) — `user_id` untouched
- [ ] `get_<resource>_scoped()` + `<resource>_belongs_to_org()` added
- [ ] `create`/`create_full` reject a missing `actor.org_id` (403, no bypass)
- [ ] `patch`/`patch_full`/`delete`/every sub-resource method raises `NotFoundError` (404) on cross-org, never 403
- [ ] No `resolve_<resource>()` dependency remains for this resource — routes call service methods directly
- [ ] Every route gated with `require_permission("<resource>", "<action>")`
- [ ] `/me` scopes to `actor.sub` + `actor.org_id`, declared before `/{id}`
- [ ] End-to-end verified with real signed JWTs (not `dependency_overrides`) — happy path, cross-org 404, org-less 403
- [ ] CLAUDE.md's auth-rollout resource list updated in every section that names it

# Sample organization-scope profile — Organization

`org_abc123.json` is a ready-to-POST request body for
`POST /api/fhir/v1/fhir-profiles` (`FhirProfileCreateSchema`) — the **third
and most specific** layer in the base -> country -> organization profile
chain (see `docs/structure-definitions/12-three-layer-validation-architecture.md`
and `scripts/data/profiling/` for the base/country layers this one builds
on). It's a template showing how an individual hospital/clinic tenant would
define their **own** profile for the Organization resource, narrowing the
India country profile (`scripts/data/profiling/resources/organization/country_in.json`)
one step further.

**No `scope_id`, `url`, `baseDefinition`, or `id` field in the body.** For
`scope_level='organization'`, all four are fully server-derived, never
client-supplied:
- `scope_id` must be the caller's own org_id — `FhirProfileCreateSchema` rejects
  this body outright (422) if `scope_id` is supplied for this scope_level; the
  router derives it from the verified JWT's `activeOrganizationId` claim
  (`actor.org_id`) instead, same as every other org-scoped resource in this
  codebase (see CLAUDE.md's Multi-Tenancy & Ownership).
- `structure_definition.url` is auto-derived by `FhirProfileService.create_profile()`
  from `(scope_id, resource_type)` and unconditionally overwritten even if supplied
  — same convention `dispatch.py` falls back to (`org-{org_id}-{resource_type}`).
- `structure_definition.baseDefinition` is always server-resolved (country
  profile for this resource_type if one exists for the deployment's
  configured country, else base).
- `structure_definition.id` (the base FHIR `Resource.id`, distinct from
  `url` — nothing in this pipeline reads or relies on it) is always a
  fresh server-generated UUID4 on create, and kept stable across edits
  (not regenerated on PATCH, since a draft edit mutates the row, it
  doesn't replace it).

None of these four are in this sample at all, since supplying any of them
would just be ignored.

The `org_abc123` name baked into the sample's `name`/`description` fields is
just this fictional sample tenant's own label — whichever org's token
actually calls this endpoint is the org the resulting profile gets scoped
to (and the real `url` it gets), not `"org_abc123"` literally. A token with
no `activeOrganizationId` claim gets a 403 instead of creating a profile for
nobody.

Unlike the base and country layers, this layer has **no seed script and no
admin UI yet** — it's only reachable through the API directly. The only way
to create one today is this exact API call:

```
POST /api/fhir/v1/fhir-profiles
Authorization: Bearer <token with fhir_profile:create and an activeOrganizationId claim>
Content-Type: application/json

<contents of org_abc123.json>
```

It starts as `status='draft'` — call `POST /api/fhir/v1/fhir-profiles/{id}/activate`
(`fhir_profile:update`) to make it take effect, which atomically retires
whatever was previously active for `(Organization, organization, <caller's org_id>)`.

**What it changes:** tightens the `hfr-id` identifier slice from the country
layer's `0..1` (optional — not every Organization under the India profile is
itself a registered facility) to `1..1` (required) — exactly the example
`country_in.json`'s own `hfr-id` comment calls out: a tenant-layer profile for
an actual hospital/clinic/lab/pharmacy would make this mandatory. Legal per
the narrowing rule (`docs/structure-definitions/05-cardinality-and-multiplicity.md`)
since `0..1 -> 1..1` only removes already-allowed room, never adds a new
possibility the parent profile forbade.

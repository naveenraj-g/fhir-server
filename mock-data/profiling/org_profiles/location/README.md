# Sample organization-scope profile — Location

`loc_abc123.json` is a ready-to-POST request body for
`POST /api/fhir/v1/fhir-profiles` (`FhirProfileCreateSchema`) — the **third
and most specific** layer in the base -> country -> organization profile
chain (see `docs/structure-definitions/12-three-layer-validation-architecture.md`
and `scripts/data/profiling/` for the base/country layers this one builds
on). It's a template showing how an individual hospital/clinic tenant would
define their **own** profile for the Location resource, narrowing the
India country profile (`scripts/data/profiling/resources/location/country_in.json`)
one step further — the sibling of `org_profiles/organization/org_abc123.json`,
same tenant, same narrowing pattern, different resource type.

**No `scope_id`, `url`, `baseDefinition`, or `id` field in the body.** For
`scope_level='organization'`, all four are fully server-derived, never
client-supplied — same rules as the Organization sample (see that folder's
README for the full rationale):
- `scope_id` must be the caller's own org_id — rejected outright (422) if
  supplied for this scope_level; derived from the verified JWT's
  `activeOrganizationId` claim instead.
- `structure_definition.url` is auto-derived by `FhirProfileService.create_profile()`
  from `(scope_id, resource_type)` and unconditionally overwritten even if supplied
  (`org-{org_id}-location`).
- `structure_definition.baseDefinition` is always server-resolved (the India
  country profile for Location if one exists for the deployment's configured
  country, else base Location).
- `structure_definition.id` is always a fresh server-generated UUID4 on
  create, kept stable across edits.

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

<contents of loc_abc123.json>
```

It starts as `status='draft'` — call `POST /api/fhir/v1/fhir-profiles/{id}/activate`
(`fhir_profile:update`) to make it take effect, which atomically retires
whatever was previously active for `(Location, organization, <caller's org_id>)`.

**What it changes:** tightens the `hfr-id` identifier slice from the country
layer's `0..1` (optional — not every Location under the India profile is
itself a registered physical facility; a ward or room sub-Location under a
registered site wouldn't carry one) to `1..1` (required) — exactly the
example `country_in.json`'s own `hfr-id` comment calls out for a tenant-layer
profile covering an actual registered site's Location record. Legal per the
narrowing rule (`docs/structure-definitions/05-cardinality-and-multiplicity.md`)
since `0..1 -> 1..1` only removes already-allowed room, never adds a new
possibility the parent profile forbade.

**Note on `Location.extension`:** the India country profile (`in-location`)
already narrows `Location.extension` to `max=0` (no custom extensions
permitted at all) — same governance decision as `in-organization`. This
tenant-layer profile doesn't touch that element at all, since there's
nothing left to narrow below zero; it's listed here only so it isn't
mistaken for an oversight.

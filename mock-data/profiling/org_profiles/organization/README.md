# Sample organization-scope profile — Organization

`org_abc123.json` is a ready-to-POST request body for
`POST /api/v1/fhir-profiles` (`FhirProfileCreateSchema`) — the **third and
most specific** layer in the base -> country -> organization profile chain
(see `docs/structure-definitions/12-three-layer-validation-architecture.md`
and `scripts/data/profiling/` for the base/country layers this one builds
on). It's a template showing how an individual hospital/clinic tenant would
define their **own** profile for the Organization resource, narrowing the
India country profile (`scripts/data/profiling/resources/organization/country_in.json`)
one step further.

Unlike the base and country layers, this layer has **no seed script and no
admin UI yet** — `FhirProfileService.get_organization_profile()`'s own
docstring confirms the read side is wired but nothing writes one of these
rows yet. The only way to create one today is this exact API call:

```
POST /api/v1/fhir-profiles
Authorization: Bearer <token with fhir_profile:create>
Content-Type: application/json

<contents of org_abc123.json>
```

It starts as `status='draft'` — call `POST /api/v1/fhir-profiles/{id}/activate`
(`fhir_profile:update`) to make it take effect, which atomically retires
whatever was previously active for `(Organization, organization, org_abc123)`.

**What it changes:** tightens the `hfr-id` identifier slice from the country
layer's `0..1` (optional — not every Organization under the India profile is
itself a registered facility) to `1..1` (required) — exactly the example
`country_in.json`'s own `hfr-id` comment calls out: a tenant-layer profile for
an actual hospital/clinic/lab/pharmacy would make this mandatory. Legal per
the narrowing rule (`docs/structure-definitions/05-cardinality-and-multiplicity.md`)
since `0..1 -> 1..1` only removes already-allowed room, never adds a new
possibility the parent profile forbade.

`baseDefinition` in the sample is illustrative only — `FhirProfileService.create_profile()`
overwrites it server-side to the resolved parent's actual `canonical_url`
regardless of what's sent, so the chain is enforced by the service, not
trusted from this payload.

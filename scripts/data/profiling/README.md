# Profile storage — seed source for `fhir_profile`, no longer read at request time

**This directory is no longer read at validation/request time.** It was originally a
file-backed stand-in for the `fhir_profile` database table; now that table is the live
source for both layers — base and country alike — read through
`FhirProfileService`'s cache-aside layer (`app/services/fhir_profile/`,
cache config in `configs/cache.yaml`'s `fhir_profile_cache`), resolved by
`app/fhir/validation/dispatch.py` and registered with the Java validator sidecar by
`app/fhir/validation/java_validator.py` — neither touches this folder anymore. This
directory's only remaining job is as the **seed source** for the country layer
(`scripts/profiling/seed_country_profiles.py` still reads `country_<code>.json` from
here — see below for why base doesn't).

Layout:

```
base_fhir_r4.json       -- HL7's own, real, unmodified base R4 StructureDefinition
                            (verbatim from profiles-resources.json — org-1/org-2/org-3 and
                            every base R4 rule live in here, not reimplemented anywhere else).
                            Common, not per-resource — kept once at this folder's root as a
                            readable reference copy; actual base-layer seeding reads the full
                            HL7 bundle directly (see below), not this file.
resources/
  organization/
    country_in.json     -- this project's own India country-layer profile for Organization
                            (derivation: constraint, baseDefinition -> base R4 Organization)
```

A sample `OrganizationCreateSchema` payload for manual testing against the India profile
lives at the repo root, `mock-data/resources/organization/create_india_organization.json` —
this project's own API shape, not raw FHIR, so it doesn't belong alongside the real
StructureDefinition JSON here.

**Layer naming convention:**
- `base_fhir_r4.json` — the verbatim base R4 definition (same for every deployment, HL7-authored)
- `country_<code>.json` — a country-layer profile, `<code>` lowercased (e.g. `country_in.json`
  for India). Selected by `settings.fhir_validation.country` (`app/core/config.py`) — a single,
  global, deploy-time setting, not resolved per-request or per-tenant; see
  `app/fhir/validation/dispatch.py`'s module docstring for why trusting the payload's own data
  (e.g. `Organization.address.country`) to pick its own rule set would be backwards.
- Exactly **one** country profile is ever current per `(resource_type, country)` — this app's
  `dispatch.py` resolves a single canonical URL per pair (`_COUNTRY_PROFILE_URL`), and
  `FhirProfileService.activate_profile()` atomically retires whatever was previously active
  for that same scope. The DB can hold older versions too (draft/active/retired), but the file
  here only ever needs to represent the current one — git history covers the rest. That's why
  there's no per-country subfolder: one `country_<code>.json` per resource is enough.

**Both the file's on-disk name and its canonical `url` field follow one fixed convention**
(`dispatch.py`'s `_COUNTRY_PROFILE_URL`): `<fhir_validation.canonical_base_url>/fhir/StructureDefinition/<code>-<resource_type>`
— `https://fhir-server.dev` by default (`app/core/config.py`'s `FhirValidationConfig.canonical_base_url`),
change that one setting if this deployment is ever hosted under a different domain, rather than
hand-editing every profile file's `"url"` — all lowercase (e.g. `.../in-organization`). Nothing
reads a file just to discover its own URL —
the URL is derived from `(country, resource_type)` the same way the base URL is derived from
just `resource_type`. Keep a new country file's own `"url"` field consistent with this
convention, or `dispatch.py` will ask the sidecar for a URL that doesn't match what got
registered.

**Not every resource_type needs a country file from day one.** `FhirProfileService.get_country_profile()`
returns `None` for any (resource_type, country) with no matching `fhir_profile` row — `dispatch.py`
falls back to base R4 in that case, logging the fallback rather than erroring. Today, Organization
and Location each have a seeded country row (India).

**Database *seeding* doesn't source the base layer from here at all** —
`scripts/profiling/seed_base_profiles.py` reads every base resource directly from
`app/fhir/spec/profiles-resources.json` (HL7's own complete bundle — see that folder's README),
not from this folder's own `base_fhir_r4.json`, since the bundle already has all 147 base
resources and is guaranteed to never drift from this file (which was itself originally
extracted from that exact bundle). Country-layer seeding
(`scripts/profiling/seed_country_profiles.py`) still reads from here —
`country_<code>.json` files are this project's own, not HL7's, so there's no equivalent bundle
to source them from. Edit a `country_<code>.json` file here and re-run
`just fhir-profile-seed-country` to update the corresponding `fhir_profile` row — there's no
admin API for this yet, so there's also no cache-invalidation call yet either (see
`FhirProfileService.invalidate_country_profile()`'s docstring); restart the process to pick up
a changed row until that write path exists.

Every layer here — base and country alike — is a real, spec-shaped `StructureDefinition`
(`differential.element[]`, `constraint[]`, `slicing`, etc.), not the trimmed
`structure.elements`/`structure.invariants` JSONB shape that architecture document's §3
originally sketched. That trimmed shape was a reasonable simplification to propose before any
of this was built; once it came time to actually register a profile with the Java validator
sidecar (`POST /profiles`), it needs a genuine `StructureDefinition` document, so that's what
lives here — see `resources/organization/country_in.json` for a real worked example (GSTIN/PAN
required identifier slices with FHIRPath format invariants, an optional HFR ID slice), and
[`docs/structure-definitions/use-cases/`](../../../docs/structure-definitions/use-cases/README.md)
for the mechanisms it's built from.

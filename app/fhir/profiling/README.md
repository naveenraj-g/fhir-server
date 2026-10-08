# Profile storage — seed source for `fhir_profile`, no longer read at request time

**This directory is no longer read at validation/request time.** It was originally a
file-backed stand-in for the `fhir_profile` database table; now that table is the live
source for both layers — base and country alike — read through
`FhirProfileService`'s cache-aside layer (`app/services/fhir_profile_service.py`,
cache config in `configs/cache.yaml`'s `fhir_profile_cache`), resolved by
`app/fhir/validation/dispatch.py` and registered with the Java validator sidecar by
`app/fhir/validation/java_validator.py` — neither touches this folder anymore. This
directory's only remaining job is as the **seed source** for the country layer
(`app/fhir_profile/seed_country_profiles.py` still reads `country_<code>.json` from
here — see below for why base doesn't).

One real FHIR `StructureDefinition` JSON file per `(resource_type, layer)`, laid out as
`<resource_type>/<layer>.json`:

```
organization/
  base_fhir_r4.json   -- HL7's own, real, unmodified Organization StructureDefinition
                          (verbatim from profiles-resources.json — org-1/org-2/org-3 and
                          every base R4 rule live in here, not reimplemented anywhere else)
  country_in.json     -- this project's own India country-layer profile
                          (derivation: constraint, baseDefinition -> base R4 Organization)
  samples/
    create_india_organization.json  -- a realistic OrganizationCreateSchema payload
                                        (this project's own API shape, not raw FHIR) for
                                        manual testing against the India profile
```

**Layer naming convention:**
- `base_fhir_r4.json` — the verbatim base R4 definition (same for every deployment, HL7-authored)
- `country_<code>.json` — a country-layer profile, `<code>` lowercased (e.g. `country_in.json`
  for India). Selected by `settings.fhir_validation.country` (`app/core/config.py`) — a single,
  global, deploy-time setting, not resolved per-request or per-tenant; see
  `app/fhir/validation/dispatch.py`'s module docstring for why trusting the payload's own data
  (e.g. `Organization.address.country`) to pick its own rule set would be backwards.

**Both the file's on-disk name and its canonical `url` field follow one fixed convention**
(`dispatch.py`'s `_COUNTRY_PROFILE_URL`): `https://fhir-server.dev/fhir/StructureDefinition/<code>-<resource_type>`,
all lowercase (e.g. `.../in-organization`). Nothing reads a file just to discover its own URL —
the URL is derived from `(country, resource_type)` the same way the base URL is derived from
just `resource_type`. Keep a new country file's own `"url"` field consistent with this
convention, or `dispatch.py` will ask the sidecar for a URL that doesn't match what got
registered.

**Not every resource_type needs a country file from day one.** `FhirProfileService.get_country_profile()`
returns `None` for any (resource_type, country) with no matching `fhir_profile` row — `dispatch.py`
falls back to base R4 in that case, logging the fallback rather than erroring. Today, only
Organization has a seeded country row (India).

**Database *seeding* doesn't source the base layer from here at all** —
`app/fhir_profile/seed_base_profiles.py` reads every base resource directly from
`app/fhir/spec/profiles-resources.json` (HL7's own complete bundle — see that folder's README),
not from individually hand-copied `<resource_type>/base_fhir_r4.json` files, since the bundle
already has all 147 of them and is guaranteed to never drift from this folder's own
`organization/base_fhir_r4.json` (which was itself originally extracted from that exact bundle).
Country-layer seeding (`app/fhir_profile/seed_country_profiles.py`) still reads from here —
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
lives here — see `country_in.json` for a real worked example (GSTIN/PAN required identifier
slices with FHIRPath format invariants, an optional HFR ID slice), and
[`docs/structure-definitions/use-cases/`](../../../docs/structure-definitions/use-cases/README.md)
for the mechanisms it's built from.

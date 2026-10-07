# Profile storage — file-backed stand-in for `fhir_profile`

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

**Not every resource_type needs a country file from day one.** `app/fhir/validation/java_validator.py`'s
`profile_exists()` is a plain file-existence check — `dispatch.py` falls back to base R4 for any
resource_type that doesn't have a `country_<code>.json` yet, logging that fallback rather than
erroring. Today, only Organization has one.

**This directory is a deliberate stand-in for the `fhir_profile` database table** designed in
[`docs/architecture/fhir-profiling-and-extensibility-strategy.md`](../../../docs/architecture/fhir-profiling-and-extensibility-strategy.md)
§3 (`resource_type` / `scope_level` / `parent_profile_id` / `structure`) — same shape (one
resource type, an ordered set of layers), file-backed instead of DB-backed, specifically so
that swapping to the real table later only changes *where* a layer's `StructureDefinition` JSON
comes from, never how it's used once loaded. `app/fhir/validation/java_validator.py`'s
`_ensure_registered()` is the one place that reads from this directory — when the DB table
exists, only that one function's file-read needs to become a DB-read; the registration/
validation call that follows it doesn't change.

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

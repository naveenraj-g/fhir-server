# Location sample payloads

Plain-JSON request bodies for `POST /api/fhir/v1/locations/` (`create/`) and
`PATCH /api/fhir/v1/locations/{id}` (`update/`) — matching
`LocationCreateSchema`/`LocationPatchSchema` exactly (validated against the
real schemas). `Location.address` is 0..1 and flattened onto the payload as
`address_*` fields (unlike Organization's `address[]` list) — see
`LocationCreateSchema`'s own docstring.

Each numbered file exercises a different layer of the base -> country ->
organization profile chain (`docs/structure-definitions/12-three-layer-validation-architecture.md`):

| File | Layer | What it covers |
|---|---|---|
| `01_base_r4_only.json` | Base R4 only | Structurally valid per base R4 (`status`/`name`/`mode`, no address at all). **Will be rejected** against this deployment's live validator, since `fhir_validation.country: IN` means the India country profile (`scripts/data/profiling/resources/location/country_in.json`) is always enforced too — that profile requires an address with `state` and a valid PIN code. Kept as a reference for what base R4 alone requires. |
| `02_country_in.json` | Country (India) | Satisfies `country_in.json`: `address_state` present, `address_postal_code` is a valid 6-digit Indian PIN code (`^[1-9][0-9]{5}$`). No `hfr-id` identifier — optional at this layer, since not every Location under the India profile is itself a registered physical healthcare facility. |
| `03_organization_scope.json` | Organization (tenant) | Satisfies `mock-data/profiling/org_profiles/location/loc_abc123.json`, the tenant-tightened profile for Location that mirrors Organization's `org_abc123.json` narrowing — an `hfr-id` identifier present (required 1..1 at this layer, vs. optional 0..1 at the country layer), with `use: official`. Like the organization-scope profile, this layer has no seed script/admin UI yet — only reachable by POSTing to `/api/fhir/v1/fhir-profiles` directly (see that sample's own README) and activating it. |

**`04_full_with_org_reference.json`** exercises **every field**
`LocationCreateSchema` supports at once (every `identifier`/`type`/`telecom`/
`hours_of_operation`/`endpoint` sub-field, `operational_status_*`,
`physical_type_*`, all three `position_*` fields together, and every
`part_of_identifier_*` logical-reference fallback field), plus a real
**resolved** `managing_organization` reference — the Location -> Organization
cross-resource check, same mechanism `../organization/README.md`'s
`partof`/`identifier.assigner` pair exercises on the Organization side.
Replace the placeholder `"Organization/190002"` (`managing_organization`)
and the matching `identifier.assigner` with whatever id creating one of the
`organization/create/*.json` payloads actually returns, then check the
response's `managingOrganization` and `identifier[].assigner` both come
back resolved with the correct `type`/`id`/`display`.

Two of the same gotchas from the Organization payloads apply here too,
confirmed by actually POSTing this payload end-to-end against a real
database:
- No `extension` — the India Location profile (`country_in.json`) narrows
  `Location.extension` to `max=0`, same as Organization's.
- The `endpoint` entry omits `reference`/`reference_display` and uses only
  `reference_identifier_*` — same Java-validator-chokes-on-an-absolute-URL
  reason as Organization's `endpoint`. `part_of` uses only
  `part_of_identifier_*` for the same reason it's useful to exercise that
  fallback group at all: there's no second Location in this set to make a
  real `part_of` reference to (unlike `managing_organization`, which does
  have a real Organization to resolve against).

`update/*.json` are PATCH fragments for the same three scenarios.
`Location.address` fields are flattened scalars, not a list, so a PATCH
only needs to supply the specific `address_*` fields being changed — unlike
`identifier`, which is still a list and replaces wholesale when supplied.

All three `create/*.json` files pass `app.fhir.validation.base_r4.validate_base_r4`
(the backend-agnostic base R4 structural check) — only the country/organization
layer determines which ones pass the *live* validator in this deployment.

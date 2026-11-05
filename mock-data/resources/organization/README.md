# Organization sample payloads

Plain-JSON request bodies for `POST /api/fhir/v1/organizations/` (`create/`)
and `PATCH /api/fhir/v1/organizations/{id}` (`update/`) — matching
`OrganizationCreateSchema`/`OrganizationPatchSchema` exactly (validated
against the real schemas; see `scripts/data/profiling/` for the actual
StructureDefinition files these payloads are designed to satisfy or fail).

Each numbered file exercises a different layer of the base -> country ->
organization profile chain (`docs/structure-definitions/12-three-layer-validation-architecture.md`):

| File | Layer | What it covers |
|---|---|---|
| `01_base_r4_only.json` | Base R4 only | Structurally valid per base R4 (`name`/`active`, no identifiers, no `type`/`address`/`telecom` at all). **Will be rejected** against this deployment's live validator, since `configs/config.yaml`'s `fhir_validation.country: IN` means the India country profile is always enforced too — that profile requires GSTIN + PAN identifiers *and*, as of the latest revision, at least one `name` (already present here), `type`, `address`, and `telecom` entry each. Kept as a reference for what base R4 alone requires, or for a deployment with no country configured. |
| `02_country_in.json` | Country (India) | Satisfies `scripts/data/profiling/resources/organization/country_in.json` — GSTIN + PAN identifiers present, correct format, `use: official`, plus the required-non-empty `name`/`type`/`address`/`telecom` (one entry each is enough; the profile only narrows each list's cardinality to 1..*, not any sub-field within the one entry). No `hfr-id` — optional at this layer, since not every Organization under the India profile is itself a registered facility. |
| `03_organization_scope.json` | Organization (tenant) | Satisfies the sample tenant profile at `mock-data/profiling/org_profiles/organization/org_abc123.json`, which tightens `hfr-id` from optional to required (1..1) for a tenant that IS a registered ABDM healthcare facility — includes GSTIN, PAN, and `hfr-id`. |

**`04_full_parent.json` / `05_full_child_with_partof.json`** — a matched pair
exercising **every field** `OrganizationCreateSchema` supports at once
(every `identifier`/`type`/`telecom`/`address`/`contact`/`endpoint`
sub-field, including every `assigner_identifier_*`/`reference_identifier_*`
logical-reference fallback group), plus real cross-resource referencing:

- `04_full_parent.json` is a standalone top-level Organization (no `partof`)
  — every identifier's `assigner_identifier_*` fallback is used in its
  "unresolvable" logical-reference form (no local Organization to point
  `assigner` at).
- `05_full_child_with_partof.json` references the parent with a **resolved**
  reference on two separate fields — `partof` (replace the placeholder
  `"Organization/190001"` with whatever id creating `04_full_parent.json`
  actually returns) and one `identifier.assigner` (same substitution) — to
  check both reference-resolution code paths (`partOf` and
  `identifier.assigner`) actually resolve to the real parent row, with the
  correct `type`/`id`/`display` coming back on a subsequent `GET`.
- Neither includes `extension` — the India country profile
  (`country_in.json`) narrows `Organization.extension` to `max=0`, so a
  payload that includes one is correctly rejected (422) by the live
  validator in this deployment; confirmed by actually POSTing these
  payloads end-to-end against a real database and checking the response.
- Each `endpoint` entry omits `reference`/`reference_display` and uses only
  the `reference_identifier_*` fallback — `Endpoint` isn't a modeled
  resource here, and the Java validator sidecar chokes on an absolute
  external URL in `Reference.reference` (`"Invalid reference id ... Id must
  be an integer"`, since it still tries to parse a trailing path segment as
  a local numeric id even for a non-local reference) — the identifier
  fallback is both the schema's own documented way to handle this case and
  the one that actually passes.

Verified live: creating `04_full_parent.json` then `05_full_child_with_partof.json`
(with the real parent id substituted in) produces a child row whose `partOf`
and `identifier.assigner` both come back correctly resolved to the parent —
same mechanism Location's `managing_organization` reference relies on (see
`../location/README.md`).

`update/*.json` are PATCH fragments for the same three scenarios — remember
every supplied sub-resource *list* (like `identifier`) replaces the stored
list wholesale; a PATCH that touches `identifier` without including a
previously-set GSTIN/PAN/hfr-id value drops it. `01_base_r4_only.json`
deliberately doesn't touch `identifier` at all, so it's layer-agnostic (it
stays compliant with whatever profile the row already satisfied).

All three `create/*.json` files pass `app.fhir.validation.base_r4.validate_base_r4`
(the backend-agnostic base R4 structural check) — only the country/organization
layer determines which ones pass the *live* validator in this deployment.

# FHIR R4 Search — Backlog

What's still missing from FHIR R4 search (https://www.hl7.org/fhir/R4/search.html) after the
Organization rollout. The engine is resource-agnostic (`app/fhir/search/`); Organization is the
only resource on it so far (`app/repository/organization/search.py`).

Recommended order: 1 → 2 → 3 → 4 → 5 → 6.

## Already implemented (Organization, Location)

- All 13 R4 Organization search parameters: `active`, `address`, `address-city`,
  `address-country`, `address-postalcode`, `address-state`, `address-use`, `endpoint`,
  `identifier`, `name`, `partof`, `phonetic`, `type`.
- All 15 R4 Location search parameters: `address`, `address-city`, `address-country`,
  `address-postalcode`, `address-state`, `address-use`, `endpoint`, `identifier`, `name`,
  `near` (with the `location-distance` result extension), `operational-status`,
  `organization` (chainable into Organization's parameters), `partof` (hierarchy +
  chaining), `status`, `type`.
- String matching: case- and accent-insensitive starts-with, plus `:exact` and `:contains`.
- Token: `code`, `system|code`, `|code`, `system|`, plus these modifiers:
  - `:not` and `:text`
  - `:of-type` (on `identifier`)
  - `:in`, `:not-in`, `:above`, `:below` (on `type`)
- Reference:
  - values: an id, `Type/id`, or an absolute URL
  - modifiers: `:[type]`, `:identifier`, `:above` and `:below` (the partOf hierarchy)
  - chaining
- `:missing` on every parameter; comma = OR, repeat = AND; `\` escaping.
- `_id`, `_lastUpdated` (all nine date prefixes).
- `_sort`, `_count`, `_offset`, `_total`, `_summary`, `_elements`.
- `_include` / `_revinclude` (with `:iterate`), across resource types: `Organization:partof`,
  `Location:organization`, `Location:partof`, and on Organization
  `_revinclude=Location:organization`.
- Bundle: `link` (self/first/previous/next/last), `entry.fullUrl`, `entry.search.mode`.
- `POST _search` (form body).
- Error handling: a bad value or unsupported modifier → 400; unknown parameters are ignored
  and reported in an outcome entry, or rejected with `Prefer: handling=strict`.

---

## 1. Store client `meta`, and search it: `_tag`, `_profile`, `_security`, `_source`

| Parameter | Searches | Meaning |
|---|---|---|
| `_tag` | `meta.tag` (Coding) | Free labels: "test data", "imported", "needs review" |
| `_profile` | `meta.profile` (canonical) | The profile the resource claims to follow |
| `_security` | `meta.security` (Coding) | Security labels, e.g. confidentiality N / R / V |
| `_source` | `meta.source` (uri) | The system the data came from |

**Why it's missing:** `app/fhir/input_payload.py` drops the client's whole `meta` on
create/patch, so nothing is stored to search.

**To do:**
- Keep `versionId` and `lastUpdated` server-managed.
- Store the client's `profile`, `tag`, `security` and `source` in `content`.
- Index them: `tag`/`security` as token rows, `profile`/`source` as uri.
- Register the four parameters.

**Decision needed:** when a client sends `meta.profile`, which profile do we validate against?
- **(a)** The claimed profile. This is strict, but an unknown profile URL means a 422.
- **(b)** Store it, but keep validating with the base → country → org chain.

## 2. Endpoint resource

`Organization.endpoint` points at `Endpoint/<id>`, but Endpoint isn't a resource on this server
yet. Because of that:
- Endpoint references can't be existence-checked.
- `_include=Organization:endpoint` returns nothing.
- `endpoint.<param>` chaining returns 400.

**To do:**
- Build Endpoint Medplum-style from day one (sequence block 620000). Its fields: `status`,
  `connectionType`, `managingOrganization`, `payloadType`, `address`.
- Search parameters: `connection-type`, `identifier`, `name`, `organization`, `payload-type`,
  `status`.
- Then register `chain_targets={"Endpoint": ...}` on Organization's `endpoint` parameter.

## 3. `_revinclude` and `_has` from resources that reference Organization

- `_revinclude` returns the resources that point *at* the matches, e.g.
  `_revinclude=Location:organization`.
- `_has` filters by them, e.g. `_has:Location:organization:name=Ward`.

Both need the referencing resource declared in the search engine.

Done so far: Organization `_revinclude=Location:organization` (Location is on the engine).

Resources that reference Organization, still to do:
- `PractitionerRole.organization`
- `HealthcareService.providedBy`
- `Patient.managingOrganization`
- `Encounter.serviceProvider`
- `Endpoint.managingOrganization`
- …and more

`_has` is not implemented for any pair yet, including Organization ← Location.

**To do:**
- **Light:** register only their reference parameters. That covers `_revinclude`, and `_has`
  when the condition is on the reference itself.
- **Full:** move each resource onto the engine, so `_has` works with any of its parameters.

## 4. `_text` / `_content` (full-text search)

- `_text` searches the narrative (`text.div`).
- `_content` searches the whole resource.

**Why it's missing:** there's no full-text index.

**To do:**
- Add a Postgres `tsvector` column with a GIN index, built from the narrative or from every
  string value in `content`.
- Add a fallback for the SQLite test DB.

## 5. `_filter`

A separate expression language: `_filter=name co "acme" and active eq true`
(https://www.hl7.org/fhir/R4/search_filter.html). Optional in R4.

**To do:** write a parser that turns the expression into the conditions the registry already
builds.

## 6. `_list`, `_type`, `_contained` (low priority)

- **`_list`** returns only the resources in a FHIR `List` (`_list=42`). It needs a `List`
  resource first.
- **`_type`** only makes sense on whole-server search (`GET [base]?_type=Organization,Location`).
  It needs a system-level search endpoint, once several resources are on the engine.
- **`_contained`** searches resources embedded in `contained[]`. It needs each contained
  resource indexed as its own search row. Rarely used.

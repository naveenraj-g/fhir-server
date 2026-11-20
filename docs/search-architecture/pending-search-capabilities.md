# Search: what is implemented and what is pending

Audit of the FHIR R4 search engine (`app/fhir/search/`) against the HL7 R4 search spec
(https://www.hl7.org/fhir/R4/search.html). Based on a code read, not a live test run.
Diagram of the current design: [`../architecture/search-architecture.html`](../architecture/search-architecture.html).

## Plan

Everything pending here is a **capability of the shared engine** or a **per-resource search registry**.
None of it needs to be built now. The intended order:

1. Finish building the remaining resources.
2. Give each resource its own `SearchRegistry` (like `app/repository/organization/search.py` and
   `app/repository/location/search.py`). The engine is resource-agnostic, so a resource only declares its
   parameters, index columns and tables, and its `_indexer.py`.
3. Add the pending engine-level capabilities from section 4 once they can be exercised across many resources.

## 1. Scope today

The R4 search engine covers **Organization, Location, Practitioner, HealthcareService, Endpoint, PractitionerRole, Schedule, Slot, Patient, Appointment, AppointmentResponse, Encounter, RelatedPerson, AllergyIntolerance and Condition** (Practitioner added 2026-11-18, with `/me`; the end-user link is a separate `PUT /practitioners/{id}/user`, not a search/FHIR concern). Every other resource (Observation,
Condition, ...) still uses the old per-resource list filters: no modifiers, no chaining, no `_include`, no `_sort`
beyond what each repository hand-rolled. Moving them onto the engine is the biggest pending item.

## 2. Resource-specific parameters

| Resource | R4 defines | Implemented | Missing |
|---|---|---|---|
| Organization | 13 | 13 | none |
| Location | 15 | 15 | none |
| Practitioner | 17 | 17 | none |
| HealthcareService | 12 | 12 | none |
| Endpoint | 6 | 6 | none |
| PractitionerRole | 13 | 13 | none |
| Schedule | 7 | 7 | none |
| Appointment | 17 | 17 | none |
| AppointmentResponse | 7 | 7 | none |
| Encounter | 23 | 23 | none |
| RelatedPerson | 17 | 17 | none |
| AllergyIntolerance | 16 | 16 | none |
| Condition | 21 | 21 | none |
| All other resources | - | 0 (old list filters) | everything: needs a registry each |

- Organization: `active`, `address`, `address-city`, `address-country`, `address-postalcode`, `address-state`,
  `address-use`, `endpoint`, `identifier`, `name`, `partof`, `phonetic`, `type`.
- Location: the same address set, plus `endpoint`, `identifier`, `name`, `near`, `operational-status`,
  `organization`, `partof`, `status`, `type`.
- Practitioner: `active`, `address`, `address-city`, `address-country`, `address-postalcode`, `address-state`,
  `address-use`, `communication`, `email`, `family`, `gender`, `given`, `identifier`, `name`, `phone`, `phonetic`,
  `telecom`. No `_include`/`_revinclude` targets yet; `_sort` works on every parameter except `given`, `name`, `phonetic`,
  `email`, `phone`, `telecom` and `address`.
- HealthcareService: `active`, `characteristic`, `coverage-area`, `endpoint`, `identifier`, `location`, `name`,
  `organization`, `program`, `service-category`, `service-type`, `specialty`. `organization`, `location` and `coverage-area` chain;
  every parameter is sortable.
- Endpoint: `connection-type`, `identifier`, `name`, `organization`, `payload-type`, `status`. `organization` chains; every
  parameter is sortable.
- PractitionerRole: `active`, `date`, `email`, `endpoint`, `identifier`, `location`, `organization`, `phone`,
  `practitioner`, `role`, `service`, `specialty`, `telecom`. `date` is a Period search (range semantics, see below);
  `practitioner`, `organization`, `location` and `service` chain; every parameter is sortable.
- Encounter: `account`, `appointment`, `based-on`, `class`, `date`, `diagnosis`, `episode-of-care`, `identifier`, `length`, `location`,
  `location-period`, `part-of`, `participant`, `participant-type`, `patient`, `practitioner`, `reason-code`, `reason-reference`,
  `service-provider`, `special-arrangement`, `status`, `subject`, `type`. `class` is a token on a bare Coding; `date` and `location-period`
  are Period searches; `length` is a quantity search; `subject`, `participant`, `diagnosis` and `reason-reference` are multi-target
  (need a type); `appointment`, `location`, `participant`, `patient`, `practitioner`, `part-of`, `service-provider` and `subject` chain
  through the targets that are resources here; every parameter is sortable.
- RelatedPerson: `active`, `address`, `address-city`, `address-country`, `address-postalcode`, `address-state`, `address-use`,
  `birthdate`, `email`, `gender`, `identifier`, `name`, `patient`, `phone`, `phonetic`, `relationship`, `telecom`. `birthdate` is a date held
  as the range it covers; `patient` chains into Patient; every parameter except `address`, `address-use`, `phonetic`, `phone`, `email` and `telecom` is sortable.
- AllergyIntolerance: `asserter`, `category`, `clinical-status`, `code`, `criticality`, `date`, `identifier`, `last-date`, `manifestation`, `onset`, `patient`, `recorder`, `route`, `severity`, `type`, `verification-status`. `date`, `last-date` and `onset` are dateTimes held as the range they cover (`onset` reads `reaction.onset`); `code` also reads `reaction.substance`; `category`, `severity`, `type` and `criticality` are plain `code` elements bound to one system (`:not`/`:missing` only); `recorder` and `asserter` are multi-target (need a type; chain through `recorder|asserter:Practitioner|PractitionerRole|Patient|RelatedPerson`); `patient` chains into Patient; every parameter is sortable.
- Condition: `abatement-age`, `abatement-date`, `abatement-string`, `asserter`, `body-site`, `category`, `clinical-status`, `code`, `encounter`, `evidence`, `evidence-detail`, `identifier`, `onset-age`, `onset-date`, `onset-info`, `patient`, `recorded-date`, `severity`, `stage`, `subject`, `verification-status`. `onset-age`/`abatement-age` are quantity searches over an Age or a Range (`quantity_range_match`); `onset-date`/`abatement-date`/`recorded-date` are dateTime/Period ranges; `subject`, `asserter` and `evidence-detail` are multi-target (need a type); `patient` is `subject` narrowed to Patients; `patient`, `encounter`, `asserter:<Type>` and `evidence-detail:<Type>` chain; every parameter is sortable.
- Schedule: `active`, `actor`, `date`, `identifier`, `service-category`, `service-type`, `specialty`. `actor` is a multi-target
  reference (needs a type; chains through `actor:Practitioner|PractitionerRole|HealthcareService|Location`); `date` is a Period search over
  `planningHorizon`; every parameter is sortable.

## 3. Implemented (engine level)

| Feature | Status |
|---|---|
| string: starts-with (case/accent-insensitive), `:exact`, `:contains` | done |
| token: `code`, `system\|code`, `\|code`, `system\|`; `:not`, `:text`, `:of-type`, `:in`, `:not-in`, `:above`, `:below` | done (terminology-backed) |
| reference: id, `Type/id`, absolute URL; `:[type]`, `:identifier`, `:above`, `:below` | done |
| chaining (`partof.name=`), recursive | done |
| date: 9 prefixes, precision-aware (point-in-time targets and **Period** targets via `period_match`) | done |
| quantity: `[prefix]number[\|system\|code]`, precision-aware range, `\|\|code` also matches the unit text (no UCUM conversion) | done |
| special: `near` (+ `location-distance` extension) | done |
| `:missing` on every parameter | done |
| comma = OR, repeat = AND, escaping | done |
| bad value / unsupported modifier -> 400 | done |
| `_id`, `_lastUpdated` | done |
| `_count` (default 50, max 200, `0` = count only), `_offset` | done |
| `_sort` (multi-key, `-desc`, earliest/latest rule for multi-valued) | done |
| `_total`, `_summary`, `_elements` (SUBSETTED tag) | done |
| `_include` / `_revinclude` / `:iterate` | done for the registered targets (see 4.5) |
| searchset Bundle: `total`, `fullUrl`, `search.mode`, self/first/previous/next/last links | done |
| `POST [type]/_search` (form-encoded) | done |

## 4. Pending

### 4.1 Common parameters not implemented

Current behaviour: ignored with a `search.mode=outcome` entry, or 400 under `Prefer: handling=strict`.
This is spec-legal (R4 allows lenient handling) but still a capability gap.

| Parameter | Notes |
|---|---|
| `_tag`, `_profile`, `_security`, `_source` | Cheap to search, but `meta` is stripped on write today, so this needs a storage change (persist and index `meta.tag`, `meta.profile`, `meta.security`, `meta.source`) as well as a search change. |
| `_has` (reverse chaining) | Most valuable missing feature, e.g. "organizations that have an active Location". Needs the registry to know which resource types reference which. Best done once many resources have registries. |
| `_type` | Only meaningful with system-wide search (4.3). |
| `_text`, `_content` | Full-text search. Needs a text index strategy. Expensive. |
| `_list` | Needs the List resource. |
| `_filter` | Full filter expression language. Expensive, rarely used. |
| `_contained`, `_containedType` | Only the default is accepted; anything else is 400. |
| `_format` | JSON only. `_pretty` is accepted with no effect. |
| `_sort=_score` | 400. No relevance scoring. |
| `_query` | Always 400 (named queries not supported). |

### 4.2 Parameter types not implemented

number, uri and composite (**quantity is done** — Encounter `length`, `app/fhir/search/quantity.py`: `[prefix]number[|system|code]`,
precision-aware range for `eq`/`ne`, units compared as written with no UCUM conversion, `||code` also matches the human unit text). Organization and Location have none, but clinical resources will
(Observation `value-quantity`, `code-value-quantity` composites, Patient `birthdate` is date, ValueSet `url` is uri, ...).
Each needs a type builder in `app/fhir/search/sql.py` and a parser in `values.py`.

### 4.3 Protocol-level features

| Feature | Status |
|---|---|
| System-wide search (`GET [base]?_type=...`) | not implemented |
| `_history` (instance, type, system) | no history endpoint exists |
| Conditional operations (`If-None-Exist`, conditional update/delete) | not checked in this audit; no sign of them |
| `CapabilityStatement` (`GET /api/fhir/v1/metadata`) | **done** (`app/fhir/capability.py`, `app/routers/capability.py`). Generated per request from the search registries and `routes.enabled`; lists only resources on the search engine. Adding a resource = one line in `SEARCH_REGISTRIES`. Terminology's own `/metadata` is separate and deferred. |

### 4.4 Per-resource work (when each resource gets its registry)

For each resource, follow the Organization/Location pattern:

- Add index columns / child tables, populated by that resource's `_indexer.py` on every write.
- Declare a `SearchRegistry` with every R4 search parameter for the resource.
- Declare its `IncludeTarget`s (`_include` / `_revinclude`) and register a `ResourceKind` so included rows render.
- Declare `default_sort` and `summary_elements`.
- Use `app/routers/_fhir_search.py` for the route glue and add `POST /_search`.
- OpenAPI parameters come from the registry automatically (MCP callers discover them).

### 4.5 `_include` / `_revinclude` gaps

- Working today: `Organization:partof`, `Location:organization`, `Location:partof`,
  `HealthcareService:organization`, `HealthcareService:location`, `HealthcareService:coverage-area`,
  `PractitionerRole:practitioner|organization|location|service|endpoint`, `Schedule:actor[:Type]`, `Organization:endpoint`, `Location:endpoint`, `HealthcareService:endpoint`, `Endpoint:organization`, and
  `_revinclude` of `Organization:partof`, `Location:organization`, `Location:partof`,
  `HealthcareService:organization` (on Organization), `HealthcareService:location` / `:coverage-area` (on Location),
  `Endpoint:organization` (on Organization), `Organization:endpoint` / `Location:endpoint` / `HealthcareService:endpoint` (on Endpoint),
  `PractitionerRole:practitioner` / `:organization` / `:location` / `:service` / `:endpoint` (on Practitioner, Organization,
  Location, HealthcareService and Endpoint respectively), `Schedule:actor` (on Practitioner, PractitionerRole, HealthcareService and Location), `Slot:schedule` (on Schedule), `Patient:general-practitioner` (on Practitioner, PractitionerRole and Organization), `Patient:organization` (on Organization) `Patient:link` (on Patient), `Appointment:actor|patient|practitioner|location` (on Patient, Practitioner, PractitionerRole, HealthcareService and Location) `Appointment:slot` (on Slot), `AppointmentResponse:appointment` (on Appointment) and `AppointmentResponse:actor|patient|practitioner|location` (on Patient, Practitioner, PractitionerRole, HealthcareService and Location), plus `Encounter:patient|subject` (on Patient), `Encounter:participant|practitioner` (on Practitioner; `participant` also on PractitionerRole), `Encounter:location` (on Location), `Encounter:appointment` (on Appointment), `Encounter:service-provider` (on Organization) and `Encounter:part-of` (on Encounter), plus `RelatedPerson:patient` (on Patient) and, on RelatedPerson, `Appointment:actor`, `AppointmentResponse:actor`, `Encounter:participant` and `Patient:link`, plus `AllergyIntolerance:patient` (on Patient) and `AllergyIntolerance:recorder|asserter` (on Patient, Practitioner, PractitionerRole and RelatedPerson), plus `Condition:subject|patient` (on Patient), `Condition:asserter` (on Patient, Practitioner, PractitionerRole and RelatedPerson), `Condition:encounter` (on Encounter), and, on Condition, `Encounter:diagnosis|reason-reference` and `Appointment:reason-reference`; `Encounter:diagnosis|reason-reference` and `Appointment:reason-reference` also `_include` Conditions.
- `_revinclude` from resources that point at Organization/Location (Observation, ...)
  becomes possible only when those resources are on the engine.

## 5. Suggested order after the resources exist

1. Registry for every resource (the bulk of the work; mechanical).
2. `CapabilityStatement` generated from the registries, so the server declares what it supports.
3. `_tag` / `_profile` / `_security` / `_source` (with the `meta` storage change).
4. `_has`.
5. number / uri / composite types, and UCUM unit conversion for quantity, as the clinical resources need them.
6. Later or never: `_text`, `_content`, `_filter`, `_list`, `_contained`, `_history`, system-wide search.

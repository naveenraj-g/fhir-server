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

The R4 search engine covers **Organization, Location, Practitioner, HealthcareService, Endpoint, PractitionerRole, Schedule, Slot, Patient, Appointment, AppointmentResponse, Encounter, RelatedPerson, AllergyIntolerance, Condition, Procedure, DiagnosticReport, Immunization, ImmunizationRecommendation, ImmunizationEvaluation, FamilyMemberHistory, RiskAssessment, ClinicalImpression, DetectedIssue, Observation, Specimen, ServiceRequest, Medication, MedicationRequest, Group, CareTeam, CarePlan, EpisodeOfCare, DocumentReference, QuestionnaireResponse, Questionnaire, MedicationStatement, MedicationAdministration and MedicationDispense** (Practitioner added 2026-11-18, with `/me`; the end-user link is a separate `PUT /practitioners/{id}/user`, not a search/FHIR concern). Every other resource (Observation,
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
| Procedure | 16 | 16 | none |
| DiagnosticReport | 16 | 16 | none |
| Immunization | 16 | 16 | none |
| ImmunizationRecommendation | 8 | 8 | none |
| ImmunizationEvaluation | 7 | 7 | none |
| FamilyMemberHistory | 9 | 9 | none |
| RiskAssessment | 10 | 10 | none |
| ClinicalImpression | 13 | 13 | none |
| DetectedIssue | 6 | 6 | none |
| Observation | 38 | 38 | none |
| Specimen | 12 | 12 | none |
| ServiceRequest | 21 | 21 | none |
| Medication | 9 | 9 | none |
| MedicationRequest | 16 | 16 | none |
| Group | 10 | 10 | none |
| CareTeam | 8 | 8 | none |
| CarePlan | 20 | 20 | none |
| EpisodeOfCare | 9 | 9 | none |
| DocumentReference | 24 | 24 | none |
| QuestionnaireResponse | 11 | 11 | none |
| Questionnaire | 19 | 19 | none |
| MedicationStatement | 11 | 11 | none |
| MedicationAdministration | 13 | 13 | none |
| MedicationDispense | 15 | 15 | none |
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
- Procedure: `based-on`, `category`, `code`, `date`, `encounter`, `identifier`, `instantiates-canonical`, `instantiates-uri`, `location`, `part-of`, `patient`, `performer`, `reason-code`, `reason-reference`, `status`, `subject`. `instantiates-uri` is the engine's first `uri` search (`uri_match`: exact, `:below`, `:above`); `instantiates-canonical` matches canonical URLs (an unversioned URL also finds the versioned ones); `date` is a dateTime/Period range; `subject`, `performer`, `based-on`, `part-of`, `reason-reference` are multi-target (need a type); `patient` is `subject` narrowed to Patients; `patient`, `encounter`, `location`, `performer:<Type>`, `part-of:Procedure` and `reason-reference:<Type>` chain; every parameter is sortable.
- Observation: `based-on`, `category`, `code`, `code-value-concept`, `code-value-date`, `code-value-quantity`, `code-value-string`, `combo-code`, `combo-code-value-concept`, `combo-code-value-quantity`, `combo-data-absent-reason`, `combo-value-concept`, `combo-value-quantity`, `component-code`, `component-code-value-concept`, `component-code-value-quantity`, `component-data-absent-reason`, `component-value-concept`, `component-value-quantity`, `data-absent-reason`, `date`, `derived-from`, `device`, `encounter`, `focus`, `has-member`, `identifier`, `method`, `part-of`, `patient`, `performer`, `specimen`, `status`, `subject`, `value-concept`, `value-date`, `value-quantity`, `value-string`. The eight composites (`$`-joined `code$value`, same element — see `app/fhir/search/composite.py`) are the engine's first; the `combo-*` parameters are the union of an Observation-level and a component-level one. `value-quantity` is a quantity search over a Quantity (SampledData is not indexed); `value-string` is starts-with / `:contains` only; `date` reads a dateTime, instant, Period or Timing; `focus` is Reference(Any); composites take no modifiers and are not sortable or chainable; every other parameter is sortable.
- Specimen: `accession`, `bodysite`, `collected`, `collector`, `container`, `container-id`, `identifier`, `parent`, `patient`, `status`, `subject`, `type`. `collected` reads a dateTime or a Period; `container` and `container-id` read every container; `parent` is a self-reference; `subject` and `collector` are multi-target; every parameter is sortable.
- ServiceRequest: `authored`, `based-on`, `body-site`, `category`, `code`, `encounter`, `identifier`, `instantiates-canonical`, `instantiates-uri`, `intent`, `occurrence`, `patient`, `performer`, `performer-type`, `priority`, `replaces`, `requester`, `requisition`, `specimen`, `status`, `subject`. `occurrence` reads a dateTime, a Period or a Timing; `subject`, `requester`, `performer` and `based-on` are multi-target; `instantiates-*` work as on Procedure; every parameter is sortable.
- Medication: `code`, `expiration-date`, `form`, `identifier`, `ingredient`, `ingredient-code`, `lot-number`, `manufacturer`, `status`. `lot-number` is a token over a string (code only); `ingredient-code` reads every ingredient; `ingredient` is a Substance | Medication reference; every parameter is sortable.
- MedicationRequest: `authoredon`, `category`, `code`, `date`, `encounter`, `identifier`, `intended-dispenser`, `intended-performer`, `intended-performertype`, `intent`, `medication`, `patient`, `priority`, `requester`, `status`, `subject`. `date` reads every dosage instruction's `timing.event`; `code` reads `medicationCodeableConcept` and `medication` reads `medicationReference`; `subject`, `requester` and `intended-performer` are multi-target; every parameter is sortable.
- Group: `actual`, `characteristic`, `characteristic-value`, `code`, `exclude`, `identifier`, `managing-entity`, `member`, `type`, `value`. `characteristic-value` is a composite (`code$value` on the same characteristic, paired by slot — no modifiers, not sortable or chainable); `actual` / `exclude` are boolean tokens; `value` reads a CodeableConcept or a boolean; `member` and `managing-entity` are multi-target; every other parameter is sortable.
- CareTeam: `category`, `date`, `encounter`, `identifier`, `participant`, `patient`, `status`, `subject`. `date` is a Period search over `period` (a care team with no period never matches); `subject` and `participant` are multi-target; `patient` is `subject` narrowed to Patients; every parameter is sortable.
- CarePlan: `activity-code`, `activity-date`, `activity-reference`, `based-on`, `care-team`, `category`, `condition`, `date`, `encounter`, `goal`, `identifier`, `instantiates-canonical`, `instantiates-uri`, `intent`, `part-of`, `patient`, `performer`, `replaces`, `status`, `subject`. `date` and `activity-date` are Period searches (a Timing counts from its earliest to its latest event; a care plan with no period / no schedule never matches); `subject`, `performer` and `activity-reference` are multi-target; `patient` is `subject` narrowed to Patients; every parameter is sortable.
- EpisodeOfCare: `care-manager`, `condition`, `date`, `identifier`, `incoming-referral`, `organization`, `patient`, `status`, `type`. `date` is a Period search over `period`; `care-manager` is `careManager` resolved to a Practitioner; `condition` and `incoming-referral` read every `diagnosis.condition` / `referralRequest`; every reference has one target so a bare id works; every parameter is sortable.
- DocumentReference: `author`, `authenticator`, `category`, `contenttype`, `custodian`, `date`, `description`, `encounter`, `event`, `facility`, `format`, `identifier`, `language`, `location`, `patient`, `period`, `related`, `relatesto`, `relation`, `relationship`, `security-label`, `setting`, `status`, `subject`, `type`. `relationship` is a composite (`<relatesto>$<relation>`, both on the same relatesTo entry); `location` is a `uri` search; `identifier` reads masterIdentifier and identifier; `period` is a Period search over `context.period`; `contenttype` and `language` are code-only token searches over every content entry; every parameter except `relationship` is sortable.
- QuestionnaireResponse: `author`, `authored`, `based-on`, `encounter`, `identifier`, `part-of`, `patient`, `questionnaire`, `source`, `status`, `subject`. R4 defines no parameter for the answers, so `item` is not indexed; `authored` is a dateTime range; `subject` is Reference(Any) and `patient` is `subject` narrowed to Patients; `questionnaire` is a canonical URL (an unversioned URL also finds stored versions); every parameter is sortable.
- Questionnaire: `code`, `context`, `context-quantity`, `context-type`, `context-type-quantity`, `context-type-value`, `date`, `definition`, `description`, `effective`, `identifier`, `jurisdiction`, `name`, `publisher`, `status`, `subject-type`, `title`, `url`, `version`. `code` / `definition` read `item.code` / `item.definition` at every depth; `date` and `effective` are range searches; `context-quantity` reads a Quantity or a Range; the two composites pair a useContext's code with its value; `subject-type` is an enum array (required binding); `version` is a token over a plain string; `url` and `definition` are uri searches (`:below` / `:above`).
- MedicationStatement: `category`, `code`, `context`, `effective`, `identifier`, `medication`, `part-of`, `patient`, `source`, `status`, `subject`. `effective` is a dateTime *or* a Period held as one range; `code` reads `medicationCodeableConcept` and `medication` the `medicationReference`; `subject` (Patient | Group), `context`, `source` and `part-of` are multi-target (bare id -> 400); `patient` is `subject` narrowed to Patients; `basedOn`, `derivedFrom`, `reasonCode`, `reasonReference`, `note` and `dosage` have no search parameter.
- MedicationAdministration: `code`, `context`, `device`, `effective-time`, `identifier`, `medication`, `patient`, `performer`, `reason-given`, `reason-not-given`, `request`, `status`, `subject`. `effective-time` is a dateTime *or* a Period held as one range; `code` reads `medicationCodeableConcept`, `medication` the `medicationReference`, `reason-given` / `reason-not-given` every `reasonCode` / `statusReason`; `subject` (Patient | Group), `context` and `performer` are multi-target (bare id -> 400); `patient` is `subject` narrowed to Patients; `partOf`, `category`, `reasonReference`, `note`, `dosage` and `eventHistory` have no search parameter.
- MedicationDispense: `code`, `context`, `destination`, `identifier`, `medication`, `patient`, `performer`, `prescription`, `receiver`, `responsibleparty`, `status`, `subject`, `type`, `whenhandedover`, `whenprepared`. `whenprepared` / `whenhandedover` are dateTimes held as ranges; `code` reads `medicationCodeableConcept`, `medication` the `medicationReference`; `subject`, `context`, `performer`, `receiver` and `responsibleparty` are multi-target (bare id -> 400); `patient` is `subject` narrowed to Patients; `medication`, `destination` and `prescription` have one target; `partOf`, `statusReason[x]`, `category`, `location`, `quantity`, `daysSupply`, `note`, `dosageInstruction`, `substitution` (apart from `responsibleParty`), `detectedIssue` and `eventHistory` have no search parameter.
- DetectedIssue: `author`, `code`, `identified`, `identifier`, `implicated`, `patient`. R4 defines no `status` or `severity` parameter for this resource. `identified` is a date range over `identified[x]` (a dateTime or a Period; an open-ended Period reaches everything on its side); `code` is a token on a CodeableConcept; `implicated` is Reference(Any) (needs a type); `author` is multi-target (needs a type); `patient` takes a bare id; `patient`, `author` (Practitioner, PractitionerRole) and `implicated` (rebuilt types) chain; every parameter is sortable.
- ClinicalImpression: `assessor`, `date`, `encounter`, `finding-code`, `finding-ref`, `identifier`, `investigation`, `patient`, `previous`, `problem`, `status`, `subject`, `supporting-info`. `status` is a plain code (system `http://hl7.org/fhir/event-status`); `date` is a dateTime range over `date` (`effective[x]` is not searchable); `finding-code` reads `finding.itemCodeableConcept` of every finding; `problem`, `investigation` (`investigation.item`), `finding-ref` (`finding.itemReference`) and `supporting-info` (Reference(Any)) live in one shared reference table; `subject`, `assessor` and those four are multi-target (need a type); `patient`, `encounter` and `previous` take a bare id; `patient`, `encounter`, `previous`, `assessor`, `problem`, `investigation` (DiagnosticReport, RiskAssessment, FamilyMemberHistory), `finding-ref:Condition` and `supporting-info` (rebuilt types) chain; every parameter is sortable.
- RiskAssessment: `condition`, `date`, `encounter`, `identifier`, `method`, `patient`, `performer`, `probability`, `risk`, `subject`. R4 defines no `status` parameter for this resource. `date` is a dateTime range over `occurrenceDateTime` only (a Period occurrence is missing); `probability` is a `number` search over a decimal or a Range (`number_range_match`); `risk` reads `prediction.qualitativeRisk` of every prediction; `subject` and `performer` are multi-target (need a type); `patient`, `encounter`, `condition`, `subject:Patient` and `performer:Practitioner|PractitionerRole` chain; every parameter is sortable.
- FamilyMemberHistory: `code`, `date`, `identifier`, `instantiates-canonical`, `instantiates-uri`, `patient`, `relationship`, `sex`, `status`. `code` reads `condition.code` across every condition; `date` is a dateTime range; `relationship`, `sex` and `code` are tokens on CodeableConcepts; `instantiates-canonical` / `instantiates-uri` work as on Procedure; `patient` has one target (a bare id works) and chains; every parameter is sortable.
- ImmunizationEvaluation: `date`, `dose-status`, `identifier`, `immunization-event`, `patient`, `status`, `target-disease`. `date` is a dateTime range; `dose-status` and `target-disease` are tokens on CodeableConcepts; `status` is a plain code; `patient` and `immunization-event` have one target (a bare id works) and chain; every parameter is sortable.
- ImmunizationRecommendation: `date`, `identifier`, `information`, `patient`, `status`, `support`, `target-disease`, `vaccine-type`. `date` is a dateTime range; `status`, `target-disease` and `vaccine-type` are tokens on CodeableConcepts inside the `recommendation` backbone (any entry matches); `support` (Immunization | ImmunizationEvaluation) and `information` (Reference(Any)) need a type; `patient`, `support:Immunization` and `information:<rebuilt type>` chain; every parameter is sortable.
- Immunization: `date`, `identifier`, `location`, `lot-number`, `manufacturer`, `patient`, `performer`, `reaction`, `reaction-date`, `reason-code`, `reason-reference`, `series`, `status`, `status-reason`, `target-disease`, `vaccine-code`. `date` is a dateTime range over `occurrence[x]` (a string occurrence is missing); `lot-number` and `series` are strings; `target-disease` reads `protocolApplied.targetDisease`; `performer` and `reason-reference` are multi-target (need a type); `patient`, `location`, `manufacturer`, `performer:<Type>` and `reason-reference:Condition|DiagnosticReport` chain; every parameter is sortable.
- DiagnosticReport: `based-on`, `category`, `code`, `conclusion`, `date`, `encounter`, `identifier`, `issued`, `media`, `patient`, `performer`, `result`, `results-interpreter`, `specimen`, `status`, `subject`. `date` is a dateTime/Period range and `issued` a date on an instant; `conclusion` reads `conclusionCode`; `subject`, `performer`, `results-interpreter` and `based-on` are multi-target (need a type); `patient` is `subject` narrowed to Patients; `patient`, `encounter` and `performer|results-interpreter:<Type>` chain; every parameter is sortable.
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

number, uri and composite (**quantity, number, uri and composite are all done now** — composite is `app/fhir/search/composite.py` plus a resource-side builder, first used by Observation; **quantity is done** — Encounter `length`, `app/fhir/search/quantity.py`: `[prefix]number[|system|code]`,
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
  Location, HealthcareService and Endpoint respectively), `Schedule:actor` (on Practitioner, PractitionerRole, HealthcareService and Location), `Slot:schedule` (on Schedule), `Patient:general-practitioner` (on Practitioner, PractitionerRole and Organization), `Patient:organization` (on Organization) `Patient:link` (on Patient), `Appointment:actor|patient|practitioner|location` (on Patient, Practitioner, PractitionerRole, HealthcareService and Location) `Appointment:slot` (on Slot), `AppointmentResponse:appointment` (on Appointment) and `AppointmentResponse:actor|patient|practitioner|location` (on Patient, Practitioner, PractitionerRole, HealthcareService and Location), plus `Encounter:patient|subject` (on Patient), `Encounter:participant|practitioner` (on Practitioner; `participant` also on PractitionerRole), `Encounter:location` (on Location), `Encounter:appointment` (on Appointment), `Encounter:service-provider` (on Organization) and `Encounter:part-of` (on Encounter), plus `RelatedPerson:patient` (on Patient) and, on RelatedPerson, `Appointment:actor`, `AppointmentResponse:actor`, `Encounter:participant` and `Patient:link`, plus `AllergyIntolerance:patient` (on Patient) and `AllergyIntolerance:recorder|asserter` (on Patient, Practitioner, PractitionerRole and RelatedPerson), plus `Condition:subject|patient` (on Patient), `Condition:asserter` (on Patient, Practitioner, PractitionerRole and RelatedPerson), `Condition:encounter` (on Encounter), and, on Condition, `Encounter:diagnosis|reason-reference`, `Appointment:reason-reference` and `Procedure:reason-reference`; `Encounter:diagnosis|reason-reference` and `Appointment:reason-reference` also `_include` Conditions and Procedures; plus `Procedure:subject|patient` (on Patient), `Procedure:performer` (on Patient, Practitioner, PractitionerRole and RelatedPerson), `Procedure:encounter` (on Encounter), `Procedure:location` (on Location) and, on Procedure, `Encounter:diagnosis|reason-reference`, `Appointment:reason-reference`, `Procedure:part-of` and `Procedure:reason-reference`; plus `DiagnosticReport:subject|patient` (on Patient), `DiagnosticReport:subject` (on Location), `DiagnosticReport:encounter` (on Encounter), `DiagnosticReport:performer|results-interpreter` (on Practitioner and PractitionerRole) and, on DiagnosticReport, `Procedure:reason-reference`; plus `Immunization:patient` (on Patient), `Immunization:location` (on Location), `Immunization:performer` (on Practitioner and PractitionerRole) and `Immunization:reason-reference` (on Condition and DiagnosticReport); plus `ImmunizationRecommendation:patient` (on Patient) and `ImmunizationRecommendation:support` (on Immunization and ImmunizationEvaluation); plus `ImmunizationEvaluation:patient` (on Patient) and `ImmunizationEvaluation:immunization-event` (on Immunization); plus `FamilyMemberHistory:patient` (on Patient); and `RiskAssessment:subject|patient` (on Patient), `RiskAssessment:condition` (on Condition), `RiskAssessment:encounter` (on Encounter) and `RiskAssessment:performer` (on Practitioner and PractitionerRole); and `ClinicalImpression:subject|patient` (on Patient), `ClinicalImpression:encounter` (on Encounter), `ClinicalImpression:assessor` (on Practitioner and PractitionerRole), `ClinicalImpression:problem` (on Condition and AllergyIntolerance), `ClinicalImpression:investigation` (on DiagnosticReport, RiskAssessment and FamilyMemberHistory) and `ClinicalImpression:previous` (on itself); and `DetectedIssue:patient` (on Patient) and `DetectedIssue:author` (on Practitioner and PractitionerRole); and `Observation:subject|patient` (on Patient), `Observation:encounter` (on Encounter), `Observation:performer` (on Practitioner, PractitionerRole, Patient and RelatedPerson), `Observation:part-of` (on Procedure and Immunization) and `Observation:has-member|derived-from` (on itself).
- `_revinclude` from resources that point at Organization/Location (Observation, ...)
  becomes possible only when those resources are on the engine.

## 5. Suggested order after the resources exist

1. Registry for every resource (the bulk of the work; mechanical).
2. `CapabilityStatement` generated from the registries, so the server declares what it supports.
3. `_tag` / `_profile` / `_security` / `_source` (with the `meta` storage change).
4. `_has`.
5. number / uri / composite types, and UCUM unit conversion for quantity, as the clinical resources need them.
6. Later or never: `_text`, `_content`, `_filter`, `_list`, `_contained`, `_history`, system-wide search.

# FHIR Resource Status

The single record of which FHIR R4 resources are built on the current architecture, what each one serves, and what is still open. **Update it in the same commit as any change to a resource** (see [Keeping this file current](#keeping-this-file-current)).

_Last updated: 2026-11-21, after wiring Observation as a target (`fb0845e`)._

## Architecture in one line

Medplum-style: the whole FHIR R4 resource lives in one `content` JSONB column; only the elements a search parameter filters on are indexed into columns and child tables (derived from `content` on every write). One `SearchRegistry` per resource. FHIR R4 JSON in and out. Direct JWT/RBAC auth. One-way migrations. Details: `CLAUDE.md` ("Medplum-style storage") and `.claude/commands/new-fhir-resource.md`.

---

## 1. Rebuilt on the current architecture (25)

"Params" is the number of R4 search parameters served, excluding the common `_id` and `_lastUpdated` that every resource also has (read from each `SearchRegistry`).

| # | Resource | Route | Params | Sequence | Migration | Commit | Notes |
|---|---|---|---:|---|---|---|---|
| 1 | Organization | `/organizations` | 13 | 190000 | `5b1969c2ec19` | `19a2298` | `partOf` hierarchy (`:above`/`:below`), `endpoint`, chaining |
| 2 | Location | `/locations` | 15 | 230000 | `8c41d2e7a9b3` | `19a2298` | `near` search, `partOf` hierarchy |
| 3 | Practitioner | `/practitioners` | 17 | 30000 | `a7d3f19c2b64` | `b7eebe8` | `user_id` link (`PUT/DELETE /{id}/user`), `/me` |
| 4 | HealthcareService | `/healthcare-services` | 12 | 150000 | `c9f5b2d7e813` | `2afb7e0` | Shared `token` and `reference` index tables |
| 5 | Endpoint | `/endpoints` | 6 | 620000 | `d1a6c3e8f924` | `8ac745d` | New resource (not a rebuild) |
| 6 | PractitionerRole | `/practitioner-roles` | 13 | 140000 | `e2b7d4f9a035` | `0015133` | First Period (`date`) search |
| 7 | Schedule | `/schedules` | 7 | 200000 | `f3c8e5a1b947` | `ccd1b17` | First multi-target reference (`actor`) |
| 8 | Slot | `/slots` | 8 | 220000 | `g4d9f6b2c058` | `ccd1b17` | `schedule` chains into Schedule |
| 9 | Patient | `/patients` | 23 | 10000 | `h5e0a7c3d169` | `8d505e3` | `user_id` link, `/me`, `?link_me=true`; partial-date ranges |
| 10 | Appointment | `/appointments` | 17 | 40000 | `i6f1b8d4e27a` | `0c99fb8` | Participant table; multi-target `actor` |
| 11 | AppointmentResponse | `/appointment-responses` | 7 | 370000 | `j7a2c9e5f381` | `365a394` | |
| 12 | Encounter | `/encounters` | 23 | 20000 | `k8b3d0f6a492` | `39149b0` | First quantity search (`length`); bare-Coding `class` |
| 13 | RelatedPerson | `/related-persons` | 17 | 300000 | `l9c4e1a7b503` | `c28a146` | Route was `/related_persons`; now an existence-checked target everywhere |
| 25 | Observation | `/observations` | 38 | 160000 | `x1c6e3a9b705` | `0aaa272` | **the engine's first `composite` searches** (8, via a `slot` on the token and value tables) and the `combo-*` union parameters; `value-quantity` / `value-string` / `value-date` in one value table; a revinclude source on Patient, Encounter, Practitioner, PractitionerRole, RelatedPerson, Procedure, Immunization and itself |
| 24 | DetectedIssue | `/detected-issues` | 6 | 540000 | `w0b5d2f8a614` | `90ad106` | **no `status` / `severity` search (R4 defines none)**; `identified` reads a dateTime or a Period; `implicated` is Reference(Any) in a shared reference table; a revinclude source on Patient, Practitioner and PractitionerRole |
| 23 | ClinicalImpression | `/clinical-impressions` | 13 | 530000 | `v9a4c1e7f503` | `afaa8b1` | four repeating references (`problem`, `investigation`, `finding-ref`, `supporting-info` [Reference(Any)]) share one reference table; `finding-code` reads every finding; a revinclude source on Patient, Encounter, Practitioner, PractitionerRole, Condition, AllergyIntolerance, DiagnosticReport, RiskAssessment, FamilyMemberHistory and itself (`previous`); Condition `stage.assessment` now checks it |
| 22 | RiskAssessment | `/risk-assessments` | 10 | 520000 | `u8f3b0d6e492` | `ddbfe2e` | **no `status` search (R4 defines none)**; `probability` is the engine's first `number` search; `risk` reads every prediction; a revinclude source on Patient, Condition, Encounter, Practitioner and PractitionerRole |
| 21 | FamilyMemberHistory | `/family-member-histories` | 9 | 490000 | `t7e2a9c5d381` | `a39d710` | `code` reads every condition; `instantiates-canonical`/`-uri` as on Procedure; many choice types (born/age/deceased/onset) live only in `content`; a revinclude source on Patient |
| 20 | ImmunizationEvaluation | `/immunization-evaluations` | 7 | 610000 | `s6d1f8b4c270` | `d0b2cca` | smallest of the family; old reference-type enums held member names (`PATIENT`); now an existence-checked, chainable and includable `support` target of ImmunizationRecommendation, and a revinclude source on Patient and Immunization |
| 19 | ImmunizationRecommendation | `/immunization-recommendations` | 8 | 510000 | `r5c0e7a3b169` | `d8effae` | tokens read inside the `recommendation` backbone (any entry matches); `information` is Reference(Any); now a revinclude source on Patient and Immunization |
| 18 | Immunization | `/immunizations` | 16 | 330000 | `q4b9d6f2a058` | `96f929b` | `reaction`+`reaction-date` share one row; `occurrence[x]` indexed only as a dateTime; `performer` and `reason-reference` multi-target; now a revinclude source on Patient, Location, Practitioner, PractitionerRole, Condition and DiagnosticReport |
| 17 | DiagnosticReport | `/diagnostic-reports` | 16 | 110000 | `p3a8c5e1f947` | `c9c66ba` | `performer`/`results-interpreter` share one table; `issued` instant; `subject` over Patient/Group/Device/Location; now an existence-checked target of Procedure and Condition |
| 16 | Procedure | `/procedures` | 16 | 100000 | `o2f7b4d0e836` | `7ed4def` | First `uri` search (`instantiates-uri`); `instantiates-canonical` over canonical URLs; `subject`/`performer`/`part-of`/`reason-reference` multi-target; now an existence-checked target of Encounter and Appointment |
| 15 | Condition | `/conditions` | 21 | 120000 | `n1e6a3c9d725` | `fbd1eb8` | Quantity search over an Age or a Range (`quantity_range_match`); `subject`/`asserter`/`evidence-detail` multi-target; now an existence-checked target of Encounter and Appointment |
| 14 | AllergyIntolerance | `/allergy-intolerances` | 16 | 260000 | `m0d5f2b8c614` | `7d36dfc` | `recorder`/`asserter` multi-target over four rebuilt types; one shared token table for seven parameters; `onset` reads `reaction.onset` |

All 25 are mounted (`configs/config.yaml` → `routes.enabled`), have tests under `tests/integration/<resource>/` and a conformance file (`tests/conformance/test_<resource>_fhir.py`), appear in `GET /metadata`, and have a migration with no downgrade.

### What each resource existence-checks on write (relative `Type/<id>` → 422 if missing in the caller's org)

| Resource | Checked | Stored as sent |
|---|---|---|
| Organization | `partOf`, `endpoint`, `identifier.assigner` | absolute URLs, logical references |
| Location | `managingOrganization`, `partOf`, `endpoint`, `identifier.assigner` | absolute URLs, logical references |
| Practitioner | `identifier.assigner`, `qualification.issuer` | absolute URLs, logical references |
| HealthcareService | `providedBy`, `location`, `coverageArea`, `endpoint`, `identifier.assigner` | absolute URLs, logical references |
| Endpoint | `managingOrganization`, `identifier.assigner` | absolute URLs, logical references |
| PractitionerRole | `practitioner`, `organization`, `location`, `healthcareService`, `endpoint`, `identifier.assigner` | absolute URLs, logical references |
| Schedule | `actor` of Practitioner / PractitionerRole / HealthcareService / Location, `identifier.assigner` | **Patient, RelatedPerson, Device actors**, absolute URLs |
| Slot | `schedule`, `identifier.assigner` | absolute URLs, logical references |
| Patient | `managingOrganization`, `generalPractitioner`, `link.other` (Patient, RelatedPerson), `contact.organization`, `identifier.assigner` | absolute URLs, logical references |
| Appointment | `slot`, `participant.actor` (Patient, Practitioner, PractitionerRole, RelatedPerson, HealthcareService, Location), `reasonReference` (Condition, Procedure, Observation), `identifier.assigner` | Device actors; `basedOn`, `supportingInformation` and other `reasonReference` targets |
| AppointmentResponse | `appointment`, `actor` (same types as Appointment), `identifier.assigner` | Device actors |
| Encounter | `subject` (Patient), `partOf`, `serviceProvider`, `appointment`, `participant.individual` (Practitioner, PractitionerRole, RelatedPerson), `location.location`, `hospitalization.origin/destination`, `diagnosis.condition` and `reasonReference` (Condition, Procedure; a `reasonReference` may also be an Observation), `identifier.assigner` | Group subjects, Account, EpisodeOfCare, ServiceRequest targets |
| RelatedPerson | `patient`, `identifier.assigner` | absolute URLs, logical references |
| Observation | `subject` (Patient, Location), `encounter`, `basedOn` (ImmunizationRecommendation), `partOf` (Procedure, Immunization), `performer` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `hasMember` and `derivedFrom` (Observation), `note.authorReference`, `identifier.assigner` | Group / Device subject, Specimen, Device, `focus` (Reference(Any)), MedicationRequest / ServiceRequest / CarePlan basedOn, CareTeam, QuestionnaireResponse / Media / ImagingStudy / DocumentReference targets, absolute URLs, logical references |
| DetectedIssue | `patient`, `author` (Practitioner, PractitionerRole), `mitigation.author` (Practitioner, PractitionerRole), `implicated` and `evidence.detail` (any rebuilt resource), `identifier.assigner` | Device author, MedicationRequest / MedicationDispense / Observation and other not-rebuilt `implicated` / `evidence.detail` targets, absolute URLs, logical references |
| ClinicalImpression | `subject` (Patient), `encounter`, `assessor` (Practitioner, PractitionerRole), `previous`, `problem` (Condition, AllergyIntolerance), `investigation.item` (Observation, RiskAssessment, FamilyMemberHistory, DiagnosticReport), `finding.itemReference` (Condition, Observation), `prognosisReference` (RiskAssessment), `supportingInfo` (any rebuilt resource), `note.authorReference`, `identifier.assigner` | Group subject, Media / ImagingStudy / QuestionnaireResponse investigations, Media findings, absolute URLs, logical references |
| RiskAssessment | `subject` (Patient), `encounter`, `condition`, `performer` (Practitioner, PractitionerRole), `reasonReference` (Condition, Observation, DiagnosticReport), `note.authorReference`, `identifier.assigner` | Group subject, Device performer, `basedOn` / `parent` / `basis` (Reference(Any)), DocumentReference reasons, absolute URLs, logical references |
| FamilyMemberHistory | `patient`, `reasonReference` (Condition, AllergyIntolerance, Observation, DiagnosticReport), `note.authorReference` (both the resource's and each condition's: Practitioner, PractitionerRole, Patient, RelatedPerson, Organization), `identifier.assigner` | QuestionnaireResponse / DocumentReference reasons, absolute URLs, logical references |
| ImmunizationEvaluation | `patient`, `immunizationEvent` (Immunization), `authority` (Organization), `identifier.assigner` | absolute URLs, logical references |
| ImmunizationRecommendation | `patient`, `authority`, `supportingImmunization` (Immunization, ImmunizationEvaluation), `supportingPatientInformation` (Patient, Practitioner, PractitionerRole, RelatedPerson, Organization, Location, Encounter, Appointment, Condition, Procedure, DiagnosticReport, AllergyIntolerance, Immunization), `identifier.assigner` | Observation targets, absolute URLs, logical references |
| Immunization | `patient`, `encounter`, `location`, `manufacturer`, `performer.actor` (Practitioner, PractitionerRole, Organization), `reasonReference` (Condition, Observation, DiagnosticReport), `reaction.detail` (Observation), `protocolApplied.authority`, `note` `authorReference`, `identifier.assigner` | absolute URLs, logical references |
| DiagnosticReport | `subject` (Patient or Location), `encounter`, `performer` and `resultsInterpreter` (Practitioner, PractitionerRole, Organization), `result` (Observation), `identifier.assigner` | Group/Device subject, CareTeam, `basedOn`, `specimen`, `imagingStudy`, `media.link`, absolute URLs, logical references |
| Procedure | `subject` (Patient), `encounter`, `location`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `performer.actor` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `performer.onBehalfOf`, `partOf` (Procedure), `reasonReference` (Condition, Procedure, DiagnosticReport, Observation), `report` (DiagnosticReport), `complicationDetail` (Condition), `note` `authorReference`, `identifier.assigner` | Group subject, Device performer, `basedOn`, `usedReference`, DocumentReference targets, absolute URLs, logical references |
| Condition | `subject` (Patient), `encounter`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `note` `authorReference` (Practitioner, Patient, RelatedPerson, Organization), `stage.assessment` (DiagnosticReport, ClinicalImpression, Observation), `identifier.assigner` | Group subject, `evidence.detail`, absolute URLs, logical references |
| AllergyIntolerance | `patient`, `encounter`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `note` / `reaction.note` `authorReference` (Practitioner, Patient, RelatedPerson, Organization), `identifier.assigner` | absolute URLs, logical references |

---

## 2. Not yet rebuilt (24)

Still on the old fully-normalized model and **not mounted** (commented out in `routes.enabled`). Each becomes a rebuild when it is picked up.

| Group | Resources |
|---|---|
| Orders and medication | ServiceRequest, MedicationRequest, MedicationStatement, MedicationAdministration, MedicationDispense, MedicationKnowledge |
| Care planning | CarePlan, CareTeam, EpisodeOfCare, Goal, Consent, Group |
| Communication | Communication, CommunicationRequest |
| Documents and specimens | DocumentReference, Specimen, SpecimenDefinition |
| Definitions and measures | ActivityDefinition, PlanDefinition, ObservationDefinition, Measure, MeasureReport |
| Forms | Questionnaire, QuestionnaireResponse |

Brand-new resources outside this list (like Endpoint was) can be added at any time; record them in section 1 when built, with a note that they are new rather than rebuilt.

Suggested next: any of the resources in the list above; **ServiceRequest** and **MedicationRequest** are the ones Observation can point at (`basedOn`).

---

## 3. Open items and known gaps

| Item | Detail | Where |
|---|---|---|
| Schedule `actor` | Patient and RelatedPerson actors are stored as sent: Schedule does not model them yet | Schedule |
| Encounter references | Group, Account, EpisodeOfCare, ServiceRequest, Observation and similar targets are stored as sent until those resources are rebuilt | Encounter, Appointment |
| Organization revinclude | `_revinclude=Procedure:performer`, `DiagnosticReport:performer|results-interpreter` and `Immunization:manufacturer|performer` are not declared on Organization yet (the Organization registry file has uncommitted unrelated edits) | Organization |
| Appointment operations | `$find` / `$book` not built; to be decided after reading the Medplum scheduling docs | Appointment |
| fhir-gql | The GraphQL half (types, translators for **both** connectors, queries and mutations) is deferred until every fhir-server resource is done | `D:\code\work\projects\fhir-gql` |
| Common search parameters | `_tag`, `_profile`, `_security`, `_source`, `_text`, `_content`, `_list`, `_has`, `_type`, `_filter` are ignored (reported in an `outcome` entry) | `docs/search-architecture/pending-search-capabilities.md` |
| ClinicalImpression references | No `:supporting-info` / `:finding-ref` revinclude; Condition `evidence-detail` does not chain to or include a ClinicalImpression (its modeled-type list is narrower than the rebuilt set) | ClinicalImpression, Condition |
| DetectedIssue references | No `:implicated` revinclude (a DetectedIssue cannot be found from the resources it implicates); Condition `evidence-detail` does not chain to or include a DetectedIssue | DetectedIssue |
| Observation as a target | Done for every element that names an Observation as an R4 target (existence check, chaining, `_include`, and the `_revinclude` on Observation). Left as sent: `Condition.evidence.detail` and `RiskAssessment.basis` (Reference(Any) elements outside the modeled-type lists), plus no `:supporting-info` / `:implicated` / `:information` revinclude | Condition, RiskAssessment |
| Observation search | `SampledData` is not indexed for `value-quantity`; `value-string` has no `:exact`; `Observation:performer` is not declared on Organization (uncommitted edits in its registry file); a Timing `effective[x]` is indexed as the range from its earliest event to its latest | Observation |
| Cardinality minimums | R4 required elements (e.g. `status`, `participant`) are enforced only by the `java_validator` backend, not the native one | all resources |
| Test-suite collection | `pytest tests` as a whole fails at collection (pre-existing); run per directory | tests |

---

## 4. Engine capabilities (what a new resource can reuse)

| Capability | Introduced with | Module |
|---|---|---|
| string / token / reference / date, `:missing`, `_sort`, `_include`, `_revinclude`, chaining, hierarchy | Organization | `app/fhir/search/` |
| `near` | Location | `app/repository/location/search.py` |
| Period search (`period_match`) | PractitionerRole | `app/fhir/search/sql.py` |
| Multi-target reference | Schedule | `app/fhir/search/` |
| Partial-date range (`period_bounds`) | Patient | `app/repository/_content_index.py` |
| Quantity search (`quantity_match`) | Encounter | `app/fhir/search/quantity.py` |
| Quantity search over an Age or a Range (`quantity_range_match`) | Condition | `app/fhir/search/quantity.py` |
| `uri` search (`uri_match`: exact, `:below`, `:above`) | Procedure | `app/fhir/search/sql.py` |
| `number` search over a decimal or a Range (`number_range_match`) | RiskAssessment | `app/fhir/search/quantity.py` |
| `composite` search (`split_composite`; a resource-side `$` builder pairing a code row and a value row of the same element, `slot`) and the `combo-*` union parameters | Observation | `app/fhir/search/composite.py` |

---

## Keeping this file current

Update this file **in the same commit** whenever you:

- **rebuild or add a resource**: add its row to section 1 (route, params, sequence, migration revision, commit hash once known), remove it from section 2, and fill its row in the existence-check table;
- **wire one resource to another** (a new existence check, include or chain): edit the affected rows' "Checked" and "Stored as sent" cells, and close the matching item in section 3;
- **add an engine capability** (a new search type, modifier or helper): add a row to section 4 and, if it closes a gap, remove it from section 3;
- **find or close a known gap**: edit section 3;
- **change the route prefix, sequence block or parameter count** of a resource.

Then bump the "Last updated" line. Verify the parameter count with:

```bash
uv run python -c "from app.fhir.capability import SEARCH_REGISTRIES as R; print({k: len(list(f().params.values())) - 2 for k, f in R.items()})"
```
(each registry includes `_id` and `_lastUpdated`, hence the `- 2`), and the mounted list with `configs/config.yaml` → `routes.enabled`.

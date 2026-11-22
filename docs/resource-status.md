# FHIR Resource Status

The single record of which FHIR R4 resources are built on the current architecture, what each one serves, and what is still open. **Update it in the same commit as any change to a resource** (see [Keeping this file current](#keeping-this-file-current)).

_Last updated: 2026-11-22, after rebuilding CarePlan._

## Architecture in one line

Medplum-style: the whole FHIR R4 resource lives in one `content` JSONB column; only the elements a search parameter filters on are indexed into columns and child tables (derived from `content` on every write). One `SearchRegistry` per resource. FHIR R4 JSON in and out. Direct JWT/RBAC auth. One-way migrations. Details: `CLAUDE.md` ("Medplum-style storage") and `.claude/commands/new-fhir-resource.md`.

---

## 1. Rebuilt on the current architecture (32)

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
| 26 | Specimen | `/specimens` | 12 | 310000 | `y2d7f4b0c816` | `1a463d5` | `collected` reads a dateTime or a Period; `container-id` and `container` read every container; `parent` is a self-reference (`Specimen:parent` chains and includes); `subject` / `collector` are multi-target; a revinclude source on Patient, Location, Practitioner, PractitionerRole, Observation (`:specimen`) and DiagnosticReport (`:specimen`); **the target of `Observation.specimen` and `DiagnosticReport.specimen`** |
| 27 | ServiceRequest | `/service-requests` | 21 | 80000 | `z3e8a5c1d927` | `f4434ce` | `status`, `intent` and `priority` are Enum columns holding the real FHIR codes (`original-order`, `on-hold`); `occurrence` reads a dateTime, a Period or a **Timing**; `performer`, `requester`, `subject` and `based-on` are multi-target; `requisition` is a token on columns; a revinclude source on Patient, Location, Practitioner, PractitionerRole, RelatedPerson, Organization, HealthcareService, Encounter and Specimen; **the target of `basedOn` on Observation, DiagnosticReport, Procedure, Encounter and Appointment, and of `Specimen.request`** |
| 28 | Medication | `/medications` | 9 | 250000 | `a4f9b6d2e038` | `8c513bc` | `expiration-date` reads `batch.expirationDate` as the range the dateTime covers; `lot-number` is a token over a string (code only, no system); `ingredient-code` reads the `itemCodeableConcept` of *every* ingredient; `ingredient` is a Substance | Medication reference table (`Medication:ingredient` chains, includes and reverse-includes on itself); `manufacturer` is a column reference with a `Medication:manufacturer` revinclude on Organization; the `medication_status` enum already held the real codes, so it stays; **a Medication in a Reference(Any) is now existence-checked** (ClinicalImpression, DetectedIssue, ImmunizationRecommendation, ServiceRequest) |
| 29 | MedicationRequest | `/medication-requests` | 16 | 90000 | `b5a0c7e3f149` | `7270717` | `status`, `intent` and `priority` are Enum columns holding the real FHIR codes (`on-hold`, `original-order`); `date` reads the `timing.event` dateTimes of **every dosage instruction** (a timing table, one row per event); `code` reads `medicationCodeableConcept` while `medication` reads `medicationReference` (columns); `intended-performer` (7 types), `intended-dispenser`, `requester`, `subject` are column references; a revinclude source on Patient, Encounter, Practitioner, PractitionerRole, RelatedPerson, Organization and Medication; **the target of `basedOn` on ServiceRequest, Observation and DiagnosticReport**, and of Reference(Any) in ClinicalImpression, DetectedIssue, ImmunizationRecommendation and ServiceRequest |
| 30 | Group | `/groups` | 10 | 430000 | `c6b1d8f4a250` | `a4be7b5` | **the `characteristic-value` composite** (a characteristic code and a value of the *same* characteristic, paired on the token table's `slot`, like Observation's); `actual` is a boolean column, `exclude` and the boolean `value` are `true` / `false` token rows; `value` reads a CodeableConcept or a boolean only; `member` (7 types, one row per member) and `managing-entity` (4 types) are multi-target; the `group_type` enum already held the real codes; a revinclude source on Patient, Practitioner, PractitionerRole, Medication, Organization, RelatedPerson and itself; **a Group in a Reference(Any) is now existence-checked** (ClinicalImpression, DetectedIssue, ImmunizationRecommendation, ServiceRequest, MedicationRequest) |
| 31 | CareTeam | `/care-teams` | 8 | 390000 | `d7c2e9a5b361` | `0cdb111` | `date` is a Period search over `period` (`period_match`); `status` enum recreated with the real FHIR codes (`entered-in-error`); `category` in a shared token table; `participant` (6 types incl. CareTeam itself) held one row per `participant.member` in its own table; `subject` (Patient | Group) is multi-target and `patient` is `subject` narrowed to Patients; **the first resource to follow a Group `subject`** (existence-checked, `subject:Group.` chains, `_include=CareTeam:subject:Group`, `Group?_revinclude=CareTeam:subject`); revinclude sources on Patient, Group, Encounter, Practitioner, PractitionerRole, RelatedPerson, Organization and itself; **a CareTeam in a Reference(Any) is now existence-checked** (ClinicalImpression, DetectedIssue, ImmunizationRecommendation, ServiceRequest, MedicationRequest, Group `characteristic.valueReference`) |
| 32 | CarePlan | `/care-plans` | 20 | 290000 | `e8d3f0b6c472` | `ab9d1f3` | the largest rebuild so far: `status` / `intent` enums recreated with the real FHIR codes; `date` is a Period search over `period`; **`activity-date` reads `activity.detail.scheduled[x]` of every activity** (a Period, or a Timing from its earliest to its latest event, in an activity table with `activity-reference`); `activity-code` and `category` in a shared token table; `based-on` / `replaces` / `part-of` / `care-team` / `condition` / `goal` / `instantiates-canonical` in a shared reference table (single targets, so a bare id works); `instantiates-uri` a `uri` search; `performer` (8 types, `activity.detail.performer` of every activity) and `activity-reference` (9 types) are multi-target; `subject` (Patient | Group) multi-target with `patient` narrowed to Patients and **a Group subject followed, like CareTeam**; revinclude sources on Patient, Group, Encounter, CareTeam, Condition, Practitioner, PractitionerRole, Organization, RelatedPerson, HealthcareService, Appointment, MedicationRequest, ServiceRequest and itself; **a CarePlan in a Reference(Any) is now existence-checked** (ClinicalImpression, DetectedIssue, ImmunizationRecommendation, ServiceRequest, MedicationRequest, Group, and CarePlan's own `supportingInfo`) |
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
| Appointment | `slot`, `basedOn` (ServiceRequest), `participant.actor` (Patient, Practitioner, PractitionerRole, RelatedPerson, HealthcareService, Location), `reasonReference` (Condition, Procedure, Observation), `identifier.assigner` | Device actors; CarePlan `basedOn`, `supportingInformation` and other `reasonReference` targets |
| AppointmentResponse | `appointment`, `actor` (same types as Appointment), `identifier.assigner` | Device actors |
| Encounter | `subject` (Patient), `basedOn` (ServiceRequest), `partOf`, `serviceProvider`, `appointment`, `participant.individual` (Practitioner, PractitionerRole, RelatedPerson), `location.location`, `hospitalization.origin/destination`, `diagnosis.condition` and `reasonReference` (Condition, Procedure; a `reasonReference` may also be an Observation), `identifier.assigner` | Group subjects, Account, EpisodeOfCare, CarePlan targets |
| RelatedPerson | `patient`, `identifier.assigner` | absolute URLs, logical references |
| Observation | `subject` (Patient, Location), `encounter`, `specimen`, `basedOn` (ImmunizationRecommendation, ServiceRequest, MedicationRequest), `partOf` (Procedure, Immunization), `performer` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `hasMember` and `derivedFrom` (Observation), `note.authorReference`, `identifier.assigner` | Group / Device subject, Device, `focus` (Reference(Any)), CarePlan basedOn, CareTeam, QuestionnaireResponse / Media / ImagingStudy / DocumentReference targets, absolute URLs, logical references |
| DetectedIssue | `patient`, `author` (Practitioner, PractitionerRole), `mitigation.author` (Practitioner, PractitionerRole), `implicated` and `evidence.detail` (any rebuilt resource), `identifier.assigner` | Device author, MedicationRequest / MedicationDispense / Observation and other not-rebuilt `implicated` / `evidence.detail` targets, absolute URLs, logical references |
| ClinicalImpression | `subject` (Patient), `encounter`, `assessor` (Practitioner, PractitionerRole), `previous`, `problem` (Condition, AllergyIntolerance), `investigation.item` (Observation, RiskAssessment, FamilyMemberHistory, DiagnosticReport), `finding.itemReference` (Condition, Observation), `prognosisReference` (RiskAssessment), `supportingInfo` (any rebuilt resource), `note.authorReference`, `identifier.assigner` | Group subject, Media / ImagingStudy / QuestionnaireResponse investigations, Media findings, absolute URLs, logical references |
| RiskAssessment | `subject` (Patient), `encounter`, `condition`, `performer` (Practitioner, PractitionerRole), `reasonReference` (Condition, Observation, DiagnosticReport), `note.authorReference`, `identifier.assigner` | Group subject, Device performer, `basedOn` / `parent` / `basis` (Reference(Any)), DocumentReference reasons, absolute URLs, logical references |
| FamilyMemberHistory | `patient`, `reasonReference` (Condition, AllergyIntolerance, Observation, DiagnosticReport), `note.authorReference` (both the resource's and each condition's: Practitioner, PractitionerRole, Patient, RelatedPerson, Organization), `identifier.assigner` | QuestionnaireResponse / DocumentReference reasons, absolute URLs, logical references |
| ImmunizationEvaluation | `patient`, `immunizationEvent` (Immunization), `authority` (Organization), `identifier.assigner` | absolute URLs, logical references |
| ImmunizationRecommendation | `patient`, `authority`, `supportingImmunization` (Immunization, ImmunizationEvaluation), `supportingPatientInformation` (Patient, Practitioner, PractitionerRole, RelatedPerson, Organization, Location, Encounter, Appointment, Condition, Procedure, DiagnosticReport, AllergyIntolerance, Immunization), `identifier.assigner` | Observation targets, absolute URLs, logical references |
| Immunization | `patient`, `encounter`, `location`, `manufacturer`, `performer.actor` (Practitioner, PractitionerRole, Organization), `reasonReference` (Condition, Observation, DiagnosticReport), `reaction.detail` (Observation), `protocolApplied.authority`, `note` `authorReference`, `identifier.assigner` | absolute URLs, logical references |
| DiagnosticReport | `subject` (Patient or Location), `encounter`, `performer` and `resultsInterpreter` (Practitioner, PractitionerRole, Organization), `result` (Observation), `specimen` (Specimen), `basedOn` (ServiceRequest, MedicationRequest), `identifier.assigner` | Group/Device subject, CareTeam, CarePlan `basedOn`, `imagingStudy`, `media.link`, absolute URLs, logical references |
| Specimen | `subject` (Patient or Location), `collection.collector` (Practitioner, PractitionerRole), `parent` (Specimen), `request` (ServiceRequest), `note.authorReference` (Practitioner, PractitionerRole, Patient, RelatedPerson), every `identifier` / `accessionIdentifier` / `container.identifier` `assigner` | Group / Device / Substance subject, `processing.additive`, `container.additiveReference`, absolute URLs, logical references |
| ServiceRequest | `subject` (Patient, Location), `encounter`, `requester` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `performer` (Practitioner, PractitionerRole, Organization, HealthcareService, Patient, RelatedPerson), `basedOn` and `replaces` (ServiceRequest), `specimen`, `locationReference`, `reasonReference` (Condition, Observation, DiagnosticReport), `supportingInfo` (any rebuilt resource), `note.authorReference`, every `identifier` / `requisition` `assigner` | Group / Device subject, Device requester, CareTeam / Device performer, CarePlan `basedOn`, DocumentReference reasons, `insurance`, `relevantHistory`, absolute URLs, logical references |
| Medication | `manufacturer` (Organization), `ingredient.itemReference` (a Medication), every `identifier` `assigner` | Substance ingredients, absolute URLs, logical references |
| MedicationRequest | `subject` (Patient), `encounter`, `requester` / `performer` / `reportedReference` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `recorder` (Practitioner, PractitionerRole), `medicationReference` (Medication), `dispenseRequest.performer` (Organization), `basedOn` (MedicationRequest, ServiceRequest, ImmunizationRecommendation), `priorPrescription` (MedicationRequest), `reasonReference` (Condition, Observation), `detectedIssue`, `supportingInformation` (any rebuilt resource), `note.authorReference`, every `identifier` / `groupIdentifier` `assigner` | Group subject, Device requester / performer, CareTeam performer, CarePlan `basedOn`, `insurance`, `eventHistory`, absolute URLs, logical references |
| Group | `managingEntity` (Organization, RelatedPerson, Practitioner, PractitionerRole), `member.entity` (Patient, Practitioner, PractitionerRole, Medication, Group), `characteristic.valueReference` (any rebuilt resource), every `identifier` `assigner` | Device and Substance members, absolute URLs, logical references |
| CareTeam | `subject` (Patient, Group), `encounter`, every `participant.member` (Practitioner, PractitionerRole, RelatedPerson, Patient, Organization, CareTeam) and `participant.onBehalfOf` (Organization), `reasonReference` (Condition), every `managingOrganization`, note `authorReference`, every `identifier` `assigner` | absolute URLs, logical references |
| CarePlan | `subject` (Patient, Group), `encounter`, `basedOn` / `replaces` / `partOf` (CarePlan), `author` / `contributor` (Patient, Practitioner, PractitionerRole, RelatedPerson, Organization, CareTeam), `careTeam`, `addresses` (Condition), `supportingInfo` and `activity.outcomeReference` (any rebuilt resource), `activity.reference` (Appointment, MedicationRequest, ServiceRequest), activity detail `reasonReference` (Condition, Observation, DiagnosticReport) / `location` / `performer` (7 types) / `productReference` (Medication), note and progress `authorReference`, every `identifier` `assigner` | Goal, Device, Substance, CommunicationRequest / Task / DeviceRequest / NutritionOrder / VisionPrescription / RequestGroup activities, DocumentReference reasons, absolute URLs, logical references |
| Procedure | `subject` (Patient), `basedOn` (ServiceRequest), `encounter`, `location`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `performer.actor` (Practitioner, PractitionerRole, Organization, Patient, RelatedPerson), `performer.onBehalfOf`, `partOf` (Procedure), `reasonReference` (Condition, Procedure, DiagnosticReport, Observation), `report` (DiagnosticReport), `complicationDetail` (Condition), `note` `authorReference`, `identifier.assigner` | Group subject, Device performer, CarePlan `basedOn`, `usedReference`, DocumentReference targets, absolute URLs, logical references |
| Condition | `subject` (Patient), `encounter`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `note` `authorReference` (Practitioner, Patient, RelatedPerson, Organization), `stage.assessment` (DiagnosticReport, ClinicalImpression, Observation), `identifier.assigner` | Group subject, `evidence.detail`, absolute URLs, logical references |
| AllergyIntolerance | `patient`, `encounter`, `recorder` and `asserter` (Practitioner, PractitionerRole, Patient, RelatedPerson), `note` / `reaction.note` `authorReference` (Practitioner, Patient, RelatedPerson, Organization), `identifier.assigner` | absolute URLs, logical references |

---

## 2. Not yet rebuilt (20)

Still on the old fully-normalized model and **not mounted** (commented out in `routes.enabled`). Each becomes a rebuild when it is picked up.

| Group | Resources |
|---|---|
| Orders and medication | MedicationStatement, MedicationAdministration, MedicationDispense, MedicationKnowledge |
| Care planning | EpisodeOfCare, Goal, Task, Flag, Consent |
| Communication | Communication, CommunicationRequest |
| Documents and specimens | DocumentReference, SpecimenDefinition |
| Definitions and measures | ActivityDefinition, PlanDefinition, ObservationDefinition, Measure, MeasureReport |
| Forms | Questionnaire, QuestionnaireResponse |

Brand-new resources outside this list (like Endpoint was) can be added at any time; record them in section 1 when built, with a note that they are new rather than rebuilt.

Suggested next: any of the resources in the list above; **MedicationStatement**, **MedicationAdministration** and **MedicationDispense** can now point at a rebuilt Medication and MedicationRequest (`medication[x]`, `request`, `authorizingPrescription`).

---

## 3. Open items and known gaps

| Item | Detail | Where |
|---|---|---|
| Schedule `actor` | Patient and RelatedPerson actors are stored as sent: Schedule does not model them yet | Schedule |
| Encounter references | Group, Account, EpisodeOfCare and similar targets are stored as sent until those resources are rebuilt | Encounter, Appointment |
| Organization revinclude | `_revinclude=Procedure:performer`, `DiagnosticReport:performer|results-interpreter` and `Immunization:manufacturer|performer` are not declared on Organization yet (the Organization registry file has uncommitted unrelated edits) | Organization |
| Appointment operations | `$find` / `$book` not built; to be decided after reading the Medplum scheduling docs | Appointment |
| fhir-gql | The GraphQL half (types, translators for **both** connectors, queries and mutations) is deferred until every fhir-server resource is done | `D:\code\work\projects\fhir-gql` |
| Common search parameters | `_tag`, `_profile`, `_security`, `_source`, `_text`, `_content`, `_list`, `_has`, `_type`, `_filter` are ignored (reported in an `outcome` entry) | `docs/search-architecture/pending-search-capabilities.md` |
| ClinicalImpression references | No `:supporting-info` / `:finding-ref` revinclude; Condition `evidence-detail` does not chain to or include a ClinicalImpression (its modeled-type list is narrower than the rebuilt set) | ClinicalImpression, Condition |
| DetectedIssue references | No `:implicated` revinclude (a DetectedIssue cannot be found from the resources it implicates); Condition `evidence-detail` does not chain to or include a DetectedIssue | DetectedIssue |
| Observation as a target | Done for every element that names an Observation as an R4 target (existence check, chaining, `_include`, and the `_revinclude` on Observation). Left as sent: `Condition.evidence.detail` and `RiskAssessment.basis` (Reference(Any) elements outside the modeled-type lists), plus no `:supporting-info` / `:implicated` / `:information` revinclude | Condition, RiskAssessment |
| Observation search | `SampledData` is not indexed for `value-quantity`; `value-string` has no `:exact`; `Observation:performer` is not declared on Organization (uncommitted edits in its registry file); a Timing `effective[x]` is indexed as the range from its earliest event to its latest | Observation |
| Specimen references | `processing.additive` and `container.additiveReference` (Substance) are stored as sent; there is no `:request` search parameter on Specimen; `Specimen:subject` does not include a Group / Device / Substance (not resources here) | Specimen |
| ServiceRequest references | CarePlan `basedOn`, CareTeam / Device performers, DocumentReference reasons, `insurance` (Coverage / ClaimResponse) and `relevantHistory` (Provenance) are stored as sent until those resources are rebuilt; no `Appointment:based-on` revinclude on ServiceRequest (an appointment cannot be found from the request it fulfils), and no `:supporting-info` revinclude; rule prr-1 (`orderDetail` only with a `code`) is only enforced by the `java_validator` backend; `RiskAssessment.basedOn` (Reference(Any)) still stores a ServiceRequest as sent | ServiceRequest |
| Medication references | A Substance ingredient is stored as sent (Substance is not rebuilt); nothing rebuilt references a Medication yet apart from the Reference(Any) lists, so there is no `medication` chain or revinclude from MedicationRequest / MedicationStatement / MedicationAdministration / MedicationDispense until those are rebuilt | Medication |
| MedicationRequest references | CarePlan `basedOn`, Group subjects, Device / CareTeam requesters and performers, `insurance` and `eventHistory` are stored as sent until those resources are rebuilt; `MedicationRequest:based-on`, `:prior-prescription` and `:detected-issue` are not search parameters, so a MedicationRequest cannot be found from what it is based on; `MedicationRequest.medication[x]` does not yet appear in any rebuilt resource's chain except through `medication`; rule-level R4 minimums (`status`, `intent`, `medication[x]`, `subject`) are enforced by the native validator's required-properties check, not by the database | MedicationRequest |
| Group as a subject | **A `Group/<id>` used as a `subject` is still stored as sent** (Encounter, Condition, Procedure, Observation, DiagnosticReport, Specimen, RiskAssessment, ClinicalImpression, ServiceRequest, MedicationRequest), so those searches do not chain through `subject:Group.` and there is no `Group` `_include` / `_revinclude` from them; Group is existence-checked only in Reference(Any) elements and in `Group.member` | all of those |
| CareTeam as a target | **A `CareTeam/<id>` as a performer or requester is still stored as sent**: DiagnosticReport `performer` / `resultsInterpreter`, Observation `performer`, ServiceRequest `performer`, MedicationRequest `requester` / `performer` (CareTeam is existence-checked only in Reference(Any) elements and `CareTeam.participant.member`), so those searches do not chain through `performer:CareTeam.` and there is no `CareTeam` `_include` / `_revinclude` from them | DiagnosticReport, Observation, ServiceRequest, MedicationRequest |
| CareTeam search | R4 defines no `name` search parameter, so `?name=` is an unknown parameter; rule ctm-1 (`participant.onBehalfOf` only when the member is a Practitioner) is only enforced by the `java_validator` backend; EpisodeOfCare, which references a CareTeam, is not rebuilt yet | CareTeam |
| CarePlan as a target | **A `CarePlan/<id>` in `basedOn` is still stored as sent** in Observation, DiagnosticReport, Procedure, ServiceRequest, MedicationRequest, Encounter and Appointment (CarePlan is existence-checked only in Reference(Any) elements and in its own `basedOn` / `replaces` / `partOf`), so `based-on:CarePlan.` does not chain there and there is no `CarePlan` `_include` / `_revinclude` from them | those seven resources |
| CarePlan search | `goal` is searchable but Goal is not a resource, so it does not chain; `activity.detail.goal`, `activity.detail.reasonCode`, `activity.detail.statusReason`, `activity.progress`, `activity.outcome*` and `activity.detail.product[x]` / `dailyAmount` / `quantity` live only in `content`; R4's `status` / `intent` / `subject` minimums, `activity.detail.status` and rule cpl-3 (an activity has a `reference` or a `detail`, not both) are only enforced by the `java_validator` backend; EpisodeOfCare, Goal and Task, which CarePlan references, are not rebuilt yet | CarePlan |
| Group search | `value` does not read a Quantity, Range or Reference characteristic value (R4's own expression only covers CodeableConcept and boolean); a `Group.characteristic` with no value is not paired by the composite; rule grp-1 (`member` only if `actual`) and `member` entities that disagree with `type` are only enforced by the `java_validator` backend | Group |
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

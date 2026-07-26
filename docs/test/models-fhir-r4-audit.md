# FHIR R4 Model Audit — `app/models/`

**Scope:** All 35 resource packages under `app/models/` (36 directories incl. `terminology`, which is not a FHIR resource). Each package was checked against (a) the canonical FHIR R4 specification (`https://www.hl7.org/fhir/R4/*.html`) for element completeness, cardinality, and datatype fidelity, and (b) this repository's own conventions as documented in `CLAUDE.md` (standard columns, public/internal ID separation, shared enum types, FK/eager-load rules, `__init__.py` re-export pattern).

**Method:** Six parallel audits (6 resources each), followed by manual spot-verification of every finding tagged CRITICAL below via direct file reads and repo-wide greps. All CRITICAL findings in this report have been independently confirmed against the actual source.

**Overall verdict:** The majority of resources (24 of 35) are solid — complete against R4, internally consistent, and correctly wired. But there are two genuine **spec-version regressions** (whole resources built against FHIR R5 instead of R4), one **functional data-integrity bug** (a reference column storing the wrong kind of ID), one **live migration hazard** (a duplicated Postgres enum type), and one **systemic, repo-wide gap** (reference columns routinely missing the FK/index/eager-load treatment the project's own rules require). None of these are stylistic nitpicks — each has a concrete failure mode described inline.

---

## 1. Critical findings (fix first)

### 1.1 `Encounter` is modeled against FHIR **R5**, not R4
`app/models/encounter/encounter.py` and `enums.py` are self-documented as R5 throughout (`"R5 value set"`, `"R5 renamed from period"`, `"R5 new"` appear over a dozen times). Concretely, against the R4 spec:

- `status` (enums.py:4-15) uses the **R5** code set (`planned, in-progress, on-hold, discharged, completed, cancelled, discontinued, entered-in-error, unknown`). R4's actual required codes are `planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error`. **`arrived`, `triaged`, `onleave`, `finished` do not exist in this model at all**, and `on-hold`/`discharged`/`discontinued` don't exist in R4.
- `class` — R4's required 1..1 `Coding` — has no parent-row column; only an optional `EncounterClass` 0..* child table exists (R5's shape).
- `period` (R4) was replaced by `actualPeriod`/`plannedStartDate`/`plannedEndDate` (R5 concepts).
- `hospitalization` (R4 BackboneElement) was renamed `admission`, with `dietPreference`/`specialCourtesy`/`specialArrangement` hoisted to top-level tables — an R5-only restructuring.
- `diagnosis.condition` (R4: required 1..1 `Reference(Condition|Procedure)`) is instead an R5-style 0..* CodeableReference table whose allowed-type enum only permits `Condition` — `Procedure` is missing even under an R5 reading.
- `location.physicalType` was renamed `form` (R5 term); `subjectStatus`, `businessStatus`, `virtualService`, `careTeam` are R5-only fields with no R4 equivalent.
- R4-only fields (`statusHistory`, `classHistory`) were kept "for backward compat" alongside their R5 replacements, so the model is a hybrid that matches neither spec version cleanly.

**Impact:** this directly contradicts `CLAUDE.md`'s explicit instruction ("This project targets FHIR R4... R4 only — never `.../fhir/<resource>.html`"). Any client (including the MCP layer) expecting R4 `Encounter.status`/`Encounter.class` semantics gets wrong codes and a wrong shape. Encounter is also the most heavily cross-referenced resource in the codebase (12+ other resources hold an Encounter reference), so this is high blast-radius.

### 1.2 `Appointment` is modeled against FHIR **R5**, not R4
Same defect, independently confirmed, in `app/models/appointment/appointment.py`:

- `cancellationDate`, `previousAppointment`/`originatingAppointment`, `recurrenceId`/`occurrenceChanged`, `class[]`, `virtualService[]`, `account[]`, `recurrenceTemplate` — all confirmed absent from R4, all R5-only (the code's own comments admit this: `"R5 new"`).
- `priority` modeled as CodeableConcept — R4's is `unsignedInt`.
- `participant.required` modeled as `Boolean` — R4 requires a `required|optional|information-only` code.
- `reason`/`patientInstruction` use a CodeableReference-consolidated shape — **CodeableReference does not exist in R4** (this is called out explicitly as an R4 invariant in `CLAUDE.md` itself).
- `AppointmentBasedOnReferenceType` includes `RequestOrchestration` (R5 name) where the equivalent R4 resource is `RequestGroup` — confirmed as a real defect because `CarePlan.activity.reference` in the same codebase correctly uses `RequestGroup` for the identical concept.
- The genuine R4 field `Appointment.comment` (0..1 string) has no column at all — an R5-shaped `AppointmentNote` array exists instead but nothing stores the actual R4 field.
- `subject_type/subject_id` — **`Appointment.subject` does not exist in FHIR at all** (R4 or R5); patient linkage is via `participant.actor` in both spec versions.

### 1.3 `PractitionerRole` carries R5-only elements in place of a required R4 element
`app/models/practitioner_role/practitioner_role.py` has no root-level `telecom` (0..* ContactPoint) — a core R4 element — because it was replaced by an R5-style `contact`/ExtendedContactDetail structure (explicitly commented `[R5 extension, intentional]`), alongside R5-only `characteristic`, `communication`, and an `availability` wrapper around what R4 models as two independent flat arrays (`availableTime[]`, `notAvailable[]`). The mapper (`app/fhir/mappers/practitioner_role/fhir.py:254-256`) emits `"availability"` in output JSON — genuinely R5-shaped, not R4. **Net effect: real R4 clients lose `telecom` entirely.**

### 1.4 `InsurancePlan` stores the wrong kind of reference ID (data-integrity bug, not style)
`app/models/insurance_plan/insurance_plan.py:43,47` (`owned_by_id`, `administered_by_id`) have **no `_type` enum column at all** (the only Reference fields across the whole audit that omit the polymorphic-marker column) — and, verified against `app/repository/insurance_plan_repository.py`, they store the **raw public `organization_id` from the client's reference string**, not the internal `organization.id` PK:
- `_parse_org_ref()` (repo lines 56-71) does `int(parts[1])` directly, no DB lookup.
- The value is assigned straight onto the model (repo lines 426-441) and echoed back as `f"Organization/{model.owned_by_id}"` (mapper `insurance_plan/fhir.py:328-338`).
- Compare `episode_of_care_repository.py`'s `_resolve_managing_org_pk()` (lines 96-120), which correctly does `SELECT OrganizationModel.id WHERE organization_id == org_public_id` before storing.

This is exactly the failure mode `CLAUDE.md`'s own invariant warns about ("All reference `_id` columns store the internal `resource.id` PK, never the public sequence ID"). Because `id` and `organization_id` sequences diverge over time (organization's sequence starts at 190000, its internal PK starts at 1), this field will silently point at the wrong organization (or no organization) once enough rows exist in both tables. All other Organization/coverageArea/network/endpoint child tables in this resource have the same gap.

### 1.5 `InsurancePlan` sequence collides with `CLAUDE.md`'s documented "next available block"
`CLAUDE.md`'s sequence table ends at `EpisodeOfCare = 350000` and states **"Next available block: 360000."** But `insurance_plan.py:8` already sets `insurance_plan_id_seq = Sequence("insurance_plan_pub_seq", start=360000, ...)` — confirmed by direct read. `InsurancePlan` is entirely absent from the documented table. Anyone following `CLAUDE.md`'s stated guidance today to add a new resource would create a colliding public-ID sequence. **`CLAUDE.md` needs a correction**: add `InsurancePlan → 360000` to the table and change "next available" to `370000`.

### 1.6 `Observation` created a duplicate Postgres enum type instead of reusing the shared one
`observation.py:74-75` declares `encounter_type = Column(Enum(EncounterReferenceType, name="obs_encounter_ref_type", create_type=False))`. Confirmed live in `migrations/versions/cd944558b27f_initial_migration.py:2887`: a **separate** Postgres enum type `obs_encounter_ref_type` was actually created for this column. Every other Encounter-reference column in the codebase (12+ verified: task, service_request, questionnaire_response, procedure, medication_request, appointment, allergy_intolerance, care_plan, condition, diagnostic_report, immunization, device_request) uses the shared type name `encounter_reference_type`. This directly violates `CLAUDE.md`'s explicit invariant ("`encounter_reference_type` PG type is shared — always `create_type=False`, never create/drop it again") — the `create_type=False` flag is present but pointless, since the type name itself was forked. `ObservationEncounterReferenceType` (observation/enums.py:22-23) is dead code, defined but unused, apparently the intended-but-abandoned fix.

### 1.7 `Patient`'s Organization reference is the sole outlier missing `create_type=False`
`patient.py:71-74`: `managing_organization_type = Column(Enum(OrganizationReferenceType, name="organization_reference_type"), nullable=True)` — no `create_type=False`. A repo-wide grep of all 20 usages of `organization_reference_type` confirms this is the **only** one missing it (every other usage, including `PatientContact.organization_type` in the *same file* at line 270, has it correctly). This risks a duplicate-type-creation error the next time a migration touches this table.

### 1.8 `Practitioner` has copy-pasted Patient-only elements not in R4 `Practitioner`
- `deceased_boolean`/`deceased_datetime` (practitioner.py:49-50) — confirmed: **R4 `Practitioner` has no `deceased[x]` element** (Patient-only).
- `PractitionerCommunication.preferred` plus the whole language+preferred BackboneElement shape — confirmed R4 `Practitioner.communication` is a plain `0..* CodeableConcept`, not a structure with a `preferred` boolean (that shape belongs to `Patient.communication` only).

Both read as direct copy-paste from the Patient model rather than a Practitioner-specific implementation.

### 1.9 Systemic gap: reference columns routinely skip FK / index / eager-load
This is the single most repeated finding across all six groups — not confined to one resource. `CLAUDE.md`'s stated invariant is unambiguous: every reference `_id` column should get `ForeignKey("<table>.id")`, `index=True`, and a `lazy="selectin"` relationship. Confirmed violations, verified by group, where the target table demonstrably exists locally:

| Resource | Column(s) | Target table exists? |
|---|---|---|
| AllergyIntolerance | `encounter_id` | yes (Encounter) |
| CarePlan | `encounter_id` | yes |
| Task | `encounter_id`, `location_id` | yes (verified: `task_repository.py` never eager-loads `.encounter` because the relationship doesn't exist) |
| Encounter | `service_provider_id` (Organization), `part_of_id` (self-ref Encounter) | yes |
| EpisodeOfCare | `patient_id`, `care_manager_id`, diagnosis/referral-request reference ids | yes |
| HealthcareService | `provided_by_id` (Organization), location/coverageArea reference ids | yes |
| Immunization | `patient_id`, `encounter_id`, `location_id`, `protocolApplied.authority_id` (Organization — inconsistent with `manufacturer_id` in the *same file*, which does have the FK) | yes |
| Invoice | `issuer_id` (Organization) | yes |
| Location | `managing_organization_id`, `part_of_id` (self-ref) | yes |
| PractitionerRole | `organization`/`location`/`healthcareService`/`endpoint` reference ids (stores **public** id directly, confirmed via mapper building `f"{type}/{organization_id}"` with no join) | yes |
| Provenance | `location_id` | yes |

Some single-target references get this right (the good examples to imitate): `DocumentReference.custodian`, `Condition/DeviceRequest/DiagnosticReport/Procedure/ServiceRequest/QuestionnaireResponse.encounter`, `RelatedPerson.patient`, `Slot.schedule_fk_id`, `EpisodeOfCare.managing_organization_id`, `Immunization.manufacturer_id`. The split is roughly even and shows no principled rule (it isn't "single- vs. multi-target," since all the broken cases above are single-target) — this reads as an unevenly-applied rule rather than an intentional design split, and it's worth a dedicated repo-wide sweep beyond this audit's 35 resources.

---

## 2. Recurring convention inconsistencies (moderate priority)

These aren't wrong in any one place, but the codebase currently has 3–4 different answers to the same design question, which will keep confusing whoever adds the next resource.

1. **`__init__.py` presence/completeness is a four-way split.**
   - Missing entirely: `condition`, `patient`, `service_request`.
   - Present but empty: `terminology` (0 bytes).
   - Present, models only (no enums): `claim`, `claim_response`, `observation`, `organization`, `practitioner`, `practitioner_role`, `procedure`, `schedule`, `invoice`.
   - Present, models + enums (fullest pattern): `allergy_intolerance`, `appointment`, `audit_event`, `care_plan`, `episode_of_care`, `healthcare_service`, `immunization`, `location`, `medication`, `medication_request`, `provenance`, `questionnaire_response`, `related_person`, `insurance_plan`, `slot`, `specimen`, `task`, `vitals`.
   - **However**: a repo-wide grep shows only `Practitioner`'s package-level `__init__.py` is actually imported from elsewhere (`app.models.practitioner import PractitionerModel`, 4 call sites). Every other resource's consumers (routers/services/repositories/mappers) reach into the submodule directly (`app.models.<resource>.<resource>`), so the missing files on `condition`/`patient`/`service_request` are currently harmless dead-pattern gaps, not functional breaks — but they should either all be populated consistently or the pattern should be dropped.

2. **Two parallel `IdentifierUse` enum classes exist** (`app/models/enums.py` and `app/schemas/enums.py`), identical in value but with no shared identity, both mapping to the same Postgres type name `identifier_use`. Consumers are split roughly evenly: `questionnaire_response.py` imports the `models.enums` version; `practitioner_role.py`/`related_person.py`/`slot.py` import the `schemas.enums` version. A future edit to one won't propagate to the other despite representing the same DB column.
   - `identifier.use` storage itself is inconsistent too: typed `Enum(IdentifierUse)` in `patient`, `practitioner`, `practitioner_role`, `related_person`, `questionnaire_response`; plain `String` in `medication`, `medication_request`, `observation`, `organization`, `procedure`, `schedule`, `service_request`, `specimen`, `task`.

3. **`create_type=False` on shared enums is applied unevenly.** `RelatedPerson` and `Provenance` are the clean reference examples — every shared datatype/reference enum they touch gets it. `PractitionerRole`'s `contact`/telecom tables use the same shared `contact_point_system`/`contact_point_use`/`address_use`/etc. types and set it on **none** of them; `HealthcareServiceTelecom` likewise omits it (while `LocationTelecom`, using the identical type, gets it right in the same audit group). Combined with finding 1.6/1.7 above, this is a live migration hazard, not just inconsistency.

4. **Models importing from `app.schemas.enums`** (a layering violation — models should not depend on the schemas layer): `patient.py`, `practitioner.py`, `slot.py`. Every other resource reviewed keeps datatype enums in `app.models.enums` or resource-local `enums.py`.

5. **Gender modeling diverges for an identical FHIR value set.** `Practitioner.gender` uses the shared `AdministrativeGender` (from `app.schemas.enums`, PG type `administrative_gender`). `Patient.gender` instead defines a new `PatientGender` (in `app.models.patient.enums`, PG type `patient_gender`) with value-for-value identical content. Two representations of the same R4 `AdministrativeGender` ValueSet now exist in the schema.

6. **0..* elements occasionally flattened into comma-separated `Text` columns instead of child tables**, breaking the project's own stated "0..1 flat, 0..* child table" rule: `CarePlan.instantiatesCanonical/Uri`, `DeviceRequest.instantiatesCanonical/Uri`, `MedicationRequest.instantiatesCanonical/Uri`, `Procedure.instantiatesCanonical/Uri`, `ServiceRequest.instantiatesCanonical/Uri`. Some of these are explicitly commented as a deliberate scope tradeoff ("rarely/never queried individually" — e.g. Claim's sequence fields); others (CarePlan, Procedure) carry no such justification. Contrast: `Organization.alias` and `Provenance.policy` — identically-shaped 0..* string elements — correctly got full child tables, so the flattening isn't a hard technical necessity.

7. **`Annotation.author[x]` (identical FHIR datatype field, same fixed allowed-type list everywhere it appears) is modeled two different ways** depending on resource: a closed enum (`Practitioner|Patient|RelatedPerson|Organization`) on `ServiceRequestNote`/`MedicationRequestNote`; a plain open `String` on `ObservationNote`, `SpecimenNote`, `TaskNote`.

8. **Required (`1..1`) fields are inconsistently enforced with `nullable=False` at the DB layer.** Resources that get this right for at least their primary required Reference/status field: `AllergyIntolerance.patient`, `Coverage.status/beneficiary`, `DiagnosticReport.status`, `DocumentReference.status`, `DeviceRequest.intent`, `AuditEvent.requestor`, `Provenance.recorded/agent.who`, `MedicationRequest.status/intent`, `Slot.status`. Resources that leave a documented-required field nullable: `Condition.subject`, `CarePlan.subject`, `Claim.patient/provider`, `ClaimResponse.patient/insurer`, `Encounter.status`, `Procedure.subject`, `RelatedPerson.patient`, `ServiceRequest.subject`, `Slot.start/end` (inconsistent with `Slot.status` in the same file), `QuestionnaireResponse.questionnaire` (inverse problem: enforced `NOT NULL` even though R4 cardinality is 0..1, i.e. stricter than the spec). This may be intentional (cardinality enforced at the Pydantic/service layer instead), but no resource applies the rule fully consistently even internally, so if there is an intended rule it isn't visible from the code.

9. **The `postgresql.ENUM(..., name=..., create_type=...)` pattern `CLAUDE.md` recommends over bare `sa.Enum` is not used anywhere** in any of the 35 resource packages audited (only `terminology.py`, a non-FHIR support table, uses it). This reads as a stale/aspirational rule rather than an adopted convention — worth either enforcing going forward or removing from `CLAUDE.md`.

---

## 3. Per-resource findings

### Group A — AllergyIntolerance, Appointment, AuditEvent, CarePlan, Claim, ClaimResponse

**AllergyIntolerance** — the most spec-accurate model in this group; all onset[x] variants, reaction/manifestation, category present. Only gap: `encounter_id` has no FK/index/relationship (§1.9), and it's the only resource here that enforces `nullable=False` on a required Reference (`patient`) — see §2.8.

**Appointment** — see §1.2 (R5, not R4). `__init__.py` omits several enums actually used in the model (`AppointmentAccountReferenceType`, `AppointmentReplacesReferenceType`, `AppointmentSlotReferenceType`).

**AuditEvent** — clean. All elements present and correctly typed; `source.observer` (1..1 required) is left `nullable=True` against spec, the one gap found. Good example of omitting the spurious `text` column on plain `Coding` fields (unlike CodeableConcept fields elsewhere that sometimes get one they don't need).

**CarePlan** — `subject` (1..1) left nullable (§2.8). `instantiatesCanonical`/`instantiatesUri` flattened to CSV text (§2.6). `encounter_id` missing FK (§1.9). Otherwise thorough — full `activity.detail` scheduled[x]/product[x] choice coverage, correct `RequestGroup` reference naming (contrast with Appointment's R5 `RequestOrchestration`).

**Claim** — exceptionally complete (down to `item.detail.subDetail`, full `supportingInfo.value[x]` choice set). `patient`/`provider` (both 1..1) left nullable despite the code's own comments stating "(1..1 Reference(...))" (§2.8). `__init__.py` re-exports models only, not its 15 enums.

**ClaimResponse** — equally thorough (top-level `adjudication`, full `payment`/`addItem.detail.subDetail`). `patient`/`insurer` (both 1..1) left nullable. Same `__init__.py` enum-export gap as Claim.

### Group B — Condition, Coverage, DeviceRequest, DiagnosticReport, DocumentReference, Encounter

**Condition** — complete element coverage including nested `stage.assessment`/`evidence.code/detail`. No `__init__.py` (§2.1). `subject` (1..1) left nullable. Inconsistent indexing: `subject_id` indexed, `recorder_id`/`asserter_id` not, within the same file.

**Coverage** — the cleanest resource in this group for DB-level enforcement: `status` and `beneficiary` correctly `nullable=False`. One internal inconsistency: `CoverageClass.value` (1..1) is enforced, but the sibling `CoverageCostToBeneficiaryException.type` (also 1..1) is not.

**DeviceRequest** — `subject` (1..1) left nullable. `instantiatesCanonical`/`instantiatesUri` flattened to CSV (§2.6). `code_reference_id` (Device-only target) has no FK, but likely unavoidable since this codebase has no local `device` table.

**DiagnosticReport** — otherwise the cleanest resource of the six against this rubric; only gap is `code` (1..1 CodeableConcept) left nullable. Good reuse: `performer`/`resultsInterpreter` correctly share one allowed-type enum since their target sets are identical per spec.

**DocumentReference** — the reference example for "0..1 flat, 0..* child table" done with zero exceptions (`context.encounter/event/related` → child tables; `context.period/facilityType/practiceSetting/sourcePatientInfo` → flattened). `custodian` is the textbook-correct Organization-reference implementation (FK + index + `lazy="selectin"`) that several other resources should be matched against (§1.9). `__init__.py` uses relative imports where every other resource's `__init__.py` uses absolute — cosmetic only.

**Encounter** — see §1.1 (R5, not R4) — the most severe single finding in this audit. Also: `service_provider_id`/`part_of_id` missing FK/index/relationship despite valid local targets (§1.9), and `status` left nullable under either spec reading.

### Group C — EpisodeOfCare, HealthcareService, Immunization, InsurancePlan, Invoice, Location

**EpisodeOfCare** — complete against spec. `managing_organization_id` correctly FK'd, but `patient_id`/`care_manager_id`/diagnosis and referral-request reference ids are not, in the same file (§1.9) — proof the pattern is known but unevenly applied even within one resource.

**HealthcareService** — complete against spec (23 elements + eligibility/availableTime/notAvailable). `provided_by_id` missing FK (§1.9). `HealthcareServiceTelecom` omits `create_type=False` on a shared type that `Location`'s identical field gets right (§2.3).

**Immunization** — complete, including the SimpleQuantity nuance on `doseQuantity` (correctly omits `comparator`). `patient_id`/`encounter_id`/`location_id` missing FK; `protocolApplied.authority_id` missing FK while `manufacturer_id` in the same file has it (§1.9).

**InsurancePlan** — see §1.4 (wrong-ID data bug) and §1.5 (sequence collision) — the most consequential findings outside Encounter/Appointment. Also the only resource with zero `_type` enum columns on any Reference field. `plan.specificCost.benefit.cost.qualifiers` (0..*) flattened into a single Text column, an acknowledged tradeoff but a break from every other resource's child-table handling of 0..*.

**Invoice** — complete against spec including the `chargeItem[x]` choice. `issuer_id` missing FK (§1.9). `__init__.py` re-exports models only, omitting all 6 enums — the outlier within this particular group (all its 5 siblings export enums too).

**Location** — complete, including flattened `position`/`hoursOfOperation`. `managing_organization_id`/`part_of_id` (self-ref) missing FK (§1.9). Correctly sets `create_type=False` on shared telecom enum types — the good example HealthcareService should match.

### Group D — Medication, MedicationRequest, Observation, Organization, Patient, Practitioner

**Medication** — complete, correctly splits 0..* `ingredient`/`identifier` into child tables. Cleanest `__init__.py` of the six (models + enums).

**MedicationRequest** — reference-target enums are unusually accurate (correctly 0..1, not 0..*, on `requester`/`performer` per spec). `instantiatesCanonical`/`instantiatesUri` flattened to CSV (§2.6) — contrast with `Organization.alias`, an identically-shaped field, getting a real child table in the same group. `subject` (1..1) left nullable while `status`/`intent` are enforced, in the same model.

**Observation** — the most spec-accurate model of the six: full 11-way `value[x]`, full 4-way `effective[x]`, all Reference target-type enums verified exact. See §1.6 for the one serious defect (`obs_encounter_ref_type` duplicate enum type, confirmed live in the migration). `ObservationNote.author_reference_type` is open `String` where `MedicationRequestNote`'s identical field is a closed enum (§2.7).

**Organization** — complete against spec. `partof_type` is the correct reference implementation of the shared-enum pattern (`create_type=False`) that Patient (§1.7) fails to replicate.

**Patient** — complete against spec, correct `PatientGender` value set. See §1.7 (missing `create_type=False`, sole outlier of 20 usages) and §2.1 (no `__init__.py`, confirmed the only one of these six missing it, with 9 external consumers all reaching into submodules directly). Also imports datatype enums from `app.schemas.enums` (§2.4) and defines a redundant `PatientGender` duplicating `AdministrativeGender` (§2.5).

**Practitioner** — see §1.8 (copy-pasted Patient-only `deceased[x]` and `communication.preferred`, neither valid on R4 `Practitioner`). `practitioner/enums.py` is a completely empty file (dead scaffolding). `__init__.py` is the good-practice case here — populated and genuinely consumed by 4 external call sites, unlike Patient's absent file.

### Group E — PractitionerRole, Procedure, Provenance, QuestionnaireResponse, RelatedPerson, Schedule

**PractitionerRole** — see §1.3 (R5 elements displacing required R4 `telecom`). Also: `practitioner` relationship missing `lazy="selectin"` (§1.9-adjacent — violates "always eager-load"); unique dual-column reference pattern (`practitioner_fk_id` + `practitioner_ref_id`) not seen anywhere else in the codebase; `DayOfWeek` enum defined but unused (`days_of_week` stored as raw CSV text instead).

**Procedure** — `instantiatesCanonical`/`instantiatesUri` flattened to CSV (§2.6) — inconsistent with `Provenance.policy[]` (identically-shaped 0..* uri) in the very next resource, which correctly gets a child table. `subject` (1..1) left nullable. Good example: `EncounterReferenceType` correctly reused with `create_type=False`.

**Provenance** — `entity.agent` omits `role[]` (0..* CodeableConcept) that the top-level `agent.role[]` correctly has, despite both reusing the identical R4 BackboneElement shape. `Signature.who`/`onBehalfOf` stored as open `String` despite spec defining a closed target-type set identical to `agent.who`'s (which correctly uses a closed enum) — internally inconsistent within the same file. Otherwise the best example in the whole audit of the shared-enum convention done right, and the only resource consistently enforcing required-Reference cardinality (`recorded`, `agent.who`) at the DB level.

**QuestionnaireResponse** — recursive `item`/`item.answer.item` correctly modeled via adjacency list (self-FK + `use_alter=True` to break the item↔answer circular dependency) — no artificial depth limit, a well-executed solution to the hardest modeling problem in this batch. One inversion of §2.8: `questionnaire` (0..1 per spec) is incorrectly enforced `nullable=False`, stricter than the spec requires. `value_reference` stored as a single raw string rather than the `(type, id, display)` triple used everywhere else in the same resource.

**RelatedPerson** — the cleanest resource in this group: full element coverage, and the single best example across the *entire* audit of consistent `create_type=False` usage across every shared enum it touches. `patient_id` is the textbook FK+index+`lazy="selectin"` implementation.

**Schedule** — complete against spec, correct 7-member `actor` target-type set. `ScheduleIdentifier.use` is plain `String`, not the shared enum (§2.2). `__init__.py` doesn't re-export `ScheduleActorReferenceType`.

### Group F — ServiceRequest, Slot, Specimen, Task, Terminology, Vitals

**ServiceRequest** — near-complete against spec; correct closed enum for `Annotation.author[x]` (contrast with Specimen/Task below). No `__init__.py` (§2.1) — the only resource in this group missing one. `instantiatesCanonical`/`instantiatesUri` flattened to CSV, explicitly commented as deliberate. `encounter_id` is the correct reference implementation (FK+index+`lazy="selectin"`) that Task fails to match in the same group.

**Slot** — `start`/`end` (both 1..1 required) left nullable while `status` (also 1..1) is correctly enforced, in the same table. Imports `IdentifierUse` from `app.schemas.enums` (§2.4). `schedule_fk_id` is the only reference column in the entire codebase using a `_fk_id` suffix instead of the universal `_id` convention — cosmetic, but it does correctly carry the FK/index/relationship.

**Specimen** — exceptionally complete: every choice-type variant at both `processing` and `container` level modeled, all Reference target sets exact. Only gap: `SpecimenNote.author_reference_type` is open `String` vs. ServiceRequest's closed enum for the identical datatype field (§2.7).

**Task** — `encounter_id` has no FK/index/relationship — confirmed via `task_repository.py` never eager-loading `.encounter` because the relationship doesn't exist — despite reusing the same shared `EncounterReferenceType` enum that `ServiceRequest.encounter_id` (correctly implemented) also uses, in the same audit group (§1.9). `location_id` has the same gap.

**Terminology** — not a FHIR clinical resource; a support service for code/valueset lookups (`$lookup`/`$validate-code`/`$translate`/`$expand`-style operations, plain JSON only, no `resourceType`). Appropriately has no public `<resource>_id` sequence and no `user_id`/`org_id` on the global lookup tables (correctly absent from `CLAUDE.md`'s sequence table, unlike InsurancePlan). `TerminologyConcept` does carry nullable `org_id`/`user_id` plus a sensible partial-unique-index design for org-specific custom concepts alongside global ones. `__init__.py` is empty (0 bytes) — harmless (nothing imports through it) but the most incomplete file of its kind found in the audit. No table has `created_by`/`updated_by`, which would be useful specifically for the org-specific custom-concept rows.

**Vitals** — intentionally not FHIR-Observation-shaped per `CLAUDE.md`'s explicit carve-out (plain JSON only, `resolve_vitals` instead of `require_permission`) — correctly not held to FHIR conformance. All Standard Columns present and correct (sequence starts at 70000, matching `CLAUDE.md`). `patient_id` has `index=True` but no FK — reasonable given its simplified, non-relational design, but noted as the one place a cross-resource link exists without FK enforcement.

---

## 4. Sequence allocation verification

Every resource's actual `Sequence(..., start=N)` was cross-checked against `CLAUDE.md`'s table. All 34 documented resources match exactly. The only discrepancy:

| Resource | `CLAUDE.md` table | Actual `start=` | Status |
|---|---|---|---|
| InsurancePlan | *(absent from table)* | 360000 | **Collides with "Next available block: 360000"** — see §1.5 |

`QuestionnaireResponse`'s `start=60000` was verified to match the documented value despite the apparent gap where a `50000` block would be expected between `Appointment (40000)` and `QuestionnaireResponse (60000)` — this is a pre-existing documentation gap (likely a retired resource), not an error; no action needed beyond awareness.

---

## 5. Suggested priority order for fixes

1. **InsurancePlan wrong-ID bug (§1.4)** — silent data-correctness issue that gets worse as both sequences grow; highest real-world risk.
2. **`CLAUDE.md` sequence table correction (§1.5)** — one-line doc fix, prevents a future collision.
3. **Observation duplicate enum type (§1.6)** — requires a migration to consolidate `obs_encounter_ref_type` into `encounter_reference_type`; do this before more columns fork the same way.
4. **Patient `create_type=False` (§1.7)** — one-line fix.
5. **Encounter / Appointment / PractitionerRole R4 vs R5 (§1.1–1.3)** — largest effort (real schema changes, migrations, mapper rewrites), but highest-severity spec-conformance gap; worth scoping as a dedicated project given the size.
6. **Systemic reference FK/index/eager-load sweep (§1.9)** — mechanical, resource-by-resource; a good candidate for the existing `/fhir-db-model` skill applied retroactively.
7. **§2 convention inconsistencies** — lower urgency; best addressed opportunistically whenever a resource is touched for another reason, or standardized in one pass if the team wants to lock down a single answer for each (particularly `IdentifierUse` source-of-truth and the `__init__.py` re-export pattern, which is currently dead-code-only anyway and could reasonably be dropped instead of completed).

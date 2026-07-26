# Action Items — FHIR R4 Model Audit

Checklist derived from [`models-fhir-r4-audit.md`](./models-fhir-r4-audit.md). Section references (`§x.x`) point back to that file for full detail, file:line citations, and the reasoning behind each item. Ordered by priority.

---

## 1. Data-integrity / migration risk (fix first)

- [ ] **InsurancePlan stores the wrong kind of reference ID.** `owned_by_id`/`administered_by_id` (and other Organization/coverageArea/network/endpoint refs) save the client's raw public `organization_id` instead of resolving it to the internal `organization.id` PK, unlike every other resource's repository. Fix `insurance_plan_repository.py` to resolve-then-store like `episode_of_care_repository.py::_resolve_managing_org_pk()` does, and add the missing `_type` enum columns. — [§1.4](./models-fhir-r4-audit.md#14-insuranceplan-stores-the-wrong-kind-of-reference-id-data-integrity-bug-not-style)
- [ ] **Observation forked a duplicate Postgres enum type** (`obs_encounter_ref_type` instead of the shared `encounter_reference_type`), confirmed live in the initial migration. Needs a migration to consolidate the two types before more columns fork the same way. Remove the now-dead `ObservationEncounterReferenceType`. — [§1.6](./models-fhir-r4-audit.md#16-observation-created-a-duplicate-postgres-enum-type-instead-of-reusing-the-shared-one)
- [ ] **Patient is missing `create_type=False`** on `managing_organization_type` (`organization_reference_type`) — the sole outlier of 20 usages repo-wide. One-line fix. — [§1.7](./models-fhir-r4-audit.md#17-patients-organization-reference-is-the-sole-outlier-missing-create_typefalse)

## 2. Documentation fix

- [ ] **Add InsurancePlan to `CLAUDE.md`'s sequence allocation table** (`start=360000`) and bump "Next available block" from 360000 → 370000 — it currently documents a block InsurancePlan already occupies. — [§1.5](./models-fhir-r4-audit.md#15-insuranceplan-sequence-collides-with-claudemds-documented-next-available-block) / [§4](./models-fhir-r4-audit.md#4-sequence-allocation-verification)

## 3. Spec-version regressions (largest effort — scope as dedicated work)

- [ ] **Encounter is modeled against FHIR R5, not R4** — wrong `status` codes, missing required `class`, `period`→`actualPeriod` rename, R5-only `admission`/`virtualService`/`careTeam`/`businessStatus`, `diagnosis.condition` missing `Procedure` as a target. Highest blast-radius item since 12+ other resources reference Encounter. — [§1.1](./models-fhir-r4-audit.md#11-encounter-is-modeled-against-fhir-r5-not-r4)
- [ ] **Appointment is modeled against FHIR R5, not R4** — R5-only `cancellationDate`/`class[]`/`virtualService[]`/`account[]`/`recurrenceTemplate`, `priority` wrong datatype, `participant.required` wrong datatype, CodeableReference usage (doesn't exist in R4), non-existent `Appointment.subject`, `RequestOrchestration` should be `RequestGroup`. Real R4 `comment` field has no column at all. — [§1.2](./models-fhir-r4-audit.md#12-appointment-is-modeled-against-fhir-r5-not-r4)
- [ ] **PractitionerRole carries R5-only `contact`/`characteristic`/`communication`/`availability` in place of required R4 `telecom`** — R4 clients lose `telecom` entirely. — [§1.3](./models-fhir-r4-audit.md#13-practitionerrole-carries-r5-only-elements-in-place-of-a-required-r4-element)
- [ ] **Practitioner has copy-pasted Patient-only elements** (`deceased[x]`, `communication.preferred`) that don't exist on R4 `Practitioner` — smaller, isolated cleanup, not part of the R5 items above but same root cause (spec confusion). — [§1.8](./models-fhir-r4-audit.md#18-practitioner-has-copy-pasted-patient-only-elements-not-in-r4-practitioner)

## 4. Systemic sweep

- [ ] **Reference columns missing FK / index / `lazy="selectin"`** across ~12 resources where the target table exists locally (Task.encounter/location, AllergyIntolerance.encounter, CarePlan.encounter, Encounter.service_provider/part_of, EpisodeOfCare×4, HealthcareService.provided_by, Immunization×3, Invoice.issuer, Location×2, PractitionerRole×4, Provenance.location). Good reference implementations to copy from: `DocumentReference.custodian`, `RelatedPerson.patient`, `ServiceRequest.encounter`. Candidate for applying the `/fhir-db-model` skill retroactively, resource by resource. — [§1.9](./models-fhir-r4-audit.md#19-systemic-gap-reference-columns-routinely-skip-fk--index--eager-load)

## 5. Lower-priority convention cleanup (opportunistic)

- [ ] Pick one source of truth for `IdentifierUse` (`app.models.enums` vs `app.schemas.enums`) and one storage type (`Enum` vs plain `String`) — currently split across resources. — [§2.2](./models-fhir-r4-audit.md#2-recurring-convention-inconsistencies-moderate-priority)
- [ ] Apply `create_type=False` consistently to all shared enum usages — `PractitionerRole` and `HealthcareServiceTelecom` currently omit it where siblings don't.
- [ ] Stop models importing from `app.schemas.enums` (`patient.py`, `practitioner.py`, `slot.py`) — layering violation.
- [ ] Decide whether `Patient.gender`/`PatientGender` should just reuse `AdministrativeGender` like `Practitioner.gender` does, instead of duplicating the value set.
- [ ] Either populate or drop the `__init__.py` re-export pattern — it's currently dead code everywhere except `Practitioner`'s (verified: nothing else imports through the package root). `condition`, `patient`, `service_request` have no file at all; `terminology`'s is empty.
- [ ] Standardize `Annotation.author[x]` typing (closed enum vs open `String`) — currently inconsistent between `ServiceRequest`/`MedicationRequest` and `Observation`/`Specimen`/`Task`.
- [ ] Decide on a consistent rule for when 1..1-required fields get `nullable=False` at the DB layer — currently applied unevenly both across and within resources (e.g. `Slot.status` enforced but `Slot.start`/`end` not).
- [ ] Either adopt `postgresql.ENUM(..., create_type=...)` everywhere as `CLAUDE.md` recommends, or drop that line from `CLAUDE.md` — no resource currently uses it.

---

*Generated from a full audit of all 35 `app/models/` resource packages against the FHIR R4 spec and this repo's `CLAUDE.md` conventions. See the full report for per-resource detail.*

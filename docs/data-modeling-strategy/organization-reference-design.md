# Organization — a from-scratch reference design

**This is a clean-slate design, not a patch to the current schema.** You asked for how I'd
design Organization today, ignoring what's already built, optimizing for strict FHIR R4
conformance, production scalability, and multi-tenant correctness at once. Where this ends up
differing from the current `app/models/organization/` code, that's named explicitly in §9 —
but the design itself is derived from first principles, not from a diff.

Every cardinality and binding-strength claim below is checked against the live R4 spec
(`hl7.org/fhir/R4/organization.html` §8.6.3.1's Terminology Bindings table, and
`hl7.org/fhir/R4/datatypes.html` for `ContactPoint`/`Address`/`Identifier`), not recalled from
memory — the enum-vs-string decision in §4 depends entirely on getting these exactly right.

---

## 1. Governing design principles

Stated up front because every column decision below is an application of one of these, not
an independent judgment call:

1. **The database encodes the loosest legally-valid shape the base R4 spec allows — nothing
   stricter, nothing looser.** Any rule tighter than base R4 (a hospital requiring `name`, a
   country mandating a specific `type`) belongs in the profile layer
   (`fhir-profiling-and-extensibility-strategy.md`), not in `NOT NULL`/`UNIQUE`. This is the
   same principle already applied when `Organization.active`/`name` were relaxed to nullable
   — this design generalizes it to every column and extends it to constraints, not just
   nullability.
2. **A spec invariant becomes a DB constraint only if it's checkable from a single row.**
   `org-2`/`org-3` ("no address/telecom with `use = 'home'`") are single-row, permanent, and
   universal — real Postgres `CHECK` constraints, for free, forever. `org-1` ("name or
   identifier required") spans two tables (`organization` + `organization_identifier`) — that
   cannot be a column constraint, and belongs in the service-layer validation pipeline
   instead. Getting this distinction right is what makes "100% FHIR standard" actually
   buildable rather than aspirational.
3. **A Postgres `Enum` is used only where R4 binds the element as `required`** — a binding
   strength that can never legally change, be widened, or be swapped out by any profile at
   any layer, for any deployment, ever. Everything bound `example`/`extensible`/`preferred` is
   plain `String`, validated dynamically against the resolved profile's terminology binding at
   write time (`TerminologyService`), because that value set is explicitly allowed to vary by
   country/organization.
4. **Every cross-resource reference follows one uniform pattern — flattened, no DB-level FK,
   existence validated by the service layer — even when a specific field's target type happens
   to be fixed today.** `Organization.partOf` is `Reference(Organization)` only, by spec — a
   real, self-referential FK was considered for exactly this reason (see §5 for the full
   back-and-forth), but reverted: most FHIR `Reference` fields genuinely are polymorphic, and
   having real FKs for the few fields that aren't today while flattening everything else is two
   patterns to maintain instead of one, with no schema-migration safety net if a field's target
   types ever change. The cost is explicit and accepted: referential integrity for these fields
   depends entirely on the service-layer check being correct, with no Postgres-level backstop.
   **Containment FKs (a child row belonging to its parent — `organization_identifier.organization_pk`,
   etc.) are a completely different thing and stay real FKs** — that's structural ownership, not
   a `Reference` datatype, and polymorphism never applies to it.
5. **Multi-tenancy columns (`tenant_id`, `created_by`, `updated_by`) are infrastructure, not
   FHIR content.** They never appear in the FHIR JSON this resource produces; they exist so one
   Postgres database can serve many tenants safely. Keeping them visually and structurally
   separate from the FHIR-derived columns (grouped at the top of every table, documented as
   "not a FHIR field") avoids the confusion the current codebase already calls out explicitly
   on `OrganizationCreateSchema` — worth keeping that clarity, this isn't a place to improve.
   `tenant_id` is a deliberate rename from this project's existing `org_id` — see
   `app/models/organization_design_claude/shared/tenant_audit.py`'s docstring for why.
6. **Extension support is a day-one column, not a bolt-on.** A JSONB `extension` array on the
   root table from the start, per `fhir-profiling-and-extensibility-strategy.md` §6 — adding it
   later means an extra migration touching live data; adding it now costs an empty default.
7. **Normalized relational, one table per `0..*` element, stays the right storage paradigm** —
   this isn't up for debate in this pass. `storage-strategies.md` already settled that
   question for this project (native EMR, not a pure FHIR interop repository); this design
   just applies that decision correctly to one resource, all the way down.

---

## 2. Root table — `organization`

| Column | Type | Nullable | Cardinality source | Notes |
|---|---|---|---|---|
| `id` | `BigInteger` PK | no | — | Internal PK, never exposed |
| `organization_id` | `BigInteger`, sequence-backed, unique, indexed | no | — | Public ID, sequence starting at this resource's allocated block |
| `tenant_id` | `String`, indexed | no | — | **Tenant-scoping, not FHIR.** Distinct from the `Organization` entity itself. Renamed from `org_id` — see principle 5 |
| `created_by` | `String` | no | — | From verified JWT `sub` — not FHIR, not a body field |
| `updated_by` | `String` | yes | — | Same |
| `created_at` / `updated_at` | `DateTime(timezone=True)` | server-default / onupdate | — | Indexed (see §7) — this project's own earlier scalability review flagged these as sortable-but-unindexed; fixed here from the start |
| `active` | `Boolean` | **yes, no default** | `0..1`, R4 explicitly removed R3's `true` default | Absent means *unknown*, not false — do not default it |
| `name` | `String` | **yes** | `0..1` | `org-1` (name or identifier required) enforced in the service layer, not here — see principle 2 |
| `partof_reference` | `String` | yes | `Reference.reference` | The raw literal string as received — relative or an absolute URL to another system entirely — kept independently of whether it resolves locally; see §5 |
| `partof_id` | `BigInteger`, no FK, indexed | yes | Our resolved interpretation of `partof_reference` | Holds the **public** `organization_id`, not an internal PK — no DB-level FK; existence validated by the service layer, same pattern as every other reference in this codebase — see §5 for why the FK was reverted |
| `partof_type` | `Enum` (single member: `Organization`) | yes | `Reference.type` | Always `"Organization"` — still stored; it's an independent spec element, not a polymorphism discriminator — see §5 |
| `partof_display` | `String` | yes | `Reference.display` | |
| `partof_identifier_*` (11 columns: `use`, `type_system/version/code/display/text/user_selected`, `system`, `value`, `period_start/end`) | `String`/`Boolean`/`DateTime`/`Enum` | yes | `Reference.identifier` | The logical-reference fallback — see §5 |
| `extension` | `JSONB`, default `[]` | no (default empty) | N/A — extension mechanism | Resource-level only, per the profiling doc §6 |

Two `CHECK` constraints cover `partOf`'s `Reference`-shape rules — see §5 for the full
reasoning: `ck_organization_partof_reference_shape` (*"at least one of reference, identifier and
display SHALL be present"*, whenever `partOf` is used at all) and
`ck_organization_partof_resolved_has_reference` (`partof_id` never set without
`partof_reference` also being on record).

No `UniqueConstraint` on `name`. No `UniqueConstraint` on anything beyond `organization_id`
itself — any organizational uniqueness rule a specific deployment wants (unique name per
country, unique registration number) is a profile-layer invariant, not a base-table
constraint, per principle 1.

---

## 3. Child tables

Each `0..*` element gets its own table, FK'd to `organization.id` via `organization_pk` —
pure containment (a child row belonging to its parent), a real FK regardless of how `partOf`
is modeled, since this isn't a `Reference` datatype and polymorphism doesn't apply to it. Named
`organization_pk`, not `organization_id`, specifically so it's never confused with
`OrganizationModel.organization_id` (the public, FHIR-facing sequence ID) — see principle 4.

### `organization_identifier` — `identifier` (0..*)

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | `BigInteger` PK | no | |
| `organization_pk` | `BigInteger`, FK → `organization.id`, indexed | no | Containment FK — see §3's intro |
| `tenant_id` | `String` | no | Tenant-scoping, duplicated down for query convenience (standard pattern already used throughout this codebase) |
| `use` | **`Enum(IdentifierUse)`** | yes | `Identifier.use` is `required`-bound (principle 3) |
| `type_system`/`type_version`/`type_code`/`type_display`/`type_text`/`type_user_selected` | `String`/`Boolean` | yes | `Identifier.type` is a `CodeableConcept`, no binding strength specified at all in base R4 for the generic `Identifier` type — plain columns, profile-governed if a deployment wants to constrain it |
| `system` | `String` | yes | `0..1` on `Identifier` — not required even here |
| `value` | `String` | yes | `0..1` — same |
| `period_start`/`period_end` | `DateTime(timezone=True)` | yes | |
| `assigner_reference` | `String` | yes | `Reference.reference`, raw literal — same reasoning as `partof_reference`, see §5 |
| `assigner_id` | `BigInteger`, no FK, indexed | yes | Holds the public `organization_id`; existence validated by the service layer, same as `partof_id` — see §5 |
| `assigner_type` | `Enum` (single member) | yes | `Reference.type` — same reasoning as `partOf`, see §5 |
| `assigner_display` | `String` | yes | |
| `assigner_identifier_*` (11 columns) | `String`/`Boolean`/`DateTime`/`Enum` | yes | `Reference.identifier` fallback — same reasoning as `partOf`, see §5 |

Same `CHECK` treatment as `partOf`: `ck_organization_identifier_assigner_reference_shape` and
`ck_organization_identifier_assigner_resolved_has_reference`.

**No `UniqueConstraint` on `(system, value)` — at all, not even tenant-scoped.** This departs
from even the earlier "scope it to the tenant" recommendation: in a from-scratch design, base
R4 places zero uniqueness requirement on `Identifier`, and a from-scratch schema shouldn't
invent one that isn't there. If a deployment wants "unique MRN per org," that's a textbook
profile-layer invariant (`fhir-profiling-and-extensibility-strategy.md` §2's invariant
mechanism), not a base-table rule — this is the one spot where "don't rely on current design"
produces a materially different answer than the earlier incremental fix did.

### `organization_type` — `type` (0..*)

`CodeableConcept`, binding **`example`** (confirmed via the spec's own Terminology Bindings
table — the loosest possible strength). Flattened single-coding + text, all plain `String`:
`coding_system`, `coding_version`, `coding_code`, `coding_display`, `coding_user_selected`,
`text`. No enum anywhere on this table — an `example` binding is explicitly "not expected or
even encouraged" to constrain instances at all.

### `organization_alias` — `alias` (0..*)

| Column | Type | Nullable |
|---|---|---|
| `id` | `BigInteger` PK | no |
| `organization_pk` | FK, indexed | no |
| `tenant_id` | `String` | no |
| `value` | `String` | no — an alias row with no text isn't a meaningful row |

Simplest table in the resource — `alias` is just `0..* string`, nothing else to model.

### `organization_telecom` — `telecom` (0..*)

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `system` | **`Enum(ContactPointSystem)`** | yes | `required` binding |
| `value` | `String` | yes | `0..1` |
| `use` | **`Enum(ContactPointUse)`** | yes | `required` binding |
| `rank` | `Integer` | yes | `0..1 positiveInt` |
| `period_start`/`period_end` | `DateTime(timezone=True)` | yes | |

**`CHECK (use IS DISTINCT FROM 'home')`** — `org-3`, enforced directly in Postgres. This is
not a profile concern; it's a permanent base-spec rule with no cross-table dependency, so it
gets the cheapest, most reliable enforcement available.

### `organization_address` — `address` (0..*)

Standard flattened `Address`: `use` (**`Enum(AddressUse)`**, required binding), `type`
(**`Enum(AddressType)`**, required binding), `text`, `line` (as a `String[]` array column or a
grandchild table — either is defensible; a Postgres `text[]` column is simpler and `line` has
no sub-structure worth a table), `city`, `district`, `state`, `postal_code`, `country`,
`period_start`/`period_end`.

**`CHECK (use IS DISTINCT FROM 'home')`** — `org-2`, same reasoning as `org-3` above.

### `organization_contact` + `organization_contact_telecom` — `contact` (0..*)

`contact` is a `BackboneElement` with its own nested `telecom: 0..*`, so it needs a grandchild
table, not a flattened column set:

**`organization_contact`**: `purpose_system`/`purpose_version`/`purpose_code`/
`purpose_display`/`purpose_text` (`CodeableConcept`, **`extensible`** binding — `String`, not
enum, per principle 3 — this is a real, verified contrast with `organization_type`'s
`example` binding right above it: extensible is still not `required`, so it's still `String`,
but it's a meaningfully different strength a profile is more likely to actually tighten), plus
the flattened `HumanName` fields for `name` (`name_use` — **`Enum(HumanNameUse)`**, required
binding — `name_text`, `name_family`, `name_given` as `String[]`, `name_prefix`/`name_suffix`
as `String[]`), plus the flattened `Address` fields for `contact.address` (same shape as
`organization_address` but `0..1` here, not `0..*`, so the fields live directly on this table
rather than a further child table).

**`organization_contact_telecom`**: identical shape to `organization_telecom`, FK'd to
`organization_contact.id`. **No `org-3`-style CHECK here** — that invariant is scoped to
`Organization.telecom` specifically in the base spec text, not `Organization.contact.telecom`;
applying it here anyway would be inventing a stricter rule than R4 actually states, which
principle 1 explicitly rules out.

### `organization_endpoint` — `endpoint` (0..*)

`Reference(Endpoint)`. Endpoint isn't a modeled resource in this system (per the existing
codebase's own note), so this one stays a **flattened** reference — not because of principle 4's
polymorphism test (it isn't polymorphic, it's single-target same as `partOf`), but because the
target table doesn't exist locally to FK against at all. This is the one row in this whole
design where "flattened, no FK" is the only option, not a judgment call — worth stating
explicitly so it doesn't look like an inconsistency with §5's `partOf` decision.

No `UniqueConstraint` on `(organization_id, reference_type, reference_id)` — R4 doesn't forbid
listing the same endpoint twice, and a from-scratch design shouldn't add a rule the spec
doesn't ask for (principle 1), even though it's a plausible data-hygiene nicety. If duplicate
endpoints turn out to be a real operational nuisance, that's a profile-layer invariant
(`endpoint.count() = endpoint.distinct().count()`, in FHIRPath terms), not a base constraint.

---

## 4. Enum classification, summarized

| Column | Binding strength | DB type |
|---|---|---|
| `identifier.use`, `contact.name.use` | required | `Enum` |
| `telecom.system`, `telecom.use` | required | `Enum` |
| `address.use`, `address.type` | required | `Enum` |
| `type` (`Organization.type`) | **example** | `String` |
| `contact.purpose` | **extensible** | `String` |
| `identifier.type` | unspecified in base `Identifier` | `String` |

This is the mechanical audit promised in the profiling report's §7, now actually done for one
resource — the pattern (fetch the real binding strength, don't assume) is the reusable part;
applying it to the other 7 rolled-out resources is the natural next step once this one is
agreed on.

---

## 5. The `partOf` / `assigner` decision — the full journey, and where it landed

This section went through three real iterations in review. Keeping all three visible, briefly,
because each one caught something the last one missed — this is as much a record of *how* to
reason about `Reference` fields as it is a final answer for this one.

**Iteration 1 — real FK.** `Organization.partOf` and `Identifier.assigner` are both
`Reference(Organization)` — no second possible target type, ever, by spec — so a real,
self-referential `ForeignKey("organization.id")` was proposed: Postgres rejects a dangling
reference at write time, no 422 round-trip needed, and it prevents the exact orphaning bug the
scalability report found in the current `delete()` path, structurally rather than by an
application-level guard someone has to remember to add.

**Iteration 2 — the FK silently dropped two real `Reference` fields.** `Reference` is
`{reference, type, identifier, display}`, each independently `0..1`
(`hl7.org/fhir/R4/references.html`). The real-FK version kept only an internal resolved FK plus
`display`, which quietly made two legal states unrepresentable: `type` is an independent
element of the datatype itself (present on every reference, polymorphic target or not — not a
discriminator that stops mattering once there's only one legal value), and `identifier` (the
*logical reference* — *"no requirement that it point to something actually exposed as a FHIR
instance"*) is how a sender legitimately points at a parent org with no local resource at all
(e.g. "part of" a national network never modeled as a row here). Both were restored, plus a
raw `{prefix}_reference` string column for the literal value as received (an external absolute
URL has nowhere else to live — it isn't a resolvable FK and it isn't a structured
`Identifier`). This also surfaced `Reference`'s own cross-field rule — *"at least one of
reference, identifier and display SHALL be present"* — checkable from a single row, so it
became a real `CHECK` constraint the same way `org-2`/`org-3` are (principle 2).

**Iteration 3 — the real FK itself was reverted.** Keeping a real FK for `partOf`/`assigner`
while every genuinely polymorphic reference in this system (and every other reference in the
rest of this codebase) stays flattened-with-no-FK means maintaining two different reference
patterns side by side, chosen per-field based on whether that field's target happens to be
single-typed *today*. That's a real, ongoing cost — not just stylistic inconsistency — for a
"since there's only one target type now, we can special-case it" calculation that has to be
redone, correctly, for every reference field in the system. The decision: drop the FK, keep
everything else from iteration 2 (`{prefix}_reference`, `{prefix}_type`, the `identifier`
fallback, both `CHECK` constraints), and store the **public** `organization_id` in
`partof_id`/`assigner_id` rather than the internal PK — consistent with how `{prefix}_id`
already works for every other flattened reference in this codebase, and with what's actually
serialized into `"Organization/{id}"`. **Accepted cost, stated plainly:** referential
integrity for these fields now depends entirely on the service-layer `ensure_resource_exists()`
-style check being correct — there is no Postgres-level backstop if that check has a bug, which
is exactly the class of risk a real FK would have closed. This mirrors the actual
`RESOURCE_REGISTRY` convention already in use for every other reference in this codebase; no
inconsistency with sibling resources remains.

**What stays a real FK regardless: containment.** `organization_identifier.organization_pk`
(and the equivalent column on every other child table) is a completely different relationship
— a child row belonging to its parent, not a `Reference` datatype — and polymorphism never
applies to it. Named `organization_pk`, not `organization_id`, specifically so it's never
confused with `OrganizationModel.organization_id` (the public, FHIR-facing sequence ID) — same
literal name, two unrelated meanings, was a real point of confusion worth naming and fixing on
its own.

---

## 6. What the profile layer owns on top of this

Nothing in §2–§4 changes when `fhir-profiling-and-extensibility-strategy.md` gets built — this
table is already the "always-true floor" every profile layer narrows from:

- `org-1` (name or identifier required) — a base-layer invariant in `fhir_profile`, evaluated
  in the service-layer pipeline before `organization`/`organization_identifier` rows are
  written, not a column constraint (principle 2).
- A hospital requiring `name`, a country mandating `Organization.type`, a clinic adding a
  custom `extension` — all organization/country-layer `fhir_profile` rows narrowing this same
  table's columns, with the write-time pipeline rejecting anything that violates them. The
  base table never needs to change when a new country or organization profile is added.

---

## 7. Indexing

| Index | On | Why |
|---|---|---|
| `organization_id` (unique) | `organization` | Public ID lookup — already the pattern everywhere |
| `tenant_id` | `organization` and every child table | Tenant-scoping — every list/search query filters on this first |
| `partof_id` | `organization` | No FK (§5), but still indexed — "find all children of this org" is a real query even without DB-enforced integrity |
| `created_at`, `updated_at` | `organization` | Already offered as sort options in list endpoints; the earlier scalability report found these unindexed in the current schema — fixed here from the start, not retrofitted |
| `organization_pk` (FK) | every child table | Standard FK index, needed for both the join and `ON DELETE` cascade performance |
| `assigner_id` | `organization_identifier` | No FK (§5), indexed for the same lookup reason as `partof_id` |

No trigram/GIN indexes proposed here speculatively — per the earlier scalability report,
add them when a genuine uncorrelated full-text search feature exists, not ahead of one.

---

## 8. Multi-tenancy & audit, restated plainly

- `tenant_id`: tenant-scoping value from the verified JWT's `activeOrganizationId`. Never a FHIR
  field, never serialized into `to_fhir_organization()`'s output. Renamed from this project's
  existing `org_id` — see principle 5.
- `created_by`/`updated_by`: verified JWT `sub`. Same — infrastructure, not spec content.
- No `user_id` at all — Organization is a shared tenant-level entity, not scoped to an
  individual end-user, matching this project's existing documented reasoning for the six
  resources in this category.

---

## 9. What's different from the current `app/models/organization/` code, named explicitly

| Area | Current code | This design |
|---|---|---|
| `active` | Already fixed to nullable, no default (this session) | Same — confirms that fix was correct |
| `name` | Already fixed to nullable (this session) | Same — confirms that fix was correct |
| `identifier (system, value)` uniqueness | Already dropped entirely (this session) | Same conclusion, arrived at independently from first principles |
| `partOf` / `Identifier.assigner` | Flattened `type`/`id`/`display`/`identifier`-fallback, no FK, `id` stores the public `organization_id` | **Same shape, confirmed correct after a real FK was tried and reverted** (§5) — the one actual addition is the raw `partof_reference`/`assigner_reference` string column, which the current code doesn't have |
| "at least one of reference/identifier/display" (`Reference`'s own invariant) | Not enforced anywhere | **`CHECK` constraints**, new — found while working through the `partOf`/`assigner` design, see §5 |
| Child-table parent-FK naming (`organization_id`) | Same name as the public `organization_id` column — ambiguous | Renamed to `organization_pk` everywhere — see principle 4 |
| `org-2`/`org-3` (no `home` use) | Not enforced anywhere | **`CHECK` constraints** on `organization_address.use` / `organization_telecom.use` |
| `extension` | Doesn't exist | New `JSONB` column on `organization`, present from day one |
| `organization_endpoint` uniqueness | `UNIQUE(organization_id, reference_type, reference_id)` | Dropped — not a spec requirement (principle 1) |
| `created_at`/`updated_at` indexes | Not indexed | Indexed |
| Enum audit (`type`, `contact.purpose`) | Already plain `String` (correct) | Confirmed correct, with the exact spec binding strength now documented inline rather than assumed |

Worth being honest about what this exercise actually found, not just what changed: `active`/
`name`/identifier-uniqueness were independently re-derived from spec-first reasoning, matching
conclusions the earlier incremental pass reached from auditing the existing code — a good sign
neither pass was guessing. `partOf`/`assigner`'s flattened, no-FK, public-ID-storing shape —
after a real FK was proposed, revised, and ultimately reverted across §5's three iterations —
turned out to already match what the current code does. The genuinely new, net material from
this pass is narrower than it looked partway through: the raw `{prefix}_reference` string
column, the `Reference`-shape and `org-2`/`org-3` `CHECK` constraints, the `organization_pk`
rename, and the `extension` column.

**On getting from here to there:** this report is a target shape, not a migration plan. The
two genuinely new columns (`partof_reference`/`assigner_reference`) are additive and nullable
— no backfill is strictly required to add them. But enabling
`ck_organization_partof_resolved_has_reference`/`..._assigner_resolved_has_reference`
afterward needs care: any existing row with `partof_id`/`assigner_id` already set (which the
current code allows, since it never had this column to populate) would violate a freshly
added `CHECK` immediately. The safe sequence is: add the columns, backfill
`partof_reference`/`assigner_reference` for existing rows that have `partof_id`/`assigner_id`
set (`f"Organization/{partof_id}"` is a reasonable default, matching this project's own public
reference-string format), *then* add the `CHECK` constraints — or add them `NOT VALID` first
and `VALIDATE CONSTRAINT` once the backfill is confirmed clean. The `organization_pk` rename
on every child table is a plain column rename (`ALTER TABLE ... RENAME COLUMN`), no type or
value change, no backfill needed.

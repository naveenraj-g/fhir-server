# Scalability & performance analysis — the 8 JWT/RBAC-rolled-out resources

**Scope.** This is a query-architecture and schema-design review, not a FHIR-spec-fidelity
review (see [`production-readiness-checklist.md`](./production-readiness-checklist.md) for
that angle). It covers Patient, Practitioner, Organization, Location, HealthcareService,
PractitionerRole, Schedule, and Slot — the resources that got the new flattened-reference
schema treatment — and contrasts them with the ~27 legacy resources where relevant. Every
finding below cites the actual file/line it was verified against; nothing here is generic
advice.

**Verdict up front: no, not production-ready as-is for real multi-tenant load.** The
relational, hand-normalized approach itself is correct (see the parent
[README](./README.md)) and several parts of the query layer are genuinely well engineered
(§2). But there is one confirmed data-corruption bug that will fire in ordinary multi-tenant
usage (§1.1), one confirmed orphaned-data bug (§1.2), and several designs that will degrade
predictably, not hypothetically, as row counts and concurrency grow (§1.3–§1.7). None of
these require abandoning the architecture — they're fixable within it.

---

## 1. Findings, ranked by severity

### 1.1 — CRITICAL: identifier uniqueness is global, not per-tenant

Every one of the 8 resources' `identifier` child table declares:

```python
UniqueConstraint("system", "value", name="uq_patient_identifier_system_value")
```

with no `org_id` in the constraint — verified identically (only the table name changes) in:

- `app/models/patient/identifier.py:23`
- `app/models/location/identifier.py:33`
- `app/models/schedule/identifier.py:27`
- `app/models/slot/identifier.py:27`
- `app/models/organization/identifier.py:25-27`
- `app/models/practitioner/identifier.py:23-25`
- `app/models/healthcare_service/identifier.py:27-29`
- `app/models/practitioner_role/identifier.py:27-29`

Every one of these same tables also carries an `org_id` column (e.g.
`app/models/patient/identifier.py:30`) — it just isn't part of the constraint. That column's
entire purpose in this codebase is tenant isolation (see `CLAUDE.md`'s Multi-Tenancy
section), and this is the one place it's silently not enforced.

**Why this breaks in production, not in a demo:** two different organizations independently
assigning the same identifier `system` (a URI they don't control the uniqueness of — e.g. a
shared national identifier scheme, or simply both orgs using an internal MRN scheme with
overlapping sequential values) will hit a Postgres unique-violation the moment the second
org's value collides with the first's. This isn't a rare edge case — it's the *default*
outcome once you have more than a handful of tenants using human-readable or sequential
identifier values, which is normal for MRNs.

**Fix:** every one of these 8 constraints should be `UniqueConstraint("org_id", "system",
"value", ...)`. This is a migration + constraint rename, no data model change.

### 1.2 — CRITICAL: no referential integrity and no orphan prevention on cross-resource references

This is the concern you raised, and it's real — but the nuance matters for the fix.

**Confirmed by design, not oversight, for polymorphic references.** `Encounter.subject`,
`Observation.subject`, `Condition.subject`, etc. use `subject_type` + `subject_id`
(`app/models/encounter/encounter.py:71-75`, `app/models/observation/observation.py:66-70`)
because FHIR itself allows `Reference(Patient | Group | ...)` — a single physical
`ForeignKey` genuinely cannot target more than one table. This part is correct and standard
for polymorphic associations in a relational schema; don't "fix" it.

**Not confirmed as necessary for single-target references — and this is where the new
resources diverge from the legacy ones inconsistently.** `Patient.managingOrganization` is
`Reference(Organization)` — FHIR only ever allows one target type here, confirmed by
`OrganizationReferenceType` having exactly one member (`app/models/enums.py:12-17`). A real
`ForeignKey("organization.id")` was entirely possible. Compare:

- **Legacy `Encounter.serviceProvider`** (same "Reference(Organization) only" semantics):
  `service_provider_id = Column(Integer, ForeignKey("organization.id"), ...)` —
  `app/models/encounter/encounter.py:98`. Real FK, DB-enforced.
- **New `Patient.managingOrganization`** (identical semantics): `managing_organization_id =
  Column(BigInteger, nullable=True, index=True)` — `app/models/patient/core.py:82`. No FK at
  all, despite being indexed.

So the 8 reworked resources didn't just lose FKs where they were architecturally
impossible (polymorphic refs) — they lost them even where the legacy resources still have
them, for the sake of a uniform "flattened reference" convention. That convention is the
right one for `RESOURCE_REGISTRY`-style generic write-time validation across many resource
types (`app/core/reference_resolver.py`) — but it costs you every safety net a real FK gives
for free: no `ON DELETE RESTRICT`/`CASCADE`, no orphan prevention, no consistency check
outside of the moment of write.

**Proven, not theoretical — orphaning is one API call away.**
`OrganizationRepository.delete()` (`app/repository/organization/core.py:272-286`) does
exactly this and nothing else:

```python
org = (await session.execute(stmt)).scalars().first()
await session.delete(org)
await session.commit()
```

No check for any Location/HealthcareService/Patient/PractitionerRole currently pointing at
this organization via `managing_organization_id`/`organization_id`/etc. Delete an
Organization that a dozen Locations reference, and every one of those Locations now carries
a `managing_organization_id` pointing at a row that no longer exists — silently. The next
read that tries to resolve/display that reference gets a dangling ID with no error, no 404,
no signal that anything is wrong, until someone notices the organization name is missing.

**Fix, in order of effort:**
1. **Cheapest, do this regardless:** add a pre-delete existence check for the highest-traffic
   reverse references (Organization is referenced by Location, HealthcareService,
   PractitionerRole, Patient, Practitioner, Schedule — audit which) and return 409 Conflict
   if any exist, the same way `check_tenant_ownership` already guards cross-org access.
2. **Better, if write volume allows it:** for the single-target references specifically
   (managingOrganization, partOf, serviceProvider-equivalents — not the genuinely polymorphic
   ones), use real FKs like the legacy resources already do. You lose nothing from
   `RESOURCE_REGISTRY`'s generic validation (it can stay as the *write-time* semantic check
   for new/changed references) and gain `ON DELETE RESTRICT` as a last-resort DB-level
   guarantee that can never drift out of sync with application code.

### 1.3 — HIGH: multi-tenant list/search columns have no composite index matching actual query shape

Confirmed on `PatientModel` (`app/models/patient/core.py:38-49`): `org_id` has its own
single-column index, `user_id` has its own single-column index, and there's a composite
**unique** constraint on `(user_id, org_id)` — which, being unique, also functions as an
index, but with `user_id` as the leading column. Every list/search query
(`app/repository/patient/core.py:377+`) filters by `org_id` first (tenant scoping) and only
sometimes by `user_id`. A composite index leading with `org_id` (the column present on
*every* query) rather than `user_id` (present only on `/me`) would let the planner use one
index-only scan for the common case instead of combining two single-column indexes via a
bitmap AND, which is what happens today. Same shape likely repeats across the other 7
resources — worth an index audit against actual `WHERE` clauses, not just "does a column
have *an* index."

### 1.4 — MEDIUM: `pg_trgm` is enabled but nothing uses it

`app/core/database.py` runs `CREATE EXTENSION IF NOT EXISTS pg_trgm` on every startup, but a
full repo search (`grep -rn "gin_trgm_ops\|postgresql_using=.gin"`) finds **zero** GIN
trigram indexes anywhere in `migrations/`. Every substring search —
`PatientName.family.ilike(f"%{family}%")`, `PatientAddress.city.ilike(...)`, etc.
(`app/repository/patient/core.py:182-332`) — has no index that can accelerate a
leading-wildcard `ILIKE`.

**This is currently masked, not absent, as a problem.** These filters go through
`apply_child_exists_filter` (`app/core/filters.py:149-164`), which correctly builds a
*correlated* `EXISTS` subquery scoped to `ChildModel.patient_id == PatientModel.id` — so the
`ILIKE` only ever runs against the handful of name/address rows belonging to one candidate
patient at a time, not the whole table. That's the right pattern and it's why this isn't an
active incident today.

**Where it stops being masked:** the day anyone adds a *global* text search (search across
all patients' names/addresses directly, not correlated per-candidate-row — e.g. a
typeahead/autocomplete feature, or a "find any patient matching X across the org" query that
isn't naturally bounded per-row first), this becomes a full sequential scan with `ILIKE`, and
`pg_trgm` is exactly the tool for that case — it's just not wired up. Either add the GIN
indexes now (cheap, and they'll be needed eventually) or drop the extension enablement and
document that it's deliberately not in use yet.

### 1.5 — MEDIUM: fixed per-request round-trip count scales with sub-resource-table count, not row count

`selectinload` is the correct choice over `joinedload` for one-to-many eager loading — it
avoids the classic N+1 problem *and* avoids join-based row multiplication that would corrupt
`LIMIT`/`OFFSET` pagination. Both are done right here. But it has its own cost: one
additional query *per relationship*, every single request, regardless of page size (a
`selectinload` on a 50-row page issues one `WHERE parent_id IN (...50 ids...)` query per
relationship — cheap per-query, but still one full round trip each).

Verified relationship counts (`grep -c "selectinload("` on each resource's `_shared.py`):

| Resource | `selectinload()` calls | Queries per single GET (1 main + N) |
|---|---|---|
| HealthcareService | 16 | **17** |
| Patient | 10 (11 incl. nested contacts) | **11-12** |
| PractitionerRole | 9 | **10** |
| Organization | 7 | **8** |
| Location | 6 | **7** |
| Schedule | 5 | **6** |

A single `GET /healthcare-services/{id}` costs 17 sequential round trips to the database
before the connection pool can be reused for the next request. At real concurrency, this is
where connection pool sizing (`app/core/config.py`'s new `DatabaseConfig` —
`pool_size`/`max_overflow`, previously hardcoded to SQLAlchemy's defaults of 5/10 with no way
to tune it — see this session's fix) directly determines your request throughput ceiling: 17
round trips per request means each in-flight `HealthcareService` request holds a pooled
connection roughly 17x longer (in round-trip count, not necessarily wall time, since these
are small indexed lookups) than a single-query endpoint would. This isn't a bug, but it is a
number worth knowing before you decide what `pool_size` a production deployment actually
needs, and it means DB round-trip latency (network distance to Postgres, not just query
plan cost) matters far more here than in a typical single-join CRUD app.

### 1.6 — MEDIUM: `OFFSET`/`LIMIT` pagination over unindexed sort columns

`_SORTABLE_FIELDS` for Patient (`app/repository/patient/_shared.py:27-33`) allows sorting by
`birth_date`, `created_at`, `updated_at`, `gender` — none of which has an index (only
`patient_id`, the default/fallback sort, is indexed via its `unique=True` constraint). Two
compounding issues for the "bulk browsing / patient history" scenario you described:

1. **Every non-default sort requires a full sort operation** (`ORDER BY created_at DESC`
   with no supporting index means Postgres sorts the whole filtered result set in memory or
   on disk, every request).
2. **`OFFSET` pagination degrades linearly with page depth** regardless of indexing — this is
   a known Postgres limitation, not specific to this codebase, but it means "page 200 of
   results" (a real pattern for bulk data review/export workflows) does `O(offset)` work to
   discard the skipped rows every single time, on every single request, forever.

**Fix:** add indexes on `created_at`/`updated_at` for the columns actually offered as sort
options (cheap, standalone migration). For the deep-pagination problem specifically, the
durable fix is keyset/cursor pagination (`WHERE (created_at, patient_id) < (last_seen_at,
last_seen_id) ORDER BY ... LIMIT n`) instead of `OFFSET` for any endpoint expected to be
paged deeply — this is a breaking API change to the pagination contract, so it's a "plan for
it," not a "just add an index" fix. `total_mode=none` (already implemented, see §2) is the
right escape hatch in the meantime for callers who don't need an exact count.

### 1.7 — LOW/MEDIUM: sequential, per-item reference validation on nested writes

`ScheduleRepository.create_full` (`app/repository/schedule/full.py:53-60`) loops over
`payload.identifier` and calls `await _validate_reference(...)` **inside the loop**, once per
identifier — a Schedule created with 5 identifiers, each with an `assigner` reference, does 5
sequential `SELECT EXISTS(...)` round trips before a single row is inserted. This is the same
pattern (verified) for `_validate_actor_reference` on Schedule's required 1..* `actor` list.
Individually each check is a cheap indexed lookup; the cost is the round-trip count under
write-heavy bulk-import scenarios, not the query cost itself. A batched existence check
(`WHERE (type, id) IN (...)` collecting all references up front, one query instead of N) would
remove this without changing behavior. Lower priority than §1.1/§1.2, but exactly the kind of
thing that shows up as "why is bulk import slow" once someone benchmarks it.

### 1.8 — VERIFY: integer-width mismatch between legacy FKs and reworked-resource PKs

`TaskModel.location_id` is declared `Column(Integer, ForeignKey("location.id"), ...)`
(`app/models/task/task.py:159`), but `LocationModel.id` is `BigInteger`
(per `CLAUDE.md`'s Standard Columns rule, applied when Location was reworked). Postgres can
create `int4 → int8` foreign keys via an implicit cast, so this likely *works* today, but it
should be confirmed against the actual applied migration (not just the model declaration) —
and any *new* FK from a legacy `Integer`-PK table into any of the 8 reworked (`BigInteger`)
tables should be written as `BigInteger` from the start to avoid relying on that implicit
cast at all.

---

## 2. What's already done right — don't change these

It's worth being explicit about this so a future refactor doesn't "fix" things that aren't
broken:

- **`BigInteger` PKs + per-resource Postgres sequences with fixed starting blocks**
  (`app/models/patient/core.py:20-22`, and the full allocation table in `CLAUDE.md`) is the
  correct choice for a system expected to scale — no UUID index bloat, no random insert
  pattern fragmenting the b-tree, and public IDs stay human-readable/sequential.
- **Correlated `EXISTS` subqueries for child-table search filters**
  (`app/core/filters.py:149-164`), not `JOIN`, is exactly right — it avoids the classic bug
  where a one-to-many join multiplies parent rows before `LIMIT`/`OFFSET` is applied,
  corrupting both pagination and any `COUNT(*)`.
- **The same filter set is applied identically to both the row query and the count query**
  (`app/repository/patient/core.py:412-414`'s comment states this explicitly, and the code
  does it) — this is the correct way to guarantee `total` never silently drifts from the
  actual filtered row count.
- **`total_mode: "none"` as an explicit escape hatch** from `COUNT(*)` on large filtered
  result sets (`app/core/pagination.py:35-42`) is a real scalability feature, already built
  — most CRUD scaffolds never bother to make counting optional.
- **`create_full`/`patch_full` are properly transactional** — one `session_factory()` block
  per operation, one flush, one commit, verified on `PatientRepository.create_full`
  (`app/repository/patient/full.py:34-51`) and `ScheduleRepository.create_full`
  (`app/repository/schedule/full.py:32-51`). A failure partway through a 9-sub-resource
  nested Patient create rolls back everything, not a partial write.
- **Session-per-operation** (`async with self.session_factory() as session:` everywhere) is
  the right call for an async codebase — no session held open across unrelated work, no
  accidental cross-request session sharing.
- **Query-level instrumentation from one place** (`app/core/database.py`'s
  `_install_query_listeners`) means every slow query across all ~35 resources is already
  visible via `db.slow_query` at the configured threshold — this report's findings are things
  that instrumentation *will* surface once there's real traffic, not blind spots in
  observability.
- **DB connection pool is now configurable** (`database.pool_size`/`max_overflow`/
  `pool_pre_ping`/`pool_recycle` in `configs/config.yaml`, wired into
  `create_async_engine()` this session) rather than silently stuck at SQLAlchemy's defaults
  — directly relevant to §1.5's round-trip-count finding, since pool sizing is the lever that
  determines how many of those multi-query requests can run concurrently.

---

## 3. Direct answer to "bulk operations, patient history, more joins"

Worth naming explicitly since it's what prompted this review:

- **"More joins" mostly doesn't happen the way you'd expect.** Cross-resource reads (e.g.
  "get everything for this patient": their Encounters, Observations, Conditions) are
  **polymorphic by FHIR design** (`subject_type`/`subject_id`), so this was never going to be
  a single SQL `JOIN` regardless of FK choice — it's inherently N separate typed queries, one
  per resource type, application-side. That part isn't a design flaw; it's what a
  polymorphic reference costs in any relational schema, FK or not.
- **Within one resource, "joins" are already avoided in favor of `selectinload`** — correctly
  for correctness (§2), at the cost of round-trip count scaling with sub-resource-table count
  (§1.5). For a resource like HealthcareService (17 queries per single fetch), that's the
  actual "join cost" hiding in this architecture, just paid as sequential round trips instead
  of a single wide join.
- **"Bulk operations" and "patient history" specifically stress the two weakest points found
  here**: deep `OFFSET` pagination over unindexed sort columns (§1.6) for history/browsing,
  and sequential per-item reference validation (§1.7) for bulk writes. Neither is a
  fundamental architecture problem — both are concrete, scoped fixes.
- **The FK question you raised is real, but narrower than "no FKs anywhere."** Polymorphic
  references never had FKs and shouldn't. Single-target references on the 8 reworked
  resources dropped FKs that the legacy resources still have for the identical semantic
  (§1.2) — that's the actual gap, and it's fixable resource-by-resource without touching the
  polymorphic ones.

## 4. Suggested order of work

1. **Now — data-corrupting, cheap to fix:** §1.1 (add `org_id` to the 8 identifier unique
   constraints). This is a ticking bug, not a hardening item.
2. **Now — data-integrity, moderate effort:** §1.2's cheap option (pre-delete reference
   checks on Organization/Location/etc. before allowing delete).
3. **Next:** §1.3 (composite tenant-scoping indexes matched to real query shape), §1.6's
   indexing half (index the actually-offered sort columns).
4. **Next, if bulk-import is an active use case:** §1.7 (batch reference validation).
5. **Later, as a deliberate architecture decision:** §1.2's FK option for single-target
   references (bigger, resource-by-resource migration work, best done alongside whatever
   resource is next in line for rework anyway).
6. **Later, once real page-depth usage is measured:** §1.6's keyset-pagination fix — this is
   an API contract change, don't do it speculatively.
7. **Opportunistic:** §1.4 (either add the GIN indexes `pg_trgm` implies, or stop enabling
   the extension), §1.8 (confirm the Integer→BigInteger FK cast is actually fine in the
   applied migration).

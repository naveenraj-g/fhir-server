# Org Concepts and Display Overrides

**What this file is:** the implementation of the two org-scoped
customization features introduced conceptually at the end of
[00-what-is-terminology.md](00-what-is-terminology.md) — one lets a
hospital network ("org") invent a brand-new code of its own, the other
lets it relabel the display text of a code that already exists
canonically. They're easy to confuse because they look almost identical
at the API level; this file is specifically about telling them apart.

Two org-scoped customization mechanisms that look similar at the router
layer (both are five-endpoint CRUD-ish surfaces, both require
`_require_org_id(request)`, both write to `TerminologyAuditLog`) but do
genuinely different things to genuinely different data. Confusing the two
is the easiest mistake to make reading this subsystem quickly — this file
exists specifically to keep them straight.

## Org Concepts — inventing a brand-new code

An org-added **`TerminologyConcept`** row, with `org_id` set. This is a new
code that doesn't exist in the canonical vocabulary — the org is extending
a CodeSystem with its own local concept. Enabled by the data model's own
partial unique index design (see
[01-data-model.md](01-data-model.md)): the same `(code_system_id, code)`
pair can exist once canonically (`org_id IS NULL`) and once more per org
(`org_id IS NOT NULL`), so an org can mint a code that happens to collide
with a canonical one without conflicting with it, and two different orgs
can each mint their own version of the same code independently.

`app/repository/terminology/org_concepts.py` (192 lines):

- `create_org_concept(...)` — inserts the `TerminologyConcept` row, flushes
  to get its id, updates `search_vector` via the same raw
  `to_tsvector(...)` SQL the bulk loaders use, then logs a
  `TerminologyAuditLog` row with `action="org_concept.created"`.
- `get_org_concept`, `list_org_concepts` (filterable by
  `code_system_url` and a full-text `q`).
- `patch_org_concept` — captures the old `display`/`definition` **before**
  mutating, so the audit row can carry both old and new values.
- `delete_org_concept` — logs `action="org_concept.deleted"` with the old
  values **before** the delete executes (the audit row has to capture that
  state before it's gone — this is also exactly why
  `TerminologyAuditLog`'s FKs are `ondelete="SET NULL"` rather than
  `CASCADE`: the row being deleted can disappear, but the audit record of
  its deletion must not).

Router: `app/routers/terminology/org_concepts.py` (153 lines). `POST
/org-concepts` returns 201, with 403 (no org on the request), 404 (target
code system doesn't exist), and 409 (this org already has a concept at this
`(system, code)`) all documented directly in the route's `responses=`.

## Display Overrides — relabeling a code that already exists

A **`TerminologyDisplayOverride`** row — a per-org override of the
*display text* for an existing, canonical concept. It does not create a
new code; it changes how an existing code's `display`/`definition` render
for that specific org. `UniqueConstraint(concept_id, org_id)` — one
override per concept per org.

`app/repository/terminology/display_overrides.py` (138 lines) mirrors
`org_concepts.py`'s exact shape (`create_`/`get_`/`patch_`/`delete_`/`list_`,
each logging to `TerminologyAuditLog` with `display_override_id` set
instead of `concept_id` as the primary subject reference) — but the create
path is different in one important way:

`create_display_override(system, code, org_id, display, definition, ...)`
— **the caller supplies `(system, code)`, not a concept id.** The service
layer (`app/services/terminology/display_overrides.py`, 59 lines) resolves
that pair via `lookup_concept(system, code)` first and returns `None` if it
doesn't resolve — **an override cannot invent a code.** If the concept
doesn't already exist canonically, there's nothing to override; the caller
needs the org-concepts path instead to add a genuinely new code.

Router: `app/routers/terminology/display_overrides.py` (144 lines), same
403/404 shape as org-concepts.

## Response shaping — where the distinction shows up again

`app/services/terminology/_shared.py`'s `_display_override_response(override,
concept, cs)` pulls `code`/`system`/`system_name` from the **joined
concept + code system** (the override has no code/system of its own — it's
not a code, it's a label on one) but `display`/`definition`/`org_id`/
`user_id`/`created_at` from the **override row itself**. Compare this to
`_org_concept_response(concept, cs)`, which pulls everything — including
`display`/`definition` — straight from the concept, because for an
org-concept the concept *is* the content, not just an identity anchor for
someone else's content.

## Shared audit trail

Both mechanisms log into the same `TerminologyAuditLog` table
(`app/repository/terminology/audit_log.py`, 32 lines, read side only:
`list_audit_log(action, performed_by, concept_id, limit, offset)`). Events
observed in the two create/patch/delete repository files:
`org_concept.created`, `org_concept.updated`, `org_concept.deleted`, and the
equivalent `display_override.*` trio. Filtering by `concept_id` returns
audit history that can span both mechanisms for the same underlying
concept (an org might both override a canonical concept's display *and*
separately own an unrelated org-added concept — these are independent
rows, independent audit trails, joined only by sharing the audit table and,
for display-overrides, by both referencing the same canonical `concept_id`).

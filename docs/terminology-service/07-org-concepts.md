# Org Concepts

**What this file is:** the implementation of this project's one org-scoped
customization feature introduced conceptually at the end of
[00-what-is-terminology.md](00-what-is-terminology.md) — letting a
hospital network ("org") invent a brand-new code of its own, scoped to
that org, without touching the canonical, standards-body-maintained
vocabulary.

A per-org *display override* (relabeling an existing canonical code's
display text without inventing a new one) was built alongside this
feature at one point, then removed before it shipped — see
[01-data-model.md](01-data-model.md) and
[08-fhir-r4-standard-compliance-gap-analysis.md](08-fhir-r4-standard-compliance-gap-analysis.md)
for why (the terminology subsystem is being rebuilt to follow the real
FHIR R4 terminology module first; a half-built local feature isn't
carried forward alongside that rebuild). It goes back on the list once
that's settled — this file only covers what's actually here now.

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

`app/repository/terminology/org_concepts.py`:

- `create_org_concept(...)` — inserts the `TerminologyConcept` row, flushes
  to get its id, then updates `search_vector` via the same raw
  `to_tsvector(...)` SQL the bulk loaders use.
- `get_org_concept`, `list_org_concepts` (filterable by
  `code_system_url` and a full-text `q`).
- `patch_org_concept`, `delete_org_concept`.

Router: `app/routers/terminology/org_concepts.py`. `POST
/org-concepts` returns 201, with 403 (no org on the request), 404 (target
code system doesn't exist), and 409 (this org already has a concept at this
`(system, code)`) all documented directly in the route's `responses=`.

## Response shaping

`_org_concept_response(concept, cs)` (`app/services/terminology/_shared.py`)
pulls everything — including `display`/`definition` — straight from the
concept, because for an org-concept the concept *is* the content.

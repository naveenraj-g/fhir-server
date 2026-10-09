# Repository and Service Layers

**What this file is:** how the tables from
[01-data-model.md](01-data-model.md) actually get read and written in
code. "Repository" is this codebase's name for the layer that talks
directly to the database; "service" is a thin layer on top of it that
shapes the raw rows into the response format an API caller gets back (see
the root `CLAUDE.md`'s "Layered Architecture" section for why the split
exists at all, across every resource in this server, not just
terminology). If a term here — CodeSystem, Concept, ValueSet, binding,
ConceptMap, org concept, display override — is unfamiliar, see
[00-what-is-terminology.md](00-what-is-terminology.md) first.

Both layers follow the same package-per-resource-but-split-into-mixins
pattern the root `CLAUDE.md` describes for Patient/Practitioner/etc. (see
"Schema Conventions" / `/split-resource-package`), except terminology was
*built* this way from the start rather than split out after growing large.

## Repository: `app/repository/terminology/`

`__init__.py` composes `TerminologyRepository` via multiple inheritance, in
this exact order:

```python
class TerminologyRepository(
    _CodeSystemsMixin, _ValueSetsMixin, _ConceptsMixin, _ValidationMixin,
    _ConceptMapsMixin, _OrgConceptsMixin, _DisplayOverridesMixin,
    _AuditLogMixin, BaseRepository,
):
```

`BaseRepository` (`app/repository/base.py`, 63 lines) sits last in the MRO
and supplies `__init__(session_factory)` plus a generic
`_execute_paginated(session, base_stmt, count_stmt, *, sort_column,
sort_desc, limit, offset, total_mode="accurate")` helper.

**None of the terminology mixins actually call `_execute_paginated()`.**
Every one of `list_value_sets`, `search_concepts`, `list_org_concepts`,
`list_display_overrides`, `list_audit_log`, and `list_concept_maps` inlines
its own count-query + rows-query pair inside one `async with
self.session_factory() as session:` block instead. Worth knowing if you're
extending one of these methods: there's no shared pagination helper actually
wired up in this subsystem despite one existing on the base class — follow
the inline pattern the sibling methods in the same file already use, don't
go looking for a `_execute_paginated()` call to copy.

### `code_systems.py` (24 lines)
`list_code_systems()`, `get_code_system_by_url(url)`. The two simplest
methods in the package — no filtering, no pagination.

### `value_sets.py` (75 lines)
- `list_value_sets(q, limit, offset)` — `ILIKE` across `name`, `title`,
  `canonical_url`.
- `get_value_set(value_set_id)`.
- `expand_value_set(value_set_id, q, limit, offset)` — joins
  `TerminologyValueSetConcept` → `TerminologyConcept` → `TerminologyCodeSystem`,
  with an optional trigram `ILIKE` filter on `display`. This is the "give me
  every concept actually in this ValueSet" operation — what FHIR calls
  `$expand`.

### `concepts.py` (65 lines)
- `search_concepts(q, system, limit, offset)` — ranks by Postgres trigram
  `similarity()`, not an embedding/vector search (see
  [01](01-data-model.md)'s note on `TerminologyConceptEmbedding` being
  unused for ranking today).
- `lookup_concept(system, code)` — exact `(canonical_url, code)` lookup,
  the building block `validate()`/`translate()` both call into (see
  [06](06-validation-and-field-bindings.md)).

### `validation.py` (73 lines)
- `get_field_binding(resource_type, field_name)` — the
  `TerminologyFieldBinding` row lookup.
- `lookup_concept_in_value_set(value_set_id, system, code)` — returns
  `(code_system, concept, in_value_set: bool)`, i.e. it tells you both
  whether the concept exists at all *and* whether it's actually a member of
  that specific ValueSet, in one call.
- `get_translations(source_concept_id, target_system)` — the
  `TerminologyConceptMap` lookup `translate()` uses.

### `concept_maps.py` (64 lines)
`list_concept_maps(source_system, target_system, limit, offset)` uses four
SQLAlchemy `aliased()` instances to self-join `ConceptMap` → `Concept` →
`CodeSystem` twice over (once for the source side, once for the target
side) — necessary because a ConceptMap row references two concepts that may
belong to two different code systems, and the row query needs both systems'
`canonical_url`/`name` in one shot.

> **Fixed bug (previously shipped):** the `count_stmt` in
> `list_concept_maps` used to be a bare
> `select(func.count()).select_from(TerminologyConceptMap)`, which did
> **not** apply the `source_system`/`target_system` `WHERE` filters that
> the row-fetching `stmt` applies — calling this with either filter set
> returned a `total` that counted *all* concept maps, not just the
> filtered set. Fixed by running the count over the same filtered/joined
> `stmt`'s subquery instead of a fresh bare count, so `total` now reflects
> exactly the rows the filters actually matched.

`add_concept_map(source_concept_id, target_concept_id, mapping_type,
confidence)` returns a bool. It does its own existence pre-check (a `COUNT`
query) rather than relying purely on `ON CONFLICT` — the model's
`UniqueConstraint(source_concept_id, target_concept_id, mapping_type)` is
still the actual DB-level guarantee, the pre-check just lets the method
return `False` cleanly on a duplicate instead of raising an integrity error.

### `org_concepts.py` (192 lines) and `display_overrides.py` (138 lines)
Structurally identical five-method shape (`create_`, `get_`, `patch_`,
`delete_`, `list_`), each logging a `TerminologyAuditLog` row on every
mutation. Covered in full in
[07-org-concepts-and-display-overrides.md](07-org-concepts-and-display-overrides.md)
since the interesting content here is the *distinction* between the two,
not either one in isolation.

### `audit_log.py` (32 lines)
`list_audit_log(action, performed_by, concept_id, limit, offset)` — the one
read path over the table both of the above write to.

## Service: `app/services/terminology/`

Same mixin-composition pattern, same ordering concept, composed in
`__init__.py` as:

```python
class TerminologyService(
    _CoreMixin, _CodeSystemsMixin, _ValueSetsMixin, _ConceptsMixin,
    _ValidationMixin, _ConceptMapsMixin, _OrgConceptsMixin,
    _DisplayOverridesMixin, _AuditLogMixin,
):
```

`_CoreMixin.__init__(self, repository: TerminologyRepository)` just stores
`self.repository` — its own docstring says there's no single primary
resource row here, so there's no "core" business logic to host, unlike
every other resource's `_CoreMixin`.

`_shared.py` (89 lines) holds the response-shaping helpers every other
service mixin calls into, so the FHIR-shape-vs-plain-shape logic lives in
one place:

- `_cs_response(cs)`, `_vs_response(vs)`, `_concept_response(concept, cs)`
- `_org_concept_response(concept, cs)` — same as `_concept_response` plus
  `user_id`/`org_id`/`created_at`.
- `_display_override_response(override, concept, cs)` — pulls
  `code`/`system`/`system_name` from the *joined concept + code system*, but
  `display`/`definition`/`org_id`/`user_id`/`created_at` from the override
  row itself. This split (identity fields from the concept, content fields
  from the override) is exactly the override/concept relationship
  [07](07-org-concepts-and-display-overrides.md) explains.

Every other service mixin (`code_systems.py`, `value_sets.py`,
`concepts.py`, `validation.py`, `concept_maps.py`, `audit_log.py`) is a thin
pass-through: call the matching repository method, wrap the result in the
matching Pydantic response schema from `app/schemas/terminology.py`
(29 schema classes total — see the schemas reference in
[03-api-routes.md](03-api-routes.md)). `validation.py` is the one service
mixin with real branching logic in it — see
[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md)
for `validate()`/`translate()`'s actual control flow.

# Data Model

**What this file is:** the database design for everything explained in
plain language in
[00-what-is-terminology.md](00-what-is-terminology.md) — every table that
stores a code system, a concept, a value set, a binding, a concept map, or
one of this project's org-scoped customizations, and exactly why each
constraint on each table exists. If you haven't read 00 yet, the terms
"CodeSystem," "Concept," "ValueSet," and "binding" below assume you already
know what they mean conceptually; this file is only about how they're
stored.

Source: `app/models/terminology/terminology.py`. All 9 tables
live here — the terminology subsystem doesn't follow the
one-package-per-resource model layout the rest of the codebase uses, since
there's no single "primary resource" to name a package after.

## `TerminologyCodeSystem`

One named vocabulary (LOINC, SNOMED CT, ICD-10-CM, a custom org vocabulary,
…). `canonical_url` is unique — this is the join key every loader and every
`ValueSet.compose.include[].system` resolves against, not the internal `id`.
`concepts` relationship cascades `delete-orphan`: deleting a CodeSystem row
deletes every Concept that belongs to it.

## `TerminologyConcept`

One code within exactly one CodeSystem. The interesting part is the two
**partial unique indexes**, both via SQLAlchemy's
`postgresql_where=text(...)`:

- `(code_system_id, code)` unique **where `org_id IS NULL`** — one canonical
  row per code, system-wide.
- `(code_system_id, code, org_id)` unique **where `org_id IS NOT NULL`** —
  the same `(system, code)` pair can additionally exist once *per org*, for
  org-added custom concepts (see
  [07-org-concepts.md](07-org-concepts.md)).

This is why `app/terminology/import_/base.py`'s bulk insert uses
`ON CONFLICT (code_system_id, code) WHERE org_id IS NULL DO NOTHING` — it has
to name the exact partial index, not just the column list, or Postgres can't
pick a matching index for the conflict target.

Other notable columns: self-referential `parent_concept_id` (nullable FK back
to this same table — used by the FHIR R4 loader's hierarchy, see
[05](05-seeding-and-external-loaders.md)), `search_vector` (`TSVECTOR`,
populated via raw `to_tsvector('english', ...)` SQL by every loader/writer,
never by SQLAlchemy/ORM-level computation). Relationships to synonyms,
translations, and embedding are all `cascade="all, delete-orphan"` —
deleting a Concept takes its synonyms/translations/embedding with it.

## `TerminologyConceptSynonym`

Alternate display strings for a concept (e.g. SNOMED's FSN vs. its
synonyms — see [05](05-seeding-and-external-loaders.md)). No unique
constraint beyond the FK — a concept can have arbitrarily many synonyms.

## `TerminologyConceptTranslation`

Cross-language display text for a concept. `UniqueConstraint(concept_id,
language_code)` — one translation per language per concept.

## `TerminologyRelationship`

A separate, explicit hierarchy/relationship table: `(parent_concept_id,
child_concept_id, relationship_type)`, `UniqueConstraint` on all three. This
is the mechanism SNOMED's IS-A hierarchy uses
(`app/terminology/import_/loaders/snomed.py`) — **not** the same mechanism as
`TerminologyConcept.parent_concept_id`, which is what the FHIR R4 loader uses
for nested `concept[]` hierarchies instead. Two different resources, two
different hierarchy representations; see
[05-seeding-and-external-loaders.md](05-seeding-and-external-loaders.md) for
why.

## `TerminologyValueSet`

A curated, named subset of concepts (can span multiple CodeSystems). Carries
its own `binding_strength` column. **This column is set by loader heuristics
only and is never read by `validate()`** — see
[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md)
for exactly what *is* read instead (`TerminologyFieldBinding.binding_strength`,
a different column on a different table). Don't assume this column does
anything at request-validation time; right now it's effectively descriptive
metadata about the ValueSet itself (the FHIR R4 loader sets it to
`"required"` when the source `ValueSet.immutable` flag is true, `"extensible"`
otherwise — see [05](05-seeding-and-external-loaders.md)).

## `TerminologyValueSetConcept`

The many-to-many join table between ValueSet and Concept.
`UniqueConstraint(value_set_id, concept_id)` — a concept can't be added to
the same ValueSet twice.

## `TerminologyFieldBinding`

Wires one `(resource_type, field_name)` pair to one governing ValueSet.
`UniqueConstraint(resource_type, field_name)` — exactly one binding per
field, which is also the `ON CONFLICT` target both seed scripts rely on (see
[05](05-seeding-and-external-loaders.md)). Owns its own
`binding_strength` and `multiple_allowed` columns — **this is the
binding_strength `validate()` actually enforces.**

## `TerminologyConceptEmbedding`

A `JSONB` float array per concept (vector embedding, presumably for semantic
search — nothing in the repository/service layer currently reads it for
ranking; `search_concepts()` ranks by trigram `similarity()` instead, see
[02](02-repository-and-service-layers.md)). The model's own docstring notes
a planned migration to a real `pgvector` column; as of this read, that
migration hasn't happened — it's still `JSONB`.

## `TerminologyConceptMap`

A separate, parallel translation layer from ValueSet/FieldBinding —
cross-system concept-to-concept mappings (`source_concept_id` →
`target_concept_id`, plus `mapping_type` and `confidence`).
`UniqueConstraint(source_concept_id, target_concept_id, mapping_type)`. Two
independent FK'd relationships to `TerminologyConcept`, each disambiguated
via SQLAlchemy's `foreign_keys=[...]` (both FKs point at the same table, so
the relationship direction has to be told explicitly which column to use).

## BigInteger / reference-style note

Every `id` and sequence-style column in this subsystem follows the same
`BigInteger` convention as the rest of the codebase (per the root
`CLAUDE.md`'s "FHIR DB Model Design" section). None of these tables use the
`{prefix}_type`/`{prefix}_id`/`{prefix}_display` flattened-reference
convention the auth-rollout resources use — every cross-table reference here
is a real `ForeignKey` to another terminology table's internal `id`, because
(unlike Appointment's polymorphic participant list, say) every reference in
this subsystem has a single, fixed target table.

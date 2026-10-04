# Cardinality and multiplicity

## `min` and `max`

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `min` | `0..1` | `unsignedInt` | The minimum number of times this element must appear. `0` = optional, `1`+ = required (at least that many). |
| `max` | `0..1` | `string` | The maximum number of times this element may appear — a literal number (`"1"`) or the literal string `"*"` meaning unbounded. It's a `string`, not an integer, specifically to accommodate `"*"`. |

Combined, these produce the `min..max` notation used throughout this entire documentation
folder and throughout `CLAUDE.md` (`0..1`, `0..*`, `1..1`, `1..*`). A few concrete readings:

- `0..1` — optional, at most one (a flat nullable column in this project's storage convention)
- `0..*` — optional, repeating (a child table)
- `1..1` — required, exactly one
- `1..*` — required, at least one, possibly more
- `0..0` — **forbidden**. A profile can legally set an inherited element's `max` to `0`, which
  means "this element, which the base type allowed, is not permitted at all under this
  profile." This is a real, named technique (sometimes called "zeroing out" an element) — see
  the narrowing rule below for why it's legal.

## `base.min` / `base.max`

Covered briefly in [`03-element-definition-core-fields.md`](03-element-definition-core-fields.md);
worth restating here since it's the field that makes the narrowing rule *checkable*. Every
`ElementDefinition` carries both its own, possibly-narrowed `min`/`max` **and** a `base.min`/
`base.max` recording what the cardinality was on the original, unprofiled definition. A profile
's own `min`/`max` should always be within `[base.min, base.max]` — never looser.

## The one rule the entire three-layer plan depends on

> **A profile can only make an inherited element *more* restrictive than its parent, never
> less.** A base element of `0..1` can become `0..0` or `1..1` under a profile, but never
> `0..*`. Whatever a child profile allows must already have been allowed by its parent.

This isn't a style convention — it's a structural requirement for the whole chain to be
meaningful. If a country profile could *widen* what base R4 allows, then "conforms to the
country profile" would no longer imply "conforms to base R4," and the entire idea of stacking
profiles (validate once per layer, cumulative) breaks down: you could end up with an instance
that's valid per the country profile but invalid per the base spec it's supposed to be built on
top of.

**Concretely, for this project:** `docs/architecture/fhir-profiling-and-extensibility-strategy.md`
(§1) already calls this out as the one rule that has to be enforced *mechanically*, not just
assumed — specifically because organization-level profiles in that design are meant to be
authored at runtime through a future admin surface, not reviewed by a human in a PR. Nothing
stops a tenant from accidentally trying to loosen a country-mandated `1..1` back down to `0..1`
unless something checks `new.min >= inherited.min` and `new.max <= inherited.max` (with `*`
treated as the largest possible value) at the moment a profile is *saved*, not just at
validation time.

## How cardinality drives this project's own storage shape

This is already a working rule in `CLAUDE.md`'s "FHIR DB Model Design" skill reference, and is
a direct, mechanical consequence of `max`:

| `max` | Storage shape | Example from this session's Organization work |
|---|---|---|
| `0..1` or `1..1` | A flat, nullable (or not) column on the parent table | `OrganizationModel.name`, `OrganizationModel.active` |
| `0..*` or `1..*` | A child table, FK back to the parent | `OrganizationIdentifier`, `OrganizationAddress`, and — the change made this session specifically because `CodeableConcept.coding` is `0..*`, not `0..1` — `OrganizationTypeCoding`/`OrganizationIdentifierTypeCoding`/`OrganizationContactPurposeCoding` |

The `min` half of cardinality (not `max`) is what `CLAUDE.md`'s Organization model docstring is
referring to when it says `org-1` ("name or identifier required") **can't** be a single-column
`NOT NULL` — `identifier` lives in a separate child table, so there's no one column a `NOT NULL`
constraint could even attach to. This is precisely the kind of rule a cardinality/`min` check
alone can't express either (it spans two different elements, `name` *or* `identifier`) — it's
an invariant, not a cardinality constraint. Covered in
[`06-constraints-and-invariants.md`](06-constraints-and-invariants.md).

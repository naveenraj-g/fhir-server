# Constraints and invariants

This is the mechanism behind `org-1`, `org-2`, and `org-3` — the three rules already discovered
and verified this session (`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s
§2 table calls these out explicitly as proof this project already needs this mechanism). This
file is also the direct spec grounding for `app/fhir/validation/base_r4.py` and for whatever
generalized invariant mechanism gets built per that architecture document's §3/§4.

## `ElementDefinition.constraint[]`

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `constraint.key` | `1..1` | `id` | A short, stable identifier for this specific rule (e.g. `"org-1"`). Referenced back by `ElementDefinition.condition` (see below) and used in error messages so a human can look the rule up. |
| `constraint.requirements` | `0..1` | `string` | Why this constraint is necessary or appropriate — the business/clinical justification, separate from the human-readable description of *what* it checks. |
| `constraint.severity` | `1..1` | `code` | `error \| warning` — see below. |
| `constraint.human` | `1..1` | `string` | A human-readable description of the rule, suitable for display in an error message — this is the exact text this project's own `OperationOutcome.issue[].diagnostics` should echo when a constraint fails. |
| `constraint.expression` | `0..1` | `string` | A **FHIRPath** boolean expression — the actual, machine-executable rule. See below. |
| `constraint.xpath` | `0..1` | `string` | The equivalent rule expressed in XPath, for XML-based tooling. Legacy; this project only ever handles JSON, so `xpath` is never relevant here. |
| `constraint.source` | `0..1` | `canonical` | The canonical URL of the `StructureDefinition` that originally introduced this constraint — lets a validator trace a failing rule back to which layer (base? country? org?) actually declared it. |

## `severity` — the two values, HL7's own definitions

| Code | Meaning |
|---|---|
| `error` | "If the constraint is violated, the resource is not conformant." The resource must be rejected. |
| `warning` | "If the constraint is violated, the resource is conformant, but it is not necessarily following best practice." The resource should still be accepted. |

**This project does not yet distinguish these two severities anywhere.** `app/fhir/validation/base_r4.py`
's `validate_base_r4()` currently treats every structural failure uniformly as a hard rejection
(422), because the structural rules it checks via `fhir.schema.json` don't carry a severity
concept at all — a JSON Schema validation failure is binary. Once real `constraint[]` entries
are evaluated (not just JSON Schema structure), `severity` becomes a real design decision: a
`warning`-level constraint violation should very likely be logged and allowed through, not
rejected with a 422 the way `org-1`/`org-2`/`org-3` (all `error`) should be. This is an open
item, not yet decided or implemented.

## `ElementDefinition.condition`

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `condition` | `0..*` | `id` | A list of `constraint.key` values from elsewhere in the same `StructureDefinition` that apply to *this* element. This is how a constraint's `key` (declared once, on whichever element the rule is most naturally attached to) gets cross-referenced from other elements the rule also concerns — e.g. a rule declared on the resource root might list affected child elements via their own `condition` entries pointing back at its `key`. Rarely populated in base R4; not used by `org-1`/`org-2`/`org-3`. |

## FHIRPath, briefly

`constraint.expression` is written in **FHIRPath** — a small path-navigation and expression
language purpose-built for FHIR, distinct from XPath or JSONPath. The subset actually used by
base R4's own invariants (verified empirically against the real spec data, not assumed) is
bounded and simple:

| Construct | Meaning | Used by |
|---|---|---|
| `<path>` | Navigate to a child element (e.g. `identifier`, `address.use`) | all three |
| `.count()` | Number of items at that path | `org-1` |
| `.exists()` | Whether any items exist at that path | common elsewhere in the base spec |
| `.empty()` | The inverse of `.exists()` | `org-2`, `org-3` |
| `.where(<condition>)` | Filter a repeating element to items matching a condition | `org-2`, `org-3` |
| `=` | Equality comparison | `org-2`, `org-3` (`use = 'home'`) |
| `+`, `>` | Arithmetic/comparison | `org-1` (`(identifier.count() + name.count()) > 0`) |

The full FHIRPath language is considerably larger (type checks via `is`/`as`, string/date
functions, `all()`, union `|`, and more) — but the three concrete rules this project has
actually verified so far don't need any of that. This is the empirical basis for
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s recommendation to reach for
an existing, maintained library (`fhirpathpy`) rather than hand-roll an evaluator — the subset
needed is small today, but there's no guarantee a future country/org-authored invariant won't
need more of the language, and a real library already covers all of it.

## Worked example, field by field: `org-1`

The actual, verified entry from HL7's own `StructureDefinition-Organization.json`:

```json
{
  "path": "Organization",
  "constraint": [
    {
      "key": "org-1",
      "severity": "error",
      "human": "The organization SHALL at least have a name or an identifier, and possibly more than one",
      "expression": "(identifier.count() + name.count()) > 0"
    }
  ]
}
```

Reading every field: this rule is attached to the `Organization` element itself (the resource
root, `path: "Organization"` with no dot) — meaning it's evaluated against the whole resource
instance, not one sub-element. Its `key` is `org-1`. Its `severity` is `error` — a violation
makes the instance non-conformant, full stop. Its `human` text is exactly what should appear in
a rejection message. Its `expression` is FHIRPath that counts how many `identifier` entries
plus how many `name` values exist, and requires that sum to be greater than zero — i.e., at
least one of the two must be present. There is no `xpath` entry (JSON-only tooling, as is
standard for anything authored against R4), and no `source` (this is the base spec itself, not
a derived profile).

`org-2` and `org-3` are structurally identical, just attached to `Organization.address` and
`Organization.telecom` respectively, with `expression: "where(use = 'home').empty()"` — "no
entry in this repeating list has `use = 'home'`."

## How this maps to what's already built

- `app/fhir/validation/base_r4.py`'s `validate_base_r4()` validates structure (required fields,
  cardinality, primitive formats, required-binding enums) via `fhir.schema.json` — **it does
  not evaluate `constraint[]`/invariants at all**, confirmed empirically earlier this session
  (`fhir.schema.json` has zero `anyOf`/conditional logic expressing invariants across 60,000+
  lines). This file's mechanism is the piece that's still missing.
- `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §2–§4 already designs
  where this goes: invariants become rows in the planned `fhir_profile.structure.invariants[]`
  JSONB array (§3), evaluated by a `validate_invariants(payload, chain)` pipeline step (§4) —
  `org-1` becomes simply the base profile's own invariant, evaluated the same way as every
  other layer's, rather than a one-off hand-written Pydantic validator.

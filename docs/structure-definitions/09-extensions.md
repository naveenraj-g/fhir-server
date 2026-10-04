# Extensions

Spec: [hl7.org/fhir/R4/extensibility.html](https://www.hl7.org/fhir/R4/extensibility.html)
(referenced, not fetched this round — the structural facts below come from `Extension`'s own
`StructureDefinition`, pulled from the same local `profiles-types.json` used throughout this
folder).

## An extension is just another StructureDefinition

As established in [`01-what-is-a-structuredefinition.md`](01-what-is-a-structuredefinition.md),
defining an extension is the *same* mechanism as defining a profile — `kind: "complex-type"`,
`type: "Extension"`, `derivation: "constraint"`, `baseDefinition` pointing at the base
`Extension` type itself. The extension's own canonical `url` (from
[`02-structuredefinition-root-fields.md`](02-structuredefinition-root-fields.md)) is what
instance data references — it's a globally unique identifier for the extension, not a
database foreign key.

## `Extension`'s own fields (the shape of the *value*, not the definition)

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `url` | `1..1` | string (`System.String`, effectively the extension's canonical URI) | Identifies *which* extension this is — must match the defining `StructureDefinition`'s own `url` exactly. |
| `value[x]` | `0..1` | any of ~50 types (same choice-element mechanism as `fixed[x]`/`pattern[x]` — see [`04-data-types-and-choice-elements.md`](04-data-types-and-choice-elements.md)) | The extension's actual payload, when it's a "simple" extension carrying one value. |
| `extension` | `0..*` | `Extension` | Nested sub-extensions — present instead of `value[x]` for a "complex" extension that needs more than one named field. |

The spec rule tying `value[x]` and nested `extension[]` together: **an extension SHALL have
either a `value[x]` or nested `extension`s, but not both.** A simple extension (one scalar or
complex value) uses `value[x]`; a complex extension (multiple named sub-fields, like a
mini-structure) uses nested `extension[]` entries, each itself shaped like a simple extension
with its own `url` (conventionally just the sub-field's name, not a full canonical URI, since
it's scoped inside the parent extension already).

## `StructureDefinition.context` and `contextInvariant` — where an extension may attach

These two root-level fields (introduced in file 02, detailed here since they're
extension-specific) are what make an extension *legal in a specific place* rather than legal
everywhere:

| `context.type` | Meaning |
|---|---|
| `element` | The context is any element whose own `ElementDefinition.id` matches the given expression — `[profile-url]#[element-id]`, or just an element id from the base spec if there's no `#`. |
| `fhirpath` | The context is every element matching a FHIRPath query. |
| `extension` | The context is a specific *other* extension, identified by its own `url` — lets one extension declare it's only legal nested inside another specific extension. |

`contextInvariant` (`0..*`, `string`) adds a further FHIRPath condition restricting *when*
(beyond just *where*) the extension may be used — e.g. "only on an active Organization."

## `modifierExtension` — the one with a hard safety rule

`extension` and `modifierExtension` are structurally identical (both `0..* Extension`) — the
difference is purely semantic, and it's a **safety rule, not a style choice**: *"If it is not
safe for an application processing the content of a resource to ignore an extension, it SHALL
be represented using `modifierExtension`."* An unrecognized plain `extension` can always be
safely ignored. An unrecognized `modifierExtension` means the processor **does not fully
understand the resource** and, per spec, should treat it as not understood — typically
rejecting it rather than silently processing a resource whose actual meaning might have been
changed by content it couldn't interpret.

This maps directly to `ElementDefinition.isModifier` (covered in
[`10-element-flags.md`](10-element-flags.md)) and is called out explicitly in
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §5 as needing a strictly
different validation rule from plain `extension` if/when this project ever supports it — not
built yet.

## How this maps to what's already built

- **Storage**: `OrganizationModel.extension` (`app/models/organization/core.py`) is a
  `JSONB`, `nullable=False`, `server_default='[]'` column, storing the raw
  `[{url, valueType, value}, ...]` array directly — no per-extension typed column, because
  extensions are dynamic and (eventually) org-defined, which can't be modeled as individually
  typed Pydantic fields. This matches `docs/architecture/fhir-profiling-and-extensibility-strategy.md`
  §5's schema recommendation exactly.
- **Input/response schemas**: `extension: list[dict] | None` on `OrganizationCreateSchema`,
  `OrganizationPatchSchema`, `PlainOrganizationResponse`, and (fixed in this session's schema
  audit — it was missing) `FHIROrganizationSchema`.
- **Mappers**: `to_fhir_organization()`/`to_plain_organization()` both pass the array through
  as-is (`list(org.extension)`), since it's already spec-shaped — no transform needed on the
  FHIR side; the plain side is a deliberately open decision per that architecture document's
  §9 ("whether `to_plain_*` attempts any flattening").
- **Not yet built**: closed-world validation of `extension[].url` against a registered
  extension definition (`fhir_profile` with `resource_type="Extension"`, per that document's
  §5) — today, any `url`/`value` shape that passes the generic `list[dict]` schema check is
  accepted. An unregistered `url` is not currently rejected.

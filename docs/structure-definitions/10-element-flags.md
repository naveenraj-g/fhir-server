# Element flags — mustSupport, isModifier, isSummary

Three independent boolean flags on `ElementDefinition`, each changing how a *consumer* of an
instance is expected to treat the element — none of them affect whether an instance is
structurally valid (a validator checking pure conformance can mostly ignore all three), but
they matter for anything actually consuming or summarizing the data, including this project's
own GraphQL gateway and the MCP tool surface built on top of the OpenAPI spec.

| Field | Card. | Type | Meaning |
|---|---|---|---|
| `mustSupport` | `0..1` | `boolean` | Flags that a system claiming to support this profile **must** be able to populate and/or meaningfully process this element — not optional to ignore, even though it may still be cardinality `0..1`. Doesn't change validity; changes conformance expectations. |
| `isModifier` | `0..1` | `boolean` | Marks that this element, if present, **changes the interpretation of other elements** in the resource — a consumer that doesn't understand a modifier element is not safe to treat the resource as fully understood. This is the element-level flag paired with `modifierExtension` (see [`09-extensions.md`](09-extensions.md)) — `Resource.modifierExtension`'s own `ElementDefinition` carries `isModifier: true`, which is exactly why unrecognized `modifierExtension` content is a hard-fail, not a soft one. |
| `isModifierReason` | `0..1` | `string` | Required alongside `isModifier: true` — explains *why* this element is a modifier, for anyone trying to understand the resource's semantics. |
| `isSummary` | `0..1` | `boolean` | Marks that this element should be included when a server returns a resource with `_summary=true` (a FHIR search parameter requesting an abbreviated representation). Purely a response-shaping concern. |

## Worked example: the three flags on real `ElementDefinition` entries

**`mustSupport`** — a country profile flagging `Organization.telecom` as something every
conformant system must actually handle, without making it structurally required:

```json
{
  "path": "Organization.telecom",
  "mustSupport": true
}
```

This changes nothing about whether an instance with no `telecom` at all is valid (it still is —
`min` is untouched). What it changes is this: if an instance *does* submit a `telecom` entry, a
system claiming to support this profile is not allowed to silently drop it. A system that
accepted a payload with `telecom` populated but returned it as `null` on the next `GET` would be
violating this flag — even though no JSON Schema check or cardinality check would ever catch that
violation, since both the write and the (broken) read are individually "valid shape."

**`isModifier` + `isModifierReason`** — this is the flag that makes `modifierExtension` behave
the way [`09-extensions.md`](09-extensions.md)'s worked example described. `Resource` itself (the
most abstract root type) carries no `extension`/`modifierExtension` at all — they're introduced
one level down, on `DomainResource` (what every actual resource, including `Organization`,
derives from). Verified directly against the real file:

```json
{
  "path": "DomainResource.modifierExtension",
  "isModifier": true,
  "isModifierReason": "Modifier extensions are expected to modify the meaning or interpretation of the resource that contains them"
}
```

Contrast with plain `extension`'s own `ElementDefinition` on the same base type, which explicitly
sets `isModifier: false`:

```json
{
  "path": "DomainResource.extension",
  "isModifier": false
}
```

This one flag — `true` on one path, explicitly `false` on the other — is the entire formal
distinction between "safe to ignore if unrecognized" and "must not be silently ignored." Nothing
else in the two elements' definitions differs.

**`isSummary`** — e.g. `Organization.name`'s own `ElementDefinition` in the base spec carries
`isSummary: true`, meaning a `GET /Organization/190001?_summary=true` request (not currently
implemented by this project, per the closing section below) would be expected to include `name`
in its trimmed-down response even though most other fields are omitted.

## Why `mustSupport` matters for this project specifically

`mustSupport` is the field a country or organization profile would use to say "yes, the base
spec allows this field to be absent, but under *our* profile, if your system claims
conformance, it had better actually be able to send/receive it" — without going so far as
bumping `min` to `1` (which would make it a hard structural requirement, rejecting any instance
that omits it). This is a real, useful middle ground between "optional, ignore freely" and
"required" that this project's current implementation doesn't yet have a home for — nothing in
`app/fhir/validation/` or the planned `fhir_profile` design
(`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §2 table) currently
accounts for it. Worth a deliberate decision once the profile-engine scope is actually being
built, not assumed to be out of scope just because it isn't a hard validation failure.

## Why `isModifier` matters even though this project doesn't support `modifierExtension` yet

Per [`09-extensions.md`](09-extensions.md), `modifierExtension` support isn't built. But the
*concept* `isModifier` encodes — "an unrecognized piece of content here means you don't safely
understand this resource" — is a real correctness property worth keeping in mind for any future
extension work: the moment this project does support `modifierExtension`, the validation rule
for it must be categorically stricter (hard-reject on anything unrecognized) than the rule for
plain `extension` (safe to ignore if unrecognized). This isn't a hypothetical edge case — it's
an explicit spec safety rule, already flagged in that architecture document's §5 as something
needing its own stricter path "per spec," not a house style choice.

## `isSummary` and this project's `_summary` support

This project's resources don't currently implement FHIR's `_summary` search parameter at all —
every `GET` returns the full resource. `isSummary` is documented here for completeness (per the
"every field, A to Z" brief) but has no current implementation surface in this codebase.

# Use case: a modifier extension

**Scenario:** a tenant needs to record that an Organization is under a temporary legal
restriction — say, a regulatory hold that means the organization's data should not be treated
as normally active even though `active: true` is still set for unrelated operational reasons.
Critically, any system that doesn't understand this restriction **must not** silently process
the Organization as if nothing were wrong — that would be actively unsafe, not just incomplete.

## Why this is `modifierExtension`, not `extension`

Per [`09-extensions.md`](../09-extensions.md)'s safety rule: *"If it is not safe for an
application processing the content of a resource to ignore the extension, it SHALL be
represented using `modifierExtension`."* A plain `extension` recording "under regulatory hold"
could be silently dropped by a system that doesn't know about it, and that system would then
treat the Organization as fully normal — which is exactly the unsafe outcome this scenario needs
to prevent. `modifierExtension` forces the opposite behavior: a system that doesn't recognize it
is supposed to treat the whole resource as not fully understood.

## Defining it

Structurally identical to a plain extension definition
([`05-adding-a-required-extension.md`](05-adding-a-required-extension.md)'s Step 1) — the only
difference is which array it's placed in on the instance, not anything in the extension's own
`StructureDefinition`:

```json
{
  "url": "https://clinic-x.dev/fhir/StructureDefinition/regulatory-hold",
  "name": "RegulatoryHold",
  "status": "active",
  "kind": "complex-type",
  "abstract": false,
  "type": "Extension",
  "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
  "derivation": "constraint",
  "context": [{ "type": "element", "expression": "Organization" }],
  "differential": {
    "element": [
      { "path": "Extension.value[x]", "type": [{ "code": "boolean" }] }
    ]
  }
}
```

And on the instance, it goes in `modifierExtension`, not `extension`:

```json
{
  "resourceType": "Organization",
  "active": true,
  "modifierExtension": [
    { "url": "https://clinic-x.dev/fhir/StructureDefinition/regulatory-hold", "valueBoolean": true }
  ]
}
```

## The element-level flag that corresponds to this: `isModifier`

If this were expressed as a profile requirement rather than an ad hoc instance value, the
`ElementDefinition` for `Organization.modifierExtension`'s slice would carry
`isModifier: true` and a required `isModifierReason` explaining why
([`10-element-flags.md`](../10-element-flags.md)) — e.g. *"Indicates the Organization's active
status cannot be relied upon at face value without checking this flag."*

## What validating this correctly means — stricter than every other extension use case

Per [`09-extensions.md`](../09-extensions.md): an unrecognized `extension` can always be safely
ignored by a validator or consumer. An unrecognized `modifierExtension` **cannot** — a correct
implementation must treat a resource carrying an unrecognized `modifierExtension` as not fully
understood, which in practice usually means rejecting it rather than silently processing it. This
is a strictly different (and stricter) rule than the closed-world registration check already
proposed for plain extensions in
[`09-extensions.md`](../09-extensions.md)'s closing section — for a plain extension, an
unregistered `url` can reasonably be rejected as *invalid input*; for a `modifierExtension`, an
unrecognized `url` arguably must be rejected by *every* consumer of the resource, including
read paths, not just the write path, since the whole point is that downstream readers can't
safely treat the resource as normal.

## What's needed to actually support this (not built yet)

This project has no concept of `modifierExtension` anywhere today — `OrganizationModel` has a
single `extension` JSONB column with no separate `modifier_extension` counterpart. Adding real
support means: a second column (or a flag distinguishing the two within one array), a stricter
validation rule enforced not just at write time but reflected in how `to_fhir_organization()`/
`to_plain_organization()` expose it to readers, and — the hardest part — deciding what
"treat as not fully understood" actually means operationally for every consumer of this data,
including this project's own GraphQL gateway. Flagged in
`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §5 as needing its own stricter
path; not designed in detail there or here.

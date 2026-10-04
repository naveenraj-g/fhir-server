# Use case: adding a required extension

**Scenario:** an organization-level tenant needs to record a government tax ID on every
Organization — not a standard FHIR element, and not something every tenant needs, so it can't
be a core column. The tenant's own profile should both *define* this extension and *require*
it.

## Step 1 — define the extension itself (a StructureDefinition, per file 09)

```json
{
  "url": "https://clinic-x.dev/fhir/StructureDefinition/tax-id",
  "name": "TaxID",
  "status": "active",
  "kind": "complex-type",
  "abstract": false,
  "type": "Extension",
  "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
  "derivation": "constraint",
  "context": [
    { "type": "element", "expression": "Organization" }
  ],
  "differential": {
    "element": [
      {
        "path": "Extension.value[x]",
        "type": [{ "code": "string" }]
      }
    ]
  }
}
```

Reading this against [`09-extensions.md`](../09-extensions.md): `context.type: "element"` with
`expression: "Organization"` means this extension is only legal directly on an `Organization`
resource, not on arbitrary other resources or nested inside other extensions. The differential
narrows `Extension.value[x]` (which in the base `Extension` type allows ~50 possible types) down
to just `string` — this is a **simple** extension (uses `value[x]`, no nested `extension[]`
sub-structure), per the "simple vs. complex" distinction in file 09.

## Step 2 — require it on the org's own Organization profile

Requiring an *extension* works the same way as requiring any other element — extensions appear
in `differential.element[]` with a `path` ending in `.extension` and a `sliceName`/`url`
identifying which extension, with ordinary `min`/`max`:

```json
{
  "path": "Organization.extension",
  "sliceName": "tax-id",
  "min": 1,
  "max": "1",
  "type": [
    { "code": "Extension", "profile": ["https://clinic-x.dev/fhir/StructureDefinition/tax-id"] }
  ]
}
```

`type.profile` (from [`04-data-types-and-choice-elements.md`](../04-data-types-and-choice-elements.md))
is what ties this slice to the specific extension definition from Step 1 — "one must apply," and
since only one profile URL is listed, it must be that one.

## Shaped for this project's planned storage

Per `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §5, extension
*definitions* reuse the same `fhir_profile` table with `resource_type = "Extension"`:

```
fhir_profile (resource_type="Extension")
  canonical_url: "https://clinic-x.dev/fhir/StructureDefinition/tax-id"
  scope_level: 'organization', scope_id: <org_id>
  structure: { "context": ["Organization"], "valueType": "string", "min": 0, "max": 1 }
```

And the *requirement* that Organization instances under this tenant must carry it would live in
that tenant's `fhir_profile` row for `resource_type = "Organization"`, under its own
`structure.elements` — the same shape used in every other use case file in this folder.

## What's needed to actually enforce this (not built yet)

Two separate checks, per that architecture document's §5:

1. **Closed-world validation** — every `extension[].url` present on a write must resolve to a
   registered `Extension`-kind `fhir_profile` entry in the org's resolved chain, with a matching
   `context`. An unregistered `url` should be rejected, not silently accepted.
2. **Required-extension enforcement** — if the org's own Organization profile declares
   `tax-id` as `min: 1`, a write with no matching entry in `extension[]` must be rejected the
   same way any other unmet `min` would be.

Neither exists today — `OrganizationModel.extension` currently accepts any
`list[{url, valueType, value}]`-shaped array with no registration check and no per-tenant
requirement.

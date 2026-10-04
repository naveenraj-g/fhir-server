# StructureDefinition — root-level fields

Every field below is pulled directly from `StructureDefinition`'s own published
`StructureDefinition` (HL7 R4, `profiles-resources.json`). Cardinality is `min..max` as
declared on the base resource itself — a profile can only narrow these further (see
[`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md)).

Every FHIR resource also carries the generic `DomainResource` fields (`id`, `meta`,
`implicitRules`, `language`, `text`, `contained`, `extension`, `modifierExtension`) — those
aren't specific to StructureDefinition and are omitted here; only the fields StructureDefinition
itself adds are covered.

## Identity and metadata

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `url` | `1..1` | `uri` | The profile's **permanent, globally unique identity** — not its database row ID, its canonical name. Every reference to this profile from anywhere else (another profile's `baseDefinition`, an extension's `context`, a binding's `valueSet`) is this URL, never an internal ID. This is the single field that makes "profiles as data, referenced by URL" work at all. |
| `identifier` | `0..*` | `Identifier` | An *additional* business identifier for the profile artifact itself (e.g. an OID some registry assigned it) — distinct from `url`, and rarely populated in practice. |
| `version` | `0..1` | `string` | The business version of this specific profile document (e.g. `"1.2.0"`) — not a FHIR version. Used together with `url` to distinguish revisions of the same canonical profile. |
| `name` | `1..1` | `string` | Computer-friendly name — must be a valid identifier-like token (no spaces), used as the thing codegen tools would name a class after. |
| `title` | `0..1` | `string` | Human-friendly display name — this is what you'd show in a UI, `name` is what code would use. |
| `status` | `1..1` | `code` | Lifecycle state: `draft \| active \| retired \| unknown`. A validator should generally only apply `active` profiles. |
| `experimental` | `0..1` | `boolean` | Marks the profile as not-for-production-use (testing/demo only). Doesn't change validation behavior by itself — it's a signal to tooling and humans. |
| `date` | `0..1` | `dateTime` | When this version of the profile was last changed — not when the resource row was created in your DB. |
| `publisher` | `0..1` | `string` | Who maintains this profile (an org or individual name) — for your country/org layers, this would naturally be the country body or the tenant's own name. |
| `contact` | `0..*` | `ContactDetail` | How to reach the publisher. |
| `description` | `0..1` | `markdown` | Natural-language explanation of what this profile is and why it exists — the human-readable counterpart to the machine-readable constraints below it. |
| `useContext` | `0..*` | `UsageContext` | The context this profile is intended for (e.g. "inpatient", "pediatric") — used for discovery/filtering in a profile registry, not evaluated during validation. |
| `jurisdiction` | `0..*` | `CodeableConcept` | Intended country/region — **this is the field a country-layer profile would naturally populate** (e.g. a code for "IN" or "US"), distinct from how your own `scope_level`/`scope_id` columns track it operationally. |
| `purpose` | `0..1` | `markdown` | Why this profile was authored — the business justification, as opposed to `description`'s "what it is." |
| `copyright` | `0..1` | `markdown` | Legal/publishing restrictions. |
| `keyword` | `0..*` | `Coding` | Terms to assist search/indexing in a profile registry. |

## What this profile actually constrains

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `fhirVersion` | `0..1` | `code` | Which FHIR version this profile targets (e.g. `4.0.1`). Matters because `ElementDefinition`'s own shape has changed across FHIR versions — a validator needs to know which rules apply. |
| `mapping` | `0..*` | `BackboneElement` | Declares an external coding scheme this profile's elements can be mapped to (e.g. HL7 v2, a national mapping spec) — each entry has `identity`/`uri`/`name`/`comment`. Individual `ElementDefinition.mapping` entries (see [`03-element-definition-core-fields.md`](03-element-definition-core-fields.md)) reference this by `identity`. Informational only — not evaluated by a validator. |
| `kind` | `1..1` | `code` | `primitive-type \| complex-type \| resource \| logical` — see the table below. This is the field that distinguishes "this defines a resource type" from "this defines an extension" (extensions are `complex-type`). |
| `abstract` | `1..1` | `boolean` | Whether this is an abstract type that's never directly instantiated (e.g. `DomainResource` itself) — `false` for every concrete resource and every profile. |
| `context` | `0..*` | `BackboneElement` | **Only relevant when this StructureDefinition defines an extension.** Says where the extension is legal to attach — see [`09-extensions.md`](09-extensions.md). Each entry has `type` (`fhirpath \| element \| extension`) and `expression`. |
| `contextInvariant` | `0..*` | `string` | FHIRPath expression(s) further restricting *when* (not just *where*) an extension can be used — also extension-only, also covered in file 09. |
| `type` | `1..1` | `uri` | The actual data type or resource this StructureDefinition is about (e.g. `"Organization"`, `"Extension"`, `"HumanName"`). For a profile, this is the *same* `type` as its base — profiling never changes what resource type you're describing, only what's allowed within it. |
| `baseDefinition` | `0..1` | `canonical` | The canonical `url` of the parent this StructureDefinition derives from. `null` only for the handful of root base types that derive from nothing (`Resource`, `Element`). This is the field that makes the three-layer chain possible — see [`11-profiles-and-derivation.md`](11-profiles-and-derivation.md). |
| `derivation` | `0..1` | `code` | `specialization \| constraint`. `specialization` = "this defines a genuinely new type" (what HL7 did for every base resource). `constraint` = "this narrows an existing type" (what every profile — country, org, extension — does). |
| `snapshot` | `0..1` | `BackboneElement` | The fully-resolved `element[]` list. One required child: `element: 1..* ElementDefinition`. |
| `differential` | `0..1` | `BackboneElement` | The authored, partial `element[]` list — only what this layer changes. One required child: `element: 1..* ElementDefinition`. |

### `kind` — the four values, HL7's own definitions

| Code | Meaning |
|---|---|
| `primitive-type` | A primitive type that has a value and an extension (e.g. `string`, `boolean`, `dateTime`). Only the base FHIR specification defines these — a profile never introduces a new primitive type. |
| `complex-type` | A complex structure made of a set of data elements, suitable for use *inside* resources (e.g. `HumanName`, `Identifier`, `CodeableConcept`, and — the one relevant to this project's extensibility work — `Extension` itself). These don't have an independently maintained identity the way a resource does. |
| `resource` | A directed acyclic graph of elements aggregating other types into an identifiable entity (e.g. `Organization`, `Patient`). This is what gets its own REST endpoints and can be the target of a `Reference`. |
| `logical` | A pattern/template not intended to be a real resource or type — used for modeling, not for actual instances. Not relevant to this project. |

### `derivation` — the two values, HL7's own definitions

| Code | Meaning |
|---|---|
| `specialization` | "This definition defines a new type that adds additional elements to the base type." This is what HL7 did once, for every base resource/datatype. This project will never author a `specialization` — only HL7 does. |
| `constraint` | "This definition adds additional rules to an existing concrete type." This is what **every** profile this project will ever author is — country layer, organization layer, and every extension definition. |

## Worked example: Organization's own root fields

Pulled directly from the real file:

```
url:              http://hl7.org/fhir/StructureDefinition/Organization
name:             Organization
status:           active
kind:             resource
abstract:         false
type:             Organization
baseDefinition:   http://hl7.org/fhir/StructureDefinition/DomainResource
derivation:       specialization
```

Note `derivation: specialization`, not `constraint` — this is the base definition itself, not a
profile of something else. A hypothetical country-layer profile of Organization would instead
have `baseDefinition: http://hl7.org/fhir/StructureDefinition/Organization` and
`derivation: constraint`.

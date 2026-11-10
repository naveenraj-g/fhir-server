# FHIR R4 Terminology Module — Standard Reference

This is a primary-source implementation reference for the FHIR R4 (v4.0.1)
terminology module — the five resources (`CodeSystem`, `ValueSet`,
`ConceptMap`, `NamingSystem`, `TerminologyCapabilities`) and every standard
operation on them (`$lookup`, `$validate-code` ×2, `$subsumes`,
`$find-matches`, `$expand`, `$translate`, `$closure`). Everything below was
pulled directly from the spec pages cited per section — use it while writing
models/schemas/routes instead of re-fetching the spec each time.

Read [08-fhir-r4-standard-compliance-gap-analysis.md](08-fhir-r4-standard-compliance-gap-analysis.md)
first if you haven't — it says what this repo is missing. This doc backs
every claim in that gap list with the actual spec text, and gives the full
structural detail needed to close each gap.

**Spec version:** R4, v4.0.1 (hl7.org/fhir/R4/). Every URL below is under
that base.

---

## 1. Binding strength (how a ValueSet governs a coded field)

From [terminologies.html](https://www.hl7.org/fhir/R4/terminologies.html).
This applies everywhere a profile binds an element to a ValueSet
(`ElementDefinition.binding.strength`) — it's the rule for what "governed by
this ValueSet" actually requires.

| Strength | Conformance rule |
|---|---|
| `required` | Codes **SHALL** come from the value set. For `CodeableConcept`, at least one `Coding` must be present and one of them must be from the value set. `text` alone does not satisfy the requirement. |
| `extensible` | Codes **SHALL** come from the value set *if* an applicable code exists there. If no appropriate code exists, an alternate code or plain text may be used instead. Any code added beyond the value set must be the closest match and cannot replace a value set code. |
| `preferred` | Value set codes **SHOULD** be used, but aren't required. |
| `example` | No conformance expectation at all — the value set just illustrates the intended concepts. |

Other rules from the same page:
- Profiles can *narrow* `required`/`extensible` bindings (add constraints) but can't add codes outside the base value set — except under `extensible`, when no appropriate base code exists.
- `preferred`/`example` bindings can be freely rebound to a different value set by a derived profile.
- For `string`/`uri` elements bound to a value set, only `value` is checked — `system`/`display` don't apply (there are none).
- `system` values are always case-sensitive. Code case-sensitivity is system-dependent (`CodeSystem.caseSensitive`); FHIR's own defined codes are case-sensitive and must be used exactly as defined.

**This repo's current narrower meaning**, confirmed against §6 of the gap
analysis: `TerminologyFieldBinding.binding_strength` only gates whether
`/validate` rejects an unrecognized code — it doesn't yet implement the
"closest match if nothing applicable" `extensible` carve-out, and `preferred`/
`example` aren't distinguished at all (both currently behave as
non-enforcing). Worth revisiting once `$validate-code` is built against this
spec's real semantics.

---

## 2. CodeSystem

Spec: [codesystem.html](https://www.hl7.org/fhir/R4/codesystem.html)

### 2.1 Element structure

| Element | Card. | Type | Notes |
|---|---|---|---|
| `url` | 0..1 | uri | Canonical identifier — this is the value that appears in `Coding.system` |
| `identifier` | 0..* | Identifier | Extra business identifiers (e.g. an OID) |
| `version` | 0..1 | string | Business version — appears in `Coding.version` |
| `name` | 0..1 | string | Computer-friendly name |
| `title` | 0..1 | string | Human-friendly title |
| `status` | **1..1** | code | `draft \| active \| retired \| unknown` — required binding, see §2.2 |
| `experimental` | 0..1 | boolean | Test/education only, not for real use |
| `date` | 0..1 | dateTime | Last-changed date |
| `publisher` | 0..1 | string | Publishing org/individual |
| `contact` | 0..* | ContactDetail | |
| `description` | 0..1 | markdown | |
| `useContext` | 0..* | UsageContext | |
| `jurisdiction` | 0..* | CodeableConcept | Extensible binding |
| `purpose` | 0..1 | markdown | |
| `copyright` | 0..1 | markdown | |
| `caseSensitive` | 0..1 | boolean | Whether code comparison is case-sensitive |
| `valueSet` | 0..1 | canonical(ValueSet) | The implicit "all codes in this system" ValueSet |
| `hierarchyMeaning` | 0..1 | code | `grouped-by \| is-a \| part-of \| classified-with` — see §2.3 |
| `compositional` | 0..1 | boolean | Whether a post-coordination grammar exists (e.g. SNOMED CT expressions) |
| `versionNeeded` | 0..1 | boolean | Concept permanence isn't guaranteed — a version must be pinned |
| `content` | **1..1** | code | `not-present \| example \| fragment \| complete \| supplement` — required binding, see §2.4 |
| `supplements` | 0..1 | canonical(CodeSystem) | Set only when `content = supplement` — the CodeSystem this one adds designations/properties to |
| `count` | 0..1 | unsignedInt | Total concept count |
| `filter[]` | 0..* | BackboneElement | Filters usable in `ValueSet.compose.include.filter.property` |
| `property[]` | 0..* | BackboneElement | Property definitions concepts may carry |
| `concept[]` | 0..* | BackboneElement | The concepts themselves, nested hierarchically |

**Invariant:** codes **SHALL** be unique within one CodeSystem.

#### `concept[]` (recursive)

| Element | Card. | Type |
|---|---|---|
| `code` | 1..1 | code |
| `display` | 0..1 | string |
| `definition` | 0..1 | string |
| `designation[]` | 0..* | `{language: code, use: Coding, value: string (1..1)}` |
| `property[]` | 0..* | `{code: code (1..1), value[x]: code\|Coding\|string\|integer\|boolean\|dateTime\|decimal (1..1)}` |
| `concept[]` | 0..* | same structure, recursive (child concepts) |

#### `filter[]`

| Element | Card. | Type |
|---|---|---|
| `code` | 1..1 | code |
| `description` | 0..1 | string |
| `operator[]` | **1..***  | code — allowed values below |
| `value` | 1..1 | string |

`filter.operator` allowed values: `=`, `is-a`, `descendent-of`, `is-not-a`, `regex`, `in`, `not-in`, `generalizes`, `exists`.

#### `property[]` (the CodeSystem's own property *definitions*, distinct from the standard "Concept Properties" code system in §2.5)

| Element | Card. | Type |
|---|---|---|
| `code` | 1..1 | code |
| `uri` | 0..1 | uri — formal meaning, often `http://hl7.org/fhir/concept-properties#<code>` (§2.5) |
| `description` | 0..1 | string |
| `type` | 1..1 | code — `code \| Coding \| string \| integer \| boolean \| dateTime \| decimal` |

### 2.2 `status` (shared across all five resources)

`draft | active | retired | unknown` — PublicationStatus, required binding. Same enum on ValueSet, ConceptMap, NamingSystem, TerminologyCapabilities.

### 2.3 `hierarchyMeaning`

Spec: [valueset-codesystem-hierarchy-meaning.html](https://www.hl7.org/fhir/R4/valueset-codesystem-hierarchy-meaning.html)

| Code | Definition (verbatim) |
|---|---|
| `grouped-by` | "No particular relationship between the concepts can be assumed, except what can be determined by inspection of the definitions of the elements (possible reasons to use this: importing from a source where this is not defined or where various parts of the hierarchy have different meanings)." |
| `is-a` | "A hierarchy where the child concepts have an IS-A relationship with the parents — that is, all the properties of the parent are also true for its child concepts. Note that is-a is a property of the concepts, so additional subsumption relationships may be defined using properties or the subsumes extension." |
| `part-of` | "Child elements list the individual parts of a composite whole (e.g. body site)." |
| `classified-with` | "Child concepts in the hierarchy may have only one parent, and there is a presumption that the code system is a 'closed world' meaning all things must be in the hierarchy. This results in concepts such as 'not otherwise classified.'" |

This repo's `TerminologyRelationship.relationship_type` is a free string (§
below, "IS-A, part-of, and other semantic relationships") — closing gap §6 of
the 08 doc (`$subsumes`) means picking `is-a` specifically, since `$subsumes`
is only meaningful for an is-a hierarchy.

### 2.4 `content` (CodeSystemContentMode)

Spec: [valueset-codesystem-content-mode.html](https://www.hl7.org/fhir/R4/valueset-codesystem-content-mode.html)

| Code | Definition (verbatim) |
|---|---|
| `not-present` | "None of the concepts defined by the code system are included in the code system resource." |
| `example` | "A few representative concepts are included in the code system resource. There is no useful intent in the subset choice and there's no process to make it workable: it's not intended to be workable." |
| `fragment` | "A subset of the code system concepts are included in the code system resource. This is a curated subset released for a specific purpose under the governance of the code system steward, and that the intent, bounds and consequences of the fragmentation are clearly defined in the fragment or the code system documentation. Fragments are also known as partitions." |
| `complete` | "All the concepts defined by the code system are included in the code system resource." |
| `supplement` | "The resource doesn't define any new concepts; it just provides additional designations and properties to another code system." |

This matters directly for the org-concepts/display-overrides redesign (08's
gap #): a per-org "add a custom code to a shared system" feature is, in real
FHIR terms, a `CodeSystem` with `content=supplement` and `supplements`
pointing at the base system — not modeled as a FHIR resource today, but this
is the shape to target if/when it is.

### 2.5 Standard "Concept Properties" code system

Spec: `http://hl7.org/fhir/concept-properties` (linked from codesystem.html's `property.uri`). **Note: the spec page itself says "This Code system is not currently used"** — these are reference-defined properties, not something every server must implement, but they're the standard vocabulary to reuse rather than inventing new property codes for the same concepts.

| Code | Type | Definition |
|---|---|---|
| `inactive` | boolean (default false) | "True if the concept is not considered active." |
| `deprecated` | dateTime | Records when a concept was deprecated. Deprecated concepts still work but use is discouraged, and they're expected to become inactive later. |
| `notSelectable` | boolean | A concept meant only as a grouping/selector, not for direct user choice. |
| `parent` | code | A parent of this concept. Meaning of "parent" is defined by `hierarchyMeaning`. |
| `child` | code | A child of this concept. Same caveat. |

### 2.6 Operations

#### `$lookup` — code/Coding → display + properties

Spec: [codesystem-operation-lookup.html](https://www.hl7.org/fhir/R4/codesystem-operation-lookup.html)

Invocation: `GET [base]/CodeSystem/$lookup?system=...&code=...` or `POST [base]/CodeSystem/$lookup` with a `Parameters` body. Idempotent. Client must supply a system+code or a `coding`.

IN:

| Name | Card. | Type |
|---|---|---|
| `code` | 0..1 | code |
| `system` | 0..1 | uri |
| `version` | 0..1 | string |
| `coding` | 0..1 | Coding |
| `date` | 0..1 | dateTime |
| `displayLanguage` | 0..1 | code |
| `property` | 0..* | code — which properties to return; server decides if omitted. Standard values: `url`, `name`, `version`, `display`, `definition`, `designation`, `parent`, `child`, `lang.X` |

OUT:

| Name | Card. | Type |
|---|---|---|
| `name` | 1..1 | string — the code system's own name |
| `version` | 0..1 | string |
| `display` | 1..1 | string |
| `designation` | 0..* | `{language, use: Coding, value: string (1..1)}` |
| `property` | 0..* | `{code (1..1), value[x], description, subproperty[]}` |

Example — GET:
```
GET [base]/CodeSystem/$lookup?system=http://loinc.org&code=1963-8
```
Response (200, `Parameters`):
```json
{
  "resourceType": "Parameters",
  "parameter": [
    {"name": "name", "valueString": "LOINC"},
    {"name": "version", "valueString": "2.48"},
    {"name": "display", "valueString": "Bicarbonate [Moles/volume] in Serum"}
  ]
}
```
Not-found → 400 `OperationOutcome`, `issue.code = not-found`.

#### `$validate-code` on CodeSystem — is this code valid in this system

Spec: [codesystem-operation-validate-code.html](https://www.hl7.org/fhir/R4/codesystem-operation-validate-code.html)

Invocation: `[base]/CodeSystem/[id]/$validate-code` (instance) or `[base]/CodeSystem/$validate-code` (type, GET or POST). **Must** send exactly one of `code`+`system`, `coding`, `codeableConcept`; outside instance level must also send `url` or `codeSystem`.

IN: `url`, `codeSystem` (inline), `code`, `version`, `display`, `coding`, `codeableConcept`, `date`, `abstract` (allow abstract concepts to validate true, default false), `displayLanguage`.

OUT: `result` (1..1 boolean), `message` (0..1), `display` (0..1 — server's recommended display).

200 even when invalid (`result=false`); 400 `OperationOutcome` only when the server genuinely *can't* determine validity (e.g. missing system).

#### `$validate-code` on ValueSet — is this code a member of this value set

Spec: [valueset-operation-validate-code.html](https://www.hl7.org/fhir/R4/valueset-operation-validate-code.html)

**This is the one this repo's own `/validate` is actually standing in for** (per 08 §5) — the real operation validates against a ValueSet *canonical URL*, not a resource+field binding.

Invocation: `[base]/ValueSet/[id]/$validate-code` or `[base]/ValueSet/$validate-code`. If not instance-level, must send one of `url`/`context`/`valueSet`. Must send exactly one of `code`/`coding`/`codeableConcept`.

IN: `url`, `context`, `valueSet` (inline), `valueSetVersion`, `code`, `system`, `systemVersion`, `display`, `coding`, `codeableConcept`, `date`, `abstract`, `displayLanguage`.

OUT: same shape as CodeSystem's — `result`, `message`, `display`.

#### `$subsumes` — hierarchy relationship between two codes

Spec: [codesystem-operation-subsumes.html](https://www.hl7.org/fhir/R4/codesystem-operation-subsumes.html)

**This is the cheapest gap to close per 08 §6** — `TerminologyRelationship` already has the data.

Invocation: `[base]/CodeSystem/$subsumes` (type) or `[base]/CodeSystem/[id]/$subsumes` (instance), GET or POST.

IN: `codeA`, `codeB`, `system`, `version`, `codingA`, `codingB`. Client must supply both an A and a B, as codes or Codings.

OUT: `outcome` (1..1, code, required binding — see table below). If the server can't determine it, an error `OperationOutcome` instead.

**`outcome` values** ([valueset-concept-subsumption-outcome.html](https://www.hl7.org/fhir/R4/valueset-concept-subsumption-outcome.html)), read **A relative to B**:

| Code | Definition (verbatim) |
|---|---|
| `equivalent` | "The two concepts are equivalent (have the same properties)." |
| `subsumes` | 'Coding/code "A" subsumes Coding/code "B" (e.g. B has all the properties A has, and some of its own).' |
| `subsumed-by` | 'Coding/code "A" is subsumed by Coding/code "B" (e.g. A has all the properties B has, and some of its own).' |
| `not-subsumed` | 'Coding/code "A" and Coding/code "B" are disjoint (e.g. each has properties that the other doesn't have).' |

Example:
```
GET [base]/CodeSystem/$subsumes?system=http://snomed.info/sct&codeA=3738000&codeB=235856003
```
```json
{"resourceType": "Parameters", "parameter": [{"name": "outcome", "valueCode": "subsumed-by"}]}
```

#### `$find-matches` (Trial Use) — infer a code from property values

Spec: [codesystem-operation-find-matches.html](https://www.hl7.org/fhir/R4/codesystem-operation-find-matches.html)

Niche, SNOMED-CT-compositional-grammar-oriented — not relevant to this repo's current scope (no compositional code system in use). IN: `system`, `version`, `property[]` (repeatable `{code, value}` pairs to match against), `exact` (1..1 boolean — human vs. machine caller), `compositional`. OUT: `match[]`, each `{code: Coding, unmatched[], comment}`.

---

## 3. ValueSet

Spec: [valueset.html](https://www.hl7.org/fhir/R4/valueset.html)

### 3.1 Element structure

| Element | Card. | Type | Notes |
|---|---|---|---|
| `url`, `identifier`, `version`, `name`, `title`, `status`, `experimental`, `date`, `publisher`, `contact`, `description`, `useContext`, `jurisdiction`, `purpose`, `copyright` | — | — | Same shapes as CodeSystem's metadata block |
| `immutable` | 0..1 | boolean | If true, no new content-defining version will ever be issued |
| `compose` | 0..1 | BackboneElement | The logical definition ("compose this value set from...") |
| `expansion` | 0..1 | BackboneElement | The materialized result of actually expanding `compose` |

#### `compose`

| Element | Card. | Type |
|---|---|---|
| `lockedDate` | 0..1 | date |
| `inactive` | 0..1 | boolean — whether to include inactive codes |
| `include[]` | **1..*** | see below |
| `exclude[]` | 0..* | same structure as `include[]` |

#### `compose.include[]` / `compose.exclude[]`

| Element | Card. | Type |
|---|---|---|
| `system` | 0..1 | uri |
| `version` | 0..1 | string — `*` means all versions |
| `concept[]` | 0..* | `{code (1..1), display, designation[]}` — explicit enumerated codes |
| `filter[]` | 0..* | `{property (1..1), op (1..1), value (1..1)}` — see operators below |
| `valueSet[]` | 0..* | canonical(ValueSet) — union of other value sets |

Invariants: must have a `valueSet` or a `system`; can't have both `concept[]` and `filter[]`; `concept`/`filter` require `system`.

`filter.op` allowed values: `=`, `is-a`, `descendent-of`, `is-not-a`, `regex`, `in`, `not-in`, `generalizes`, `exists`. Multiple filters AND together.

#### `expansion`

| Element | Card. | Type |
|---|---|---|
| `identifier` | 0..1 | uri — a fresh UUID is recommended per expansion |
| `timestamp` | **1..1** | dateTime |
| `total` | 0..1 | integer |
| `offset` | 0..1 | integer — **SHALL NOT** be present unless paging |
| `parameter[]` | 0..* | `{name (1..1), value[x]}` — echoes back the expand-request parameters that shaped this result |
| `contains[]` | 0..* | see below, recursive |

#### `expansion.contains[]`

| Element | Card. | Type |
|---|---|---|
| `system` | 0..1 | uri |
| `abstract` | 0..1 | boolean — navigational grouping only, not independently selectable |
| `inactive` | 0..1 | boolean |
| `version` | 0..1 | string |
| `code` | 0..1 | code — absent means a placeholder/abstract entry |
| `display` | 0..1 | string |
| `designation[]` | 0..* | same shape as CodeSystem's |
| `contains[]` | 0..* | recursive — nested only when the expansion is hierarchical |

Invariants: must have `code` or `display`; must have `code` if not `abstract`; must have `system` if `code` is present.

### 3.2 `$expand` — materialize the ValueSet's code list

Spec: [valueset-operation-expand.html](https://www.hl7.org/fhir/R4/valueset-operation-expand.html)

**This is the big one, and the one that most needs rebuilding per 08 §1** — today's `/value-sets/{id}/expand` takes an internal integer PK and returns a flat DB-row page; the real operation takes a canonical URL (or inline `ValueSet`) and returns a full `ValueSet` resource with a proper `expansion`.

Invocation: `GET [base]/ValueSet/$expand` or `GET [base]/ValueSet/[id]/$expand`. Idempotent.

IN parameters (all optional unless noted):

| Name | Type | Notes |
|---|---|---|
| `url` | uri | Canonical ValueSet reference |
| `valueSet` | ValueSet | Inline value set (servers may decline) |
| `valueSetVersion` | string | |
| `context` | uri | `[StructureDefinition URL]#[path]` — resolve the ValueSet from a binding context instead of a direct URL |
| `contextDirection` | code | `incoming` \| `outgoing` |
| `filter` | string | Free-text filter, server-defined matching |
| `date` | dateTime | Expand as of this date |
| `offset` | integer | Paging start (default 0) |
| `count` | integer | Page size; `count=0` = "just give me the total" |
| `includeDesignations` | boolean | |
| `designation` | string (0..*) | Which designation use/language to include |
| `includeDefinition` | boolean | |
| `activeOnly` | boolean | Can't re-add codes the value set itself excludes |
| `excludeNested` | boolean | Flatten — no `contains.contains` |
| `excludeNotForUI` | boolean | Drop abstract/UI-grouping-only codes |
| `excludePostCoordinated` | boolean | |
| `displayLanguage` | code | |
| `exclude-system` | canonical (0..*) | `[system]\|[version]` to exclude — **note the literal hyphen in the parameter name**, not `excludeSystem` |
| `system-version` | canonical (0..*) | Version to assume when the ValueSet doesn't pin one |
| `check-system-version` | canonical (0..*) | Version to enforce; conflicting version in the ValueSet → error |
| `force-system-version` | canonical (0..*) | Overrides the ValueSet's own pinned version — flagged by the spec itself as an edge case with real safety risk |

OUT: `return` (1..1, `ValueSet`) — the expansion is returned as the resource body directly, not wrapped in `Parameters`.

Examples (verbatim query forms from the spec):
```
GET [base]/ValueSet/23/$expand?filter=abdo
GET [base]/ValueSet/$expand?url=http://acme.com/fhir/ValueSet/23&valueSetVersion=1.1&filter=abdo
GET [base]/ValueSet/$expand?context=DiagnosticReport.category&contextDirection=incoming
GET [base]/ValueSet/23/$expand?date=2014-02-23&displayLanguage=de
GET [base]/ValueSet/23/$expand?offset=200&count=100
GET [base]/ValueSet/23/$expand?exclude-system=http://snomed.info/sct&check-system-version=http://loinc.org|2.62
```

Error case: expansion too large/infinite → `too-costly` issue; client should retry with a narrower `filter`.

---

## 4. ConceptMap

Spec: [conceptmap.html](https://www.hl7.org/fhir/R4/conceptmap.html)

### 4.1 Element structure

| Element | Card. | Type |
|---|---|---|
| metadata block (`url`…`copyright`) | — | same shape as CodeSystem's |
| `source[x]` | 0..1 | `sourceUri` or `sourceCanonical(ValueSet)` |
| `target[x]` | 0..1 | `targetUri` or `targetCanonical(ValueSet)` |
| `group[]` | 0..* | see below |

#### `group[]`

| Element | Card. | Type |
|---|---|---|
| `source` | 0..1 | uri — source code system |
| `sourceVersion` | 0..1 | string |
| `target` | 0..1 | uri — target code system |
| `targetVersion` | 0..1 | string |
| `element[]` | **1..*** | see below |
| `unmapped` | 0..1 | see below |

#### `group.element[]`

| Element | Card. | Type |
|---|---|---|
| `code` | 0..1 | code — the source concept |
| `display` | 0..1 | string |
| `target[]` | 0..* | see below |

#### `group.element.target[]` — **this is the piece `TerminologyConceptMap` is standing in for**

| Element | Card. | Type |
|---|---|---|
| `code` | 0..1 | code |
| `display` | 0..1 | string |
| `equivalence` | **1..1** | code — required binding, 10 values, table below |
| `comment` | 0..1 | string — **required** (by convention, not a hard invariant) when equivalence is `narrower` or `inexact` |
| `dependsOn[]` | 0..* | `{property: uri (1..1), system: canonical, value: string (1..1), display}` |
| `product[]` | 0..* | same shape as `dependsOn[]` |

#### `group.unmapped`

| Element | Card. | Type |
|---|---|---|
| `mode` | **1..1** | code — `provided \| fixed \| other-map` |
| `code` | 0..1 | code — required if `mode = fixed` |
| `display` | 0..1 | string |
| `url` | 0..1 | canonical(ConceptMap) — required if `mode = other-map` |

`mode` meanings: `provided` = pass the source code through unchanged when there's no match; `fixed` = map every unmapped source code to one default `code`; `other-map` = defer to a different ConceptMap at `url`.

### 4.2 `equivalence` — the exact 10 codes

Spec: [valueset-concept-map-equivalence.html](https://www.hl7.org/fhir/R4/valueset-concept-map-equivalence.html). **This is 08 §4's gap** — `TerminologyConceptMap.mapping_type` is currently a free string; this is the real enum to replace it with.

Read as: how does the **target** relate to the **source**.

| Code | Definition (verbatim) |
|---|---|
| `relatedto` | "The concepts are related to each other, and have at least some overlap in meaning, but the exact relationship is not known." |
| `equivalent` | "The definitions of the concepts mean the same thing (including when structural implications of meaning are considered), (i.e. extensionally identical)." |
| `equal` | "The definitions of the concepts are exactly the same (i.e. only grammatical differences) and structural implications of meaning are identical or irrelevant (i.e. intentionally identical)." |
| `wider` | "The target mapping is wider in meaning than the source concept." |
| `subsumes` | "The target mapping subsumes the meaning of the source concept (e.g. the source is-a target)." |
| `narrower` | "The target mapping is narrower in meaning than the source concept. The sense in which the mapping is narrower SHALL be described in the comments in this case, and applications should be careful when attempting to use these mappings operationally." |
| `specializes` | "The target mapping specializes the meaning of the source concept (e.g. the target is-a source)." |
| `inexact` | "The target mapping overlaps with the source concept, but both source and target cover additional meaning, or the definitions are imprecise and it is uncertain whether they have the same boundaries to their meaning. The sense in which the mapping is inexact SHALL be described in the comments in this case, and applications should be careful when attempting to use these mappings operationally." |
| `unmatched` | "There is no match for this concept in the target code system." |
| `disjoint` | "This is an explicit assertion that there is no mapping between the source and target concept." |

`$translate`'s `result=true` is only valid when at least one `match` has an equivalence *other than* `unmatched`/`disjoint` — those two codes represent "no real mapping," so a translate result consisting only of `unmatched`/`disjoint` matches must report `result: false`.

### 4.3 `$translate`

Spec: [conceptmap-operation-translate.html](https://www.hl7.org/fhir/R4/conceptmap-operation-translate.html)

Invocation: `[base]/ConceptMap/$translate` or `[base]/ConceptMap/[id]/$translate`. Idempotent. Exactly one of `code`/`coding`/`codeableConcept`.

IN: `url`, `conceptMap` (inline), `conceptMapVersion`, `code`, `system`, `version`, `source` (ValueSet the concept was chosen from — should normally be given), `coding`, `codeableConcept`, `target` (ValueSet to translate into), `targetsystem` (alternative to `target`), `dependency[]` (`{element: uri, concept: CodeableConcept}`), `reverse` (boolean — swap source/target direction).

OUT: `result` (1..1 boolean), `message`, `match[]` — each `{equivalence: code, concept: Coding (never userSelected=true), product[], source: canonical — which ConceptMap this match came from}`.

```
GET [base]/ConceptMap/$translate?system=http://hl7.org/fhir/composition-status&code=preliminary&source=http://hl7.org/fhir/ValueSet/composition-status&target=http://hl7.org/fhir/ValueSet/v3-ActStatus
```
```json
{"resourceType": "Parameters", "parameter": [
  {"name": "result", "valueBoolean": true},
  {"name": "match", "part": [
    {"name": "equivalence", "valueCode": "equivalent"},
    {"name": "concept", "valueCoding": {"system": "http://hl7.org/fhir/v3/ActStatus", "code": "active"}}
  ]}
]}
```

### 4.4 `$closure` — client-maintained transitive-closure table

Spec: [conceptmap-operation-closure.html](https://www.hl7.org/fhir/R4/conceptmap-operation-closure.html). **Not idempotent** (explicitly stated on the spec page) — it's the one operation here with real server-side state per named table.

Invocation: `POST [base]/$closure` (note: not scoped under `/ConceptMap/`).

IN: `name` (1..1 string — names the closure-table context; server-defined valid names), `concept[]` (0..* Coding — add these; zero concepts on first call = (re)initialize), `version` (0..1 string — request a resync of everything since this version; `0` = resync the whole table; can't combine with `concept`).

OUT: `return` (1..1, `ConceptMap`) — the new entries the client should merge into its local closure table. Equivalences returned are restricted to `equal`, `specializes`, `subsumes`, `unmatched`.

```
POST [base]/$closure
{"resourceType":"Parameters","parameter":[
  {"name":"name","valueString":"patient-problems"},
  {"name":"concept","valueCoding":{"system":"http://snomed.info/sct","code":"22298006"}}
]}
```
```json
{"resourceType":"ConceptMap","identifier":"49088976-...","version":"8","status":"active",
 "group":[{"source":"http://snomed.info/sct","target":"http://snomed.info/sct",
   "element":{"code":"22298006","target":[{"code":"128599005","equivalence":"subsumes"}]}}]}
```

---

## 5. NamingSystem

Spec: [namingsystem.html](https://www.hl7.org/fhir/R4/namingsystem.html). **This repo has zero implementation of this resource** — not a gap in a partial build, a total absence.

### 5.1 Element structure

| Element | Card. | Type |
|---|---|---|
| `name` | 1..1 | string |
| `status` | 1..1 | code — same `draft\|active\|retired\|unknown` |
| `kind` | **1..1** | code — `codesystem \| identifier \| root` |
| `date` | 1..1 | dateTime |
| `publisher` | 0..1 | string |
| `contact` | 0..* | ContactDetail |
| `responsible` | 0..1 | string — who maintains the namespace |
| `type` | 0..1 | CodeableConcept — extensible-bound category, e.g. `driver`, `provider`, `patient` |
| `description` | 0..1 | markdown |
| `useContext` | 0..* | UsageContext |
| `jurisdiction` | 0..* | CodeableConcept |
| `usage` | 0..1 | string |
| `uniqueId[]` | **1..*** | see below |

`kind` meaning: `codesystem` = this NamingSystem describes a code system's identity; `identifier` = describes an identifier namespace; `root` = an OID/UUID root namespace.

#### `uniqueId[]`

| Element | Card. | Type |
|---|---|---|
| `type` | 1..1 | code — `oid \| uuid \| uri \| other` |
| `value` | 1..1 | string — "the string that should be sent over the wire to identify the code system or identifier system" |
| `preferred` | 0..1 | boolean |
| `comment` | 0..1 | string |
| `period` | 0..1 | Period |

Constraints: `nsd-1` — a `root`-kind system can't have a `uuid`-type `uniqueId`. At most one `preferred=true` per `type` (`nsd-2`).

### 5.2 What NamingSystem actually is

Per the spec text directly: NamingSystem is a **registry/catalog entry**, not a semantic authority — it "represents a 'System' used within the Identifier and Coding data types," and "is frequently defined by 3rd parties that encounter the code system in use" without having authority to define the system's actual content. Multiple `NamingSystem` resources can describe the same code system (different registries' views of it), but there should only be one real `CodeSystem` for it. `uniqueId.value` is the literal string that goes into `Identifier.system`/`Coding.system` on the wire — that's the entire point of this resource: a lookup table from "what is this URI/OID" to "here's what it's for and whether it's the preferred one."

**Direct implication for this repo**: when `TerminologyFieldBinding`/`TerminologyConceptMap`/org-concept features eventually need to register a *new*, locally-invented system URI (e.g. `https://fhir-server.dev/fhir/identifier-system/<name>`, already used elsewhere per the root `CLAUDE.md`'s java_validator gotcha section) as a formally-known system, a `NamingSystem` row is the FHIR-correct way to do that — not a new ad-hoc table.

---

## 6. TerminologyCapabilities

Spec: [terminologycapabilities.html](https://www.hl7.org/fhir/R4/terminologycapabilities.html). **Also entirely absent today** (08 §7). Fetched with `GET [base]/metadata?mode=terminology`.

Purpose, precisely: CapabilityStatement describes the REST API shape; `CodeSystem` describes a vocabulary's own content; **TerminologyCapabilities describes what *this particular server* actually does with terminology** — which systems/versions it hosts, which filters/properties/operations it supports and how.

### 6.1 Element structure

| Element | Card. | Type |
|---|---|---|
| metadata block | — | same shape, `status` required |
| `kind` | 1..1 | code — `instance \| capability \| requirements` |
| `software` | 0..1 | `{name (1..1), version}` |
| `implementation` | 0..1 | `{description (1..1), url}` |
| `lockedDate` | 0..1 | boolean |
| `codeSystem[]` | 0..* | `{uri: canonical(CodeSystem), version[], subsumption: boolean}` |
| `expansion` | 0..1 | `{hierarchical, paging, incomplete, parameter[]: {name: code, documentation}, textFilter: markdown}` |
| `codeSearch` | 0..1 | code — `explicit \| all` |
| `validateCode` | 0..1 | `{translations: boolean (1..1)}` |
| `translation` | 0..1 | `{needsMap: boolean (1..1)}` |
| `closure` | 0..1 | `{translation: boolean}` |

`codeSystem[].version[]`: `{code: string, isDefault: boolean, compositional: boolean, language: code (0..*), filter[]: {code (1..1), op (1..*)}, property: code (0..*)}`.

Resource-level rule: at least one of `description`/`software`/`implementation` required. If `kind=instance`, `implementation` is required (`software` optional) — this is the shape this repo would actually publish, describing one running deployment. If `kind=capability`, `software` is required and `implementation` must be absent (a product's generic capabilities, not a specific install).

---

## 7. Registered external code systems

Spec: [terminologies-systems.html](https://www.hl7.org/fhir/R4/terminologies-systems.html) (page states its own list "is incomplete and subject to change"). These are the canonical `system` URIs to use — never invent a new URI for one of these, per the "Choosing a System URI" resolution order in [terminologies.html](https://www.hl7.org/fhir/R4/terminologies.html): (1) FHIR Code System Registry if listed — **SHALL** use; (2) publisher's own URI/OID; (3) FHIR community registry if active; (4) HL7 OID registry as `urn:oid:...`.

Systems already loaded by this repo's `app/terminology/import_/loaders/` (per the earlier survey) are marked ✅; others are common ones worth knowing the canonical URI for.

| System | Canonical URI | Notes |
|---|---|---|
| SNOMED CT ✅ | `http://snomed.info/sct` | Compositional (post-coordinated expressions have no `display`) |
| LOINC ✅ | `http://loinc.org` | |
| RxNorm ✅ | `http://www.nlm.nih.gov/research/umls/rxnorm` | |
| ICD-10-CM ✅ | — (page's visible text defers to a separate "Using ICD-10 with FHIR" page; this repo's own seed data uses `http://hl7.org/fhir/sid/icd-10-us`, confirmed against the ConceptMap index in §terminologies-conceptmaps) | |
| UCUM | `http://unitsofmeasure.org` | Case-sensitive codes |
| NDC/NHRIC | `http://hl7.org/fhir/sid/ndc` | |
| CVX (vaccine codes) | `http://hl7.org/fhir/sid/cvx` | |
| AMA CPT | `http://www.ama-assn.org/go/cpt` | |
| ISO 3166 (country/region) | `urn:iso:std:iso:3166` | |
| ATC | `http://www.whocc.no/atc` | |
| IETF BCP 47 (languages) | `urn:ietf:bcp:47` | Usually used bare in a `code` element, system implied — **this is the exact system the root `CLAUDE.md`'s java_validator gotcha warns triggers a live external ValueSet check** |
| IETF BCP 13 (MIME types) | `urn:ietf:bcp:13` | Same gotcha category — `Attachment.contentType` |
| HL7 v2 tables | `http://terminology.hl7.org/CodeSystem/v2-[X]` | e.g. `v2-0203`; some need a version suffix like `v2-0123/2.3+` |
| HL7 v3 code systems | `http://terminology.hl7.org/CodeSystem/v3-[X]` | e.g. `v3-GenderStatus` |
| DICOM | `http://dicom.nema.org/resources/ontology/DCM` | |
| GTIN | `https://www.gs1.org/gtin` | Usable in both `Coding` and `Identifier` |
| UMLS source (unregistered) | `http://www.nlm.nih.gov/research/umls/[SAB]` | `[SAB]` = lowercase UMLS source abbreviation; spec warns the real registered URI may later differ |

Genetics-specific (HGNC, ENSEMBL, RefSeq, ClinVar, HGVS, dbSNP, OMIM, PharmGKB, …) are listed on the same page if that scope is ever needed — not reproduced here since nothing in this repo touches genomics yet.

### 7.1 Known Identifier Systems (separate registry, for `Identifier.system`)

Spec: [identifier-registry.html](https://www.hl7.org/fhir/R4/identifier-registry.html) — a **different** registry from §7 above: this one is specifically for `Identifier.system` values (SSNs, license numbers, etc.), not `Coding.system`. Examples: `http://hl7.org/fhir/sid/us-ssn` (US SSN, OID `2.16.840.1.113883.4.1`, written without dashes), `http://hl7.org/fhir/sid/us-npi` (US National Provider Identifier), `urn:dicom:uid`, `urn:oid:2.16.840.1.113883.4.3.2` (Alaska driver's license — other states follow the same OID-root pattern). The spec notes this page does **not** explain its relationship to `NamingSystem` explicitly — treat §5.2's general NamingSystem-as-registry role as the mechanism, and this page as a curated "already known, don't reinvent" shortlist within it.

### 7.2 FHIR's own built-in ValueSets/ConceptMaps

Spec: [terminologies-valuesets.html](https://www.hl7.org/fhir/R4/terminologies-valuesets.html) / [terminologies-conceptmaps.html](https://www.hl7.org/fhir/R4/terminologies-conceptmaps.html). FHIR publishes its own small built-in value sets (`administrative-gender`, `publication-status`, `address-use`, `marital-status`, …) under `http://hl7.org/fhir/ValueSet/<name>`, and ~50+ built-in ConceptMaps mapping resource-specific status codes to canonical cross-resource status codes, plus v2/v3 interop maps (`FHIR-v3-Address-Use`, `v2.AdministrativeGender`, etc.) and one worked SNOMED CT → ICD-10-CM example (fracture of ulna, target system `http://hl7.org/fhir/sid/icd-10-us`). None of this needs to be re-authored — these are HL7-published resources this server could optionally cache/reference rather than build.

---

## 8. What this repo currently has vs. what the standard requires

[08-fhir-r4-standard-compliance-gap-analysis.md](08-fhir-r4-standard-compliance-gap-analysis.md) already states the gap list; this section cites the primary source behind each claim now that it's been fetched directly, rather than from secondhand summary.

| 08's claim | Confirmed against |
|---|---|
| §4: `ConceptMap.equivalence` is a required-binding 10-value enum, not a free string | §4.2 above — exact 10 codes with verbatim definitions, from [valueset-concept-map-equivalence.html](https://www.hl7.org/fhir/R4/valueset-concept-map-equivalence.html) |
| §6: `$subsumes` outcome is a 4-value enum (`equivalent\|subsumes\|subsumed-by\|not-subsumed`) | §2.6 above, from [valueset-concept-subsumption-outcome.html](https://www.hl7.org/fhir/R4/valueset-concept-subsumption-outcome.html) — and confirmed `TerminologyRelationship` already stores the IS-A edges §2.3 says `$subsumes` needs |
| §1: `$expand` takes a canonical `url` (+`\|version`), not an internal PK, and returns a full `ValueSet` resource, not a flat list | §3.2 above, from [valueset-operation-expand.html](https://www.hl7.org/fhir/R4/valueset-operation-expand.html) — also surfaced that `$expand` has ~18 more optional parameters (paging, filtering, language, version pinning) than this repo's current two (`q`, pagination) |
| §5: `/validate` stands in for `ValueSet/$validate-code`, not `CodeSystem/$validate-code` | §2.6/§3.2 above confirm these are two genuinely different operations with different IN-parameter shapes (ValueSet's has `context`/`valueSetVersion`; CodeSystem's has `codeSystem`/`abstract` differently scoped) — worth deciding which (or both) this repo actually needs |
| §8: designations (synonyms/translations) exist in the DB but aren't surfaced as FHIR `designation[]` | §2.6's `$lookup` OUT shape confirms `designation[]` (`{language, use, value}`) is exactly the FHIR shape `TerminologyConceptSynonym`/`TerminologyConceptTranslation` should map onto |
| *(new, not in 08)* `NamingSystem` has zero implementation | §5 above — confirmed via direct fetch, not just absence-by-omission |
| *(new, not in 08)* No `TerminologyCapabilities` | §6 above — confirmed via direct fetch; this is the resource 08 §7's "no CapabilityStatement entry" gap should actually target (CapabilityStatement is the REST-API-shape document every resource already needs; TerminologyCapabilities is the terminology-specific one, and this repo has neither for terminology) |

Nothing fetched here contradicts 08's existing gap list — it's confirmed accurate throughout. The one correction: 08 frames the missing capability declaration as "no `CapabilityStatement` entry," but per §6, the terminology-specific document a client actually needs is `TerminologyCapabilities`, a separate resource type — both may eventually be worth publishing, but they're not the same gap.

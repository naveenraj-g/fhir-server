# FHIR profiling, extensions, and org-defined business rules — a design report

**Status: design/discussion only. No code in this repo implements anything below yet.**
This answers three questions asked together: (1) is the base → country → organization
profile layering idea correct, (2) how do resource-level extensions fit in, (3) how do
hospitals/clinics define their own validation/business rules — and closes with what it means
for "should the DB layer enforce enums."

Everything FHIR-specific below is checked against the actual R4 spec
(`hl7.org/fhir/R4/profiling.html`, `hl7.org/fhir/R4/extensibility.html`), not recalled from
memory, because the one rule that makes or breaks this whole design — cardinality can only
ever be narrowed, never widened, as you go down the layers — is a precise spec rule, not a
style preference.

---

## 1. Verdict on the three-layer idea

**Yes, base → country → organization is the right shape** — it's exactly how real-world FHIR
profiling already works (HL7's own pattern: base R4 → a national base like US Core/IN Core →
an institution's own profile deriving from that). You're not inventing a new concept; you're
describing standard FHIR profile derivation (`StructureDefinition.baseDefinition` +
`derivation = constraint`), applied three levels deep instead of two.

**One rule governs the entire design and has to be enforced mechanically, not just assumed:**

> A profile can only make an inherited element _more_ restrictive than its parent, never less.
> A base element of `0..1` can become `0..0` or `1..1` under a profile, but never `0..*`. A
> required (`required`) terminology binding can never be loosened to `extensible` by a child
> profile. Whatever a child profile allows must already have been allowed by its parent.

This matters concretely for your design because **organization admins will be authoring
profiles at runtime through some future UI**, not through a reviewed PR. Nothing stops a
hospital admin from accidentally trying to make a country-mandated required field optional
unless something _mechanically_ rejects that at authoring time. Section 4 covers the
authoring-time guard this requires — it's not optional for a system where profile authorship
is self-service.

**The "factory pattern" instinct is right, but implement it as data selection, not a class
hierarchy.** A country profile isn't logic — it's a fixed set of constraints over the base
resource. If you build `USOrganizationProfile`, `INOrganizationProfile`, ... as Python
classes, every new country or every spec update becomes a code change and a deploy. The
correct shape:

- Country profiles are **data** (JSON/YAML, structurally close to a real FHIR
  `StructureDefinition`), checked into the repo or loaded from a profile registry.
- A thin factory/registry (`ProfileRegistry.for_country(code)`) resolves `config.yaml`'s
  country setting to the right profile bundle at startup and caches it. The "factory
  pattern" lives in that one resolver function, not in a parallel class per country.
- Adding a new country is: add a JSON file, add a config entry. No deploy of new Python
  logic required.

Organization-level profiles can't be static data in the repo at all — they're created at
runtime by tenants, so they have to live in the database and be authored through an
(eventually-built) admin API, which is explicitly out of scope for this report per your
instruction to ignore the API layer for now. What _is_ in scope is the shape they're stored
in and how they get validated — covered below.

---

## 2. What "a profile" actually needs to express, precisely

Grounding this in the spec so the storage design in §3 has a real target, not a guess.
`StructureDefinition` profiles work through five independent mechanisms — a profile can use
any combination of these per element:

| Mechanism                 | What it does                                                                                           | Example                                                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cardinality narrowing** | Tightens `min`/`max` within what the parent already allows                                             | Base `Organization.name` is `0..1`; a hospital profile could make it `1..1`                                                                   |
| **Fixed/pattern values**  | Locks an element to one value, or a pattern complex types must match                                   | A clinic profile fixes `Organization.type` to always be `prov`                                                                                |
| **Must-support**          | Flags an element systems must be able to populate/use                                                  | Doesn't change validity, just conformance expectations — lower priority for you                                                               |
| **Terminology binding**   | Narrows which codes are valid, and how strictly (`required` / `extensible` / `preferred` / `example`)  | A country profile could bind `Organization.type` to a government-published code system as `required`                                          |
| **Slicing**               | Splits a repeating element into named sub-lists with per-slice rules                                   | Not urgent for Organization; relevant later for things like `Patient.identifier` (MRN slice vs. SSN slice, each with its own required system) |
| **Invariants**            | Arbitrary FHIRPath boolean expressions, with a severity, evaluated against the whole resource instance | `org-1` itself — _"name or identifier required"_ — is exactly this kind of rule, already in the base spec                                     |

**The important realization for your "business rules" question (§5): invariants are already
the FHIR-native mechanism for exactly what you're describing**, as long as the rule is
expressible as a statement about one resource instance. `org-1` is proof this project already
needs this mechanism — it just isn't built generically yet.

---

## 3. Storage design for the profile chain

A profile, at any layer, needs the same shape: _what resource type it constrains_, _what its
parent is_, _its own list of constraints_, and _who owns it_. One generalized model handles
all three layers instead of three different mechanisms:

```
fhir_profile
  id
  resource_type         -- "Organization", "Patient", ...
  scope_level            -- 'base' | 'country' | 'organization'
  scope_id                -- NULL for base; country code for country; org_id for organization
  parent_profile_id       -- FK to fhir_profile.id (NULL only for the base-R4 row)
  canonical_url            -- globally unique, FHIR-style (e.g. "https://yourorg.dev/fhir/StructureDefinition/org-in-clinic")
  version
  status                     -- draft | active | retired
  structure                    -- JSONB: cardinality overrides, fixed/pattern values, bindings, slicing — see below
  created_by / created_at / updated_by / updated_at
  UNIQUE(resource_type, scope_level, scope_id, version)
```

`structure` is where the actual constraints live — a JSONB document shaped like a trimmed
FHIR `StructureDefinition.differential` (only the elements a given layer actually touches,
not a full copy of the parent):

```json
{
  "elements": {
    "name": { "min": 1 },
    "type": { "binding": { "strength": "required", "valueSetUrl": "..." } },
    "active": { "fixed": true }
  },
  "invariants": [
    {
      "key": "org-clinic-1",
      "severity": "error",
      "expression": "telecom.where(system='phone').exists()",
      "description": "Clinics must record at least one phone contact."
    }
  ]
}
```

This is this project's own working subset of `StructureDefinition`, not a reinvention of it —
storing the full spec-shaped resource would work too, but a trimmed differential is smaller,
easier to diff between versions, and enough to drive a validator. If you ever need to
interoperate with real `StructureDefinition` resources (publish your profiles for external
conformance tools), add a serializer that expands this into the real shape — don't design the
runtime storage around that from day one.

**This generalizes the terminology-binding mechanism that already exists in this codebase.**
`app/models/terminology/terminology.py`'s `TerminologyFieldBinding` already maps
`(resource_type, field_name) → value_set + binding_strength` — but as a single global row per
field, with no layering. That's a proto-profile system for exactly one of the five mechanisms
in §2 (terminology binding), and nothing else. The natural path is **not** to build
`fhir_profile` as something unrelated — it's to either (a) fold field-binding resolution into
`fhir_profile.structure.elements[field].binding`, scoped per layer, or (b) add `scope_level`/
`scope_id` to `TerminologyFieldBinding` itself and keep it as the terminology-specific half of
the system while `fhir_profile` owns cardinality/fixed-values/slicing/invariants. Either
works; (a) is more consistent (one source of truth per resource type), (b) is less migration
work on an already-shipped table. Worth deciding once you're ready to build, not now.

### Profile resolution

Given `(org_id, resource_type)`, resolve the chain once (cache it — it changes rarely):

```
org_profile = fhir_profile.where(scope_level='organization', scope_id=org_id, resource_type=X, status='active')
country_profile = fhir_profile.where(scope_level='country', scope_id=settings.fhir.country, resource_type=X, status='active')
base_profile = fhir_profile.where(scope_level='base', resource_type=X)  -- always exists, ships with the repo

chain = [base_profile, country_profile, org_profile]  -- apply in order, each layer only tightening the last
```

Merge left-to-right into one effective constraint set, and **reject the merge outright** (not
just at validation time, but at the moment a profile is _saved_) if any layer tries to widen
what its parent already constrained — this is the mechanical guard from §1.

---

## 4. The validation pipeline, and where it runs

Confirms your instinct: **not in the database.** The pipeline sits in the service layer,
before the repository write — the same place `_validate_reference` already runs for reference
existence checks today:

```
Router → Service.create(payload, org_id, actor)
            │
            ├─ 1. resolve_profile_chain(org_id, "Organization")   -- cached
            ├─ 2. validate_structure(payload, chain)               -- cardinality, fixed/pattern values
            ├─ 3. validate_terminology(payload, chain)              -- delegates to the EXISTING
            │                                                          TerminologyService.validate()
            │                                                          for each coded field, now
            │                                                          chain-aware instead of global-only
            ├─ 4. validate_invariants(payload, chain)                 -- FHIRPath, incl. org-1 generalized
            ├─ 5. validate_business_rules(payload, chain, actor)      -- §5, only for rules that
            │                                                           aren't expressible as (4)
            └─ 6. Repository.create_full(...)                          -- only reached if 1–5 all pass
```

Every failure becomes the same `BusinessRuleViolationError`/`OperationOutcome` shape this
codebase already uses for every other domain-rule rejection — profile validation is just
another source of 422s, not a parallel error system.

**This also resolves the org-1 question left open on Organization.** Once this pipeline
exists, `org-1` ("name or identifier required") is simply the base profile's own invariant —
evaluated the same way as every other layer's invariants, at create _and_ patch (since the
pipeline runs on every write, not just create). No bespoke Pydantic validator needed; it falls
out of building this generically.

**Build vs. hand-roll FHIRPath:** don't write a FHIRPath evaluator from scratch.
[`fhirpathpy`](https://pypi.org/project/fhirpathpy/) is a maintained Python port used by other
FHIR server stacks — evaluate `invariant.expression` against the resource dict and check the
boolean result. This is the one piece of this whole design worth reaching for an existing
library over, since a hand-rolled FHIRPath subset is a long tail of edge cases for something
that's supposed to be the trustworthy validation layer.

---

## 5. Org-defined extensions

You're right that this is resource-level, and the spec backs that framing directly: an
`Extension.url` is a globally unique absolute URI naming a separate `StructureDefinition` (of
type `Extension`) that defines the extension's own cardinality, value type, and binding —
_"An extension SHALL have either a value... or sub-extensions, but not both."_ Practically,
that means **an extension is just another profile artifact**, reusing the exact same
`fhir_profile` storage from §3 with `resource_type = "Extension"`:

```
fhir_profile (resource_type="Extension")
  canonical_url: "https://clinic-x.dev/fhir/StructureDefinition/preferred-pharmacy"
  scope_level: 'organization', scope_id: <org_id>
  structure: { "context": ["Organization"], "valueType": "Reference", "min": 0, "max": 1 }
```

**Schema changes this needs**, scoped to resource level only as you said:

- One new column per resource table: `extension` (`JSONB`, nullable, default `[]`) storing
  the raw `[{url, valueType, value}, ...]` array. Not one column per extension — extensions
  are dynamic and org-defined, so they can't be individually typed Pydantic fields.
- One new generic Pydantic field: `extension: list[ExtensionInput] | None` added explicitly
  to each `CreateSchema`/`PatchSchema`. This is the right way to let extensions through
  `extra="forbid"` — an explicit typed field, not a loosened model config.
- **Closed-world validation, not open:** at write time, every `extension[].url` present on the
  payload must resolve to a registered `fhir_profile` (resource_type="Extension") entry
  somewhere in the org's resolved chain, with its own `context` including the current
  resource type. An unregistered `url` should be rejected (422), not silently accepted — this
  is what "100% FHIR standard, nothing extra, nothing untracked" actually means in practice
  for a field designed to carry arbitrary data.
- **`modifierExtension` needs a stricter rule than `extension`, per spec**: _"If it is not
  safe for an application processing the content of the resource to ignore the extension it
  SHALL be represented using modifierExtension."_ If/when you support it, any unrecognized
  `modifierExtension` must hard-fail closed with no exceptions — that's a spec safety rule,
  not a house style choice.
- **Mapper layer**: `to_fhir_*` emits the JSONB array as `resource["extension"]` directly
  (already spec-shaped, no transform needed). `to_plain_*` is an open decision worth deciding
  deliberately rather than defaulting: pass the raw array through as-is (simplest, keeps
  dynamic data dynamic), since flattening arbitrary org-defined extensions into named plain
  fields isn't possible without per-org schema generation.

---

## 6. Org-defined business/validation rules beyond structure

Split this deliberately into two tiers — conflating them makes "is this resource valid per
profile X" an ambiguous question, since one tier is spec-portable and the other isn't:

**Tier 1 — expressible as a FHIRPath invariant on one resource instance.** This is most of
what "clinics define their own validation rules" will actually turn out to mean in practice
("every Patient we create must have a phone number," "our Organizations must always have a
`type`"). These are just more rows in `fhir_profile.structure.invariants` (§3), scoped to the
organization layer, evaluated by the same pipeline step as `org-1`. No separate system needed
— this is the generic mechanism FHIR already gives you for exactly this.

**Tier 2 — genuinely cross-resource, workflow, or external-lookup rules** ("this Encounter's
practitioner must already have an active PractitionerRole at this Location," "reject if this
is the patient's 3rd no-show this month"). FHIRPath over a single resource instance can't
express these — they need their own explicitly-scoped mechanism, evaluated as pipeline step 5
in §4, _after_ structural/invariant validation passes.

**Strong recommendation for Tier 2: do not let organizations upload arbitrary executable
code.** This is a multi-tenant system — a hospital's "custom business rule" running as
real Python/JS in your process is a sandbox-escape and data-exfiltration risk the moment one
tenant's rule can be written to read another tenant's data or exhaust shared resources. The
safer, still genuinely useful option is a **declarative, non-Turing-complete rule format**
(something in the shape of JSONLogic or a small whitelisted expression grammar) that can only
express comparisons/boolean logic over the fields of the resource being validated plus a
narrow, explicitly-allowed set of lookups (e.g. "does a PractitionerRole exist matching X,
scoped to this org") — never arbitrary queries, never arbitrary code execution. This is a
genuine build decision with real security weight, not a detail — flagging it now so it's
decided deliberately rather than inherited from whatever's fastest to prototype.

---

## 7. Back to the original question: should the DB stop enforcing enums?

**Partially yes — and the current schema already agrees with you in most places; the
remaining Postgres `Enum` columns split into two categories that need different answers.**

**Category A — required-binding, spec-fixed value sets. Keep these as Postgres `Enum`.**
FHIR's `required` binding strength means _no profile, at any layer, can ever add a code
outside that value set_ — narrowing-only cuts both ways here: a required binding can be
narrowed further but never swapped or widened. `PatientGender`
(`app/models/patient/enums.py`), `IdentifierUse`, `AppointmentStatus` — these are permanently
closed by the base spec itself, for every country and every organization, forever. A Postgres
`Enum` here costs nothing (no legitimate value will ever be rejected) and buys real integrity
and a smaller index. Don't touch these.

**Category B — extensible/preferred/example-binding CodeableConcept fields, or anything a
profile is meant to actually constrain. These should not be (and mostly already aren't)
Postgres enums — they should be `String`, validated dynamically against the resolved profile
chain's terminology binding (§4, step 3) through the already-existing `TerminologyService`.**
This is most of `type_code`/`type_system`/etc. across the codebase today, so the instinct is
mostly already reality — the useful next step isn't a sweeping rewrite, it's a **mechanical
audit** (same spirit as the earlier R4/R5 conformance audit): for every Postgres `Enum`
column in the schema, look up that element's actual binding strength in the base R4 spec.
`required` → leave as `Enum`. Anything else → flag as a candidate to become `String` +
profile-validated, resource by resource.

**One category this report is explicitly not touching: the Reference `_type` discriminator
enums** (`OrganizationReferenceType`, `PatientLinkOtherType`, etc.). These have nothing to do
with terminology bindings or profiles — they're the structural type-tag half of the
flattened-reference pattern (`CLAUDE.md`'s "Two reference conventions" section), and exist
because a polymorphic `Reference` field's target type has to be stored _somehow_ without a
real FK. Don't conflate "stop enforcing terminology enums in the DB" with "remove the
reference-type enums" — they're solving an unrelated problem and should stay exactly as they
are.

---

## 8. Suggested order of work

This is a genuinely large feature — sequence it so each phase is independently useful rather
than needing the whole thing before anything works:

1. **Generalize `TerminologyFieldBinding`** to carry `scope_level`/`scope_id` (§3's option b)
   — smallest change, immediately gives country/org-level terminology binding overrides using
   infrastructure that already exists and already works.
2. **Build `fhir_profile`** (§3) for cardinality/fixed-values/invariants, starting with just
   the base layer — this is what finally gives `org-1` (and any resource's analogous
   invariant) a real, generic home instead of a one-off validator.
3. **Wire the validation pipeline** (§4) into one resource's service layer first — Organization
   is the natural pilot, since it's the resource currently being hardened to strict R4 shape.
4. **Add country-layer profiles**, config-selected (§1's factory), once the base layer is
   proven on Organization.
5. **Add organization-layer profiles** — this is the point where you need at least a minimal
   authoring surface (even an internal-only endpoint), since these are created at runtime,
   not shipped as data.
6. **Extensions** (§6) — natural to build right after org-layer profiles exist, since an
   extension definition is stored the same way.
7. **Tier 2 business rules** (§7) — last, and only after deciding the rule-language security
   question deliberately, not under feature-delivery pressure.

## 9. Decisions this report is deliberately not making for you

- Fold terminology bindings into `fhir_profile` vs. extend `TerminologyFieldBinding`
  in place (§3).
- Whether `to_plain_*` passes `extension[]` through raw or attempts any flattening (§6).
- The actual rule language for Tier 2 business rules — JSONLogic, a custom DSL, or something
  else (§7) — this one specifically needs a security review before being settled, not just an
  engineering preference.
- Whether unknown `extension` URLs are hard-rejected or merely flagged — this report
  recommends hard-reject for consistency with "100% strict FHIR," but it's your call on how
  strict the write path should be during a migration/onboarding period.

---

# Reference Conversation (NVM)

Short answer: yes, this is the right approach — and it's not just "a valid approach," it's literally how real FHIR validators (HL7's own reference validator, HAPI FHIR's validation module) are architected. You've independently arrived at the standard design. Let me confirm the details and be honest about the scope.

StructureDefinition is indeed the one resource for all of this. There is no separate FHIR resource for "business rules" or "custom validation logic" — profiles, extensions, and constraints/invariants all live in the same place:

- Profiling (narrowing an existing resource): a StructureDefinition with derivation: "constraint" and baseDefinition pointing at its parent, redeclaring elements in its differential to tighten cardinality (e.g. Organization.name 0..1 → 1..1), fix/pattern a value, add slicing, or flag mustSupport.
- Extensions: also a StructureDefinition, just with type: "Extension" and a context[] saying where it's allowed to attach.
- Business rules / invariants: ElementDefinition.constraint[] — the exact mechanism behind org-1/2/3 we already found.

One StructureDefinition, three jobs. There's no alternate resource doing any of this in parallel — the supporting cast (ValueSet/CodeSystem for terminology a binding points at, ImplementationGuide for packaging a set of these together for publication, CapabilityStatement for a server declaring which profiles it claims to support) all exist around StructureDefinition, none of them carry rule logic themselves.

So "one engine, fed different StructureDefinitions, chained by baseDefinition" is exactly right conceptually — base R4, country profile, org profile become three documents walked by the same code, not three code paths. That's precisely the HL7/HAPI model.

Where I want to be straight with you: a complete engine is a much bigger undertaking than anything built so far this session. A full profile-validation engine needs, at minimum:

- Snapshot generation — merging a profile's differential against its base's full snapshot recursively up the baseDefinition chain (the differential only lists changed elements; you need the merged, fully-resolved element list to validate against)
- Slicing — arrays split into named sub-constraints with discriminators (e.g. "this list must contain exactly one identifier sliced by system = 'npi'")
- Binding validation — codes checked against an actual ValueSet, which itself may need expansion (potentially contacting a terminology server)
- Extension validation — resolving a referenced extension's own StructureDefinition and recursing into it
- Invariant execution — the FHIRPath piece we already discussed

Each of those is its own non-trivial subsystem. The real HL7 Java validator is a mature, decade-refined codebase specifically because of this surface area — it's not a weekend build, and there isn't a mature "do all of this" Python library to lean on (that's a known gap in the Python FHIR ecosystem, part of why fhir.resources only goes as far as Pydantic-model-level structure).

Given that, there are really two honest paths, and I don't think I should pick for you without flagging both:

1. Build a deliberately scoped-down version of this engine — not the full spec surface, just the subset your actual profiles need: cardinality tightening, fixed values, constraint-invariant evaluation (bounded FHIRPath subset), maybe simple required-binding checks. This matches how the base layer was built (checked empirically against what the data actually requires, not against the full spec surface) and is realistic to grow incrementally, resource by resource. No slicing, no terminology-server integration, until something genuinely needs it.
2. Delegate to HL7's own reference validator (the validator_cli.jar, or a REST sidecar wrapping it — this pattern is common enough that an official fhir-validator-wrapper HTTP service exists specifically so non-Java apps can call it) and point it at your own authored StructureDefinitions for the country/org layers. You get full spec-complete validation for free, maintained by HL7, at the cost of introducing a JVM dependency/sidecar into what's currently a pure-Python stack — a bigger architectural commitment than a pip package, worth deciding deliberately rather than backing into.

You mentioned you want to go study ElementDefinition field-by-field first — that's exactly the right move before committing to either path, since it'll tell you concretely which of those subsystems (slicing? bindings? just invariants + cardinality?) your real country/org profiles actually need, which is what should drive the scope decision rather than trying to cover the whole spec upfront.

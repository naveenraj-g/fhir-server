# Use case: mustSupport and defaultValue[x]

Two mechanisms grouped in one file because both share a common trait: neither one is a hard
*structural* validation rule the way cardinality/`fixed[x]`/invariants are — both change
behavior without ever, by themselves, making an otherwise-valid instance invalid.

## `mustSupport`, concretely

**Scenario:** a country profile wants to require that every system claiming to implement it can
actually *populate and act on* `Organization.telecom`, without going as far as making it
structurally required (`min: 1`) — because a brand-new Organization genuinely might not have a
phone number on file yet at the moment of creation, and rejecting the write over that would be
too strict. What the profile wants instead is a conformance expectation: *"if your system
implements this profile at all, it must be capable of sending/receiving this field when
present — you may not silently drop it."*

```json
{
  "path": "Organization.telecom",
  "mustSupport": true
}
```

No `min`/`max` change at all — `Organization.telecom` stays `0..*`, exactly as base R4 defines
it. The only thing that changed is a conformance expectation, not a structural one. Per
[`10-element-flags.md`](../10-element-flags.md), this is deliberately a different kind of rule
from everything else in this folder's use cases: a validator checking pure instance conformance
can legitimately pass an instance that omits a `mustSupport` field, because `mustSupport` is a
promise about *system capability*, not about *this specific instance's completeness*.

**What this would actually mean for this project, concretely:** if `Organization.telecom` were
flagged `mustSupport` under some profile, this project's own repository/mapper code would need
to guarantee it never silently drops a submitted `telecom[]` array (uses it in storage, returns
it faithfully on read) — which, as it happens, is already true today regardless of any profile
flag, simply because the Organization rework this session treats every base-spec field as fully
supported. `mustSupport` becomes operationally meaningful the moment this project's own
implementation becomes *incomplete* relative to the base spec somewhere (a field accepted on
write but silently dropped on a particular read path, for instance) — it's a guardrail against
exactly that kind of silent gap, formalized as a declared conformance claim.

## `defaultValue[x]`, concretely

**Scenario:** a tenant wants every Organization created through their own workflow to be treated
as active unless explicitly marked otherwise — but doesn't want to make `active` a required
field (some automated import processes genuinely don't know the status at creation time).

```json
{
  "path": "Organization.active",
  "defaultValueBoolean": true
}
```

Per [`04-data-types-and-choice-elements.md`](../04-data-types-and-choice-elements.md)'s table:
this says "if `active` is absent from the instance entirely, treat it as `true`" — it does not
make the field required, and critically, it's **not the same as the application simply writing
`true` into the database when nothing was submitted.** The FHIR-spec meaning is about how a
*reader* should interpret an absent field, not a server-side substitution performed at write
time. If this project's write path already fills in `active = true` when nothing is submitted
(worth checking — `OrganizationModel.active` is currently `nullable=True` with no default,
per `app/models/organization/core.py`, meaning an omitted `active` is stored and returned as
genuinely absent, `null`, not `true`), then implementing `defaultValue[x]` correctly would mean
either (a) actually writing the default value into storage at create time under this profile, or
(b) leaving storage as `null` and having every *reader* of the resource apply the default at
read time — these are two different implementations of the same spec concept, and which one is
right depends on whether other parts of the system need to distinguish "explicitly set to
false-equivalent" from "never set at all," which a pre-filled default would permanently erase.

## Why neither of these is covered by `app/fhir/validation/base_r4.py` today

Both are **conformance/interpretation** concerns, not **structural validity** concerns —
`fhir.schema.json`'s JSON Schema has no way to express either one (there's no JSON Schema
concept of "this field is optional, but a conformant system must still handle it," nor "treat an
absent field as if it were this value"). Both would need to be implemented as their own explicit
logic in the profile-resolution/validation pipeline described in
`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §4 — neither exists today.

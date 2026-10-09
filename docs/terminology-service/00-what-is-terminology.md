# What Is "Terminology," and Why Does a FHIR Server Need a Service for It?

Start here if you've never worked with FHIR, healthcare data, or this
subsystem before. There's no code, no schemas, no table names in this file
— just the ideas, explained in plain language, that everything else in
`docs/terminology-service/` builds on. If you already know what a code
system, value set, or concept map is, skip ahead to the
[README](README.md).

## The problem: everyone codes the same thing differently

Imagine three different hospital computer systems all need to record "this
patient had a blood glucose test."

- System A calls it `2345-7`.
- System B calls it `GLUC`.
- System C just writes the English words "Glucose [Mass/volume] in Blood."

All three mean the exact same real-world lab test. But if a piece of
software — say, one trying to flag every diabetic patient's recent glucose
readings across all three hospitals — just compares these strings, it will
conclude they're three unrelated things. It will miss data, or worse, merge
the wrong things together (what if `GLUC` means something slightly
different at System B than at System A?).

This is the problem "terminology" solves: **giving every meaningful medical
concept — a lab test, a diagnosis, a procedure, a drug, a body site, a unit
of measure — one standard, unambiguous code**, so that software built by
different vendors, in different hospitals, in different countries, can
agree on what a piece of data actually means without a human reading it.

This has nothing to do with "terminology" in the everyday sense of
"vocabulary" or "jargon." In this codebase, **a "terminology service" is a
specific piece of infrastructure**: a lookup system for standardized medical
codes, the rules about which codes are valid where, and the mappings
between different coding systems.

## A code system: a dictionary of codes

A **code system** (sometimes called a "vocabulary" or "coding system") is a
published list of codes and what each one means — like a dictionary, except
every entry is a code instead of a word. Real-world examples this project
actually loads data from:

- **LOINC** — codes for lab tests and clinical measurements. Code `2345-7`
  means "Glucose [Mass/volume] in Blood."
- **SNOMED CT** — codes for clinical findings, diagnoses, procedures,
  body structures, and much more. Tens of thousands of concepts.
- **ICD-10-CM** — diagnosis codes, the kind used for billing and
  statistics.
- **RxNorm** — codes for medications and drug products.

A made-up, simplified example of what a tiny code system might look like:

| Code | Meaning |
|---|---|
| `A1` | Common cold |
| `A2` | Seasonal flu |
| `A3` | Chickenpox |

That table — a fixed, named collection of codes and their meanings — is
what this project calls a **CodeSystem**.

## A concept: one entry in that dictionary

A **concept** is just one single row in a code system — one code plus its
meaning. `2345-7` → "Glucose [Mass/volume] in Blood" is one concept, living
inside the LOINC code system. "One concept" is the smallest unit this whole
subsystem deals with.

## A value set: the relevant slice, not the whole dictionary

No single field in a medical record should be allowed to contain *any*
code from *any* code system. A field like "status of this lab order" should
only ever contain something like `requested`, `in-progress`, `completed`,
or `cancelled` — not an arbitrary SNOMED diagnosis code, and not every
single status code that has ever existed for any purpose anywhere.

A **value set** is a curated, purpose-built subset of concepts — the
specific list of codes that are actually legal for one particular use. A
value set can pull concepts from one code system or several. "The allowed
statuses for a lab order" is a value set. "The allowed country codes" is a
value set. Where a code system is the whole dictionary, a value set is a
hand-picked page torn out of it (or several pages, from several
dictionaries) for one specific purpose.

## A binding: which field is restricted to which value set

A **binding** is the rule connecting a specific field, on a specific kind
of record, to the value set that governs it. "An Organization's `type`
field can only be one of these 12 codes" is a binding. Without a binding,
a value set is just a list sitting unused — the binding is what makes it
actually matter for a particular piece of data entry.

FHIR (the healthcare-data standard this whole server implements — see the
root `CLAUDE.md` for what FHIR is at the project level) defines how
*strict* a binding is supposed to be:

- **required** — the value must come from this value set. No exceptions.
- **extensible** — it should come from this value set, but a different
  code is tolerable if nothing in the value set fits.
- **preferred** / **example** — purely advisory; suggests good codes to
  use but doesn't restrict anything.

(This project's own implementation of binding strength is narrower than
the full spec — see
[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md)
once you're ready for the implementation-level detail.)

## A concept map: a translation table between two dictionaries

Sometimes the same real-world thing has two different, equally valid codes
in two different code systems — recall the glucose test example at the top:
LOINC's `2345-7` and some lab's internal `GLUC`. A **concept map** is a
translation table that records "this code, in this system, means the same
thing as that code, in that system" — so software can convert a value from
one vocabulary to another without a human re-mapping it by hand every time.
Translation (concept maps) and validation (value sets + bindings) are two
different jobs that happen to share the same underlying dictionary of
codes and concepts.

## This project's own twist: org-scoped customization

Standard code systems (LOINC, SNOMED, etc.) are maintained by outside
standards bodies — nobody using this server gets to edit them. But real
hospital networks ("orgs," in this codebase's terms — see the root
`CLAUDE.md`'s Multi-Tenancy section) sometimes need something a little
different:

- **An org-owned concept** — sometimes a hospital network has its own
  internal code for something that doesn't have a standard equivalent yet
  (an internal department code, a locally-invented procedure variant, …).
  This subsystem lets an org add its own brand-new concept to an existing
  code system, scoped so it's only visible/usable for that org — without
  touching or colliding with the canonical, standards-body-maintained
  codes.
- **A display override** — sometimes the *code* is right (a hospital does
  want to use the standard LOINC code for a lab test) but the org wants a
  different human-readable label shown for it — maybe their clinicians
  are used to different phrasing, or a different language's wording. A
  display override doesn't invent a new code; it just relabels the display
  text of a code that already exists, for that org only.

These are two deliberately different operations — one invents a new code,
the other relabels an existing one — and this project keeps them as two
separate mechanisms rather than one, because conflating them would make it
impossible to tell, later, which codes in the system are "real" (standard,
portable, meaningful to any other system reading this data) versus purely
local labeling. See
[07-org-concepts-and-display-overrides.md](07-org-concepts-and-display-overrides.md)
for exactly how that distinction is implemented.

## Where to go next

With those six ideas — code system, concept, value set, binding, concept
map, and this project's org-scoped additions — you have everything you
need to read the rest of this folder. Go to the [README](README.md) for
the implementation-level map of how all of this is actually built: which
database tables, which API routes, which background scripts load the real
LOINC/SNOMED/ICD-10/RxNorm/FHIR data in.

# Split a Large Resource File into a Per-Sub-Resource Package

Converts a single large file (`app/models/<resource>/<resource>.py`, `app/repository/<resource>_repository.py`, `app/services/<resource>_service.py`, `app/routers/<resource>.py`, `app/schemas/<resource>/input.py`, `app/schemas/<resource>/response.py`) into a same-named package directory with one file per sub-resource. This is the pattern Patient, Practitioner, and Organization all use — apply it to any resource once its file becomes hard to navigate (roughly once it has 4+ sub-resources or crosses ~500 lines).

## ARGUMENTS: $RESOURCE $LAYER

`$RESOURCE` = the resource name (e.g. `Patient`). `$LAYER` = which file to split (`model`, `repository`, `service`, `router`, `schema-input`, or `schema-response`). Run this once per layer — they're independent.

---

## The core trick: module → package conversion

Python treats `from app.foo.bar import X` identically whether `bar` resolves to `bar.py` or `bar/__init__.py`. So converting `app/schemas/patient/input.py` into `app/schemas/patient/input/__init__.py` + sibling files is **transparent to every existing import** — nothing outside the package needs to change, as long as the new `__init__.py` re-exports every name the old flat file exported.

This means the split is mechanically safe and low-risk, but only if you do the safety check in Step 0 first.

---

## Step 0 — Safety check (do this before writing anything)

Grep the whole `app/` tree for any import that reaches *past* the package root into the flat file directly:

```bash
grep -rn "from app.schemas.<resource>.input import\|from app.schemas.<resource>.response import" app/ --include="*.py" | grep -v "app/schemas/<resource>/"
```

(Adjust the path for whichever layer you're splitting — `app.repository.<resource>_repository`, `app.services.<resource>_service`, `app.routers.<resource>`, `app.models.<resource>.<resource>`.)

If every consumer imports via the package root (e.g. `from app.schemas.patient import X` or `from app.schemas.fhir import X`), the split is safe — those imports don't care whether the target is a module or a package. If something imports a deeply-nested path directly, note it; you'll need to either update that one caller or keep re-exporting from the same relative location inside the new package.

Also grep for the **exact export surface** you must preserve — read the resource's own `__init__.py` (e.g. `app/schemas/patient/__init__.py`) in full. Every name it imports from the file you're splitting must still be importable from the new package's `__init__.py` afterward.

---

## Step 1 — Decide the file breakdown

Standard shape, consistent across all four code layers and both schema files:

```
<resource>/
  core.py          # the main/parent entity's own logic — not a sub-resource
  <sub1>.py         # one file per 0..* child table, named exactly after the sub-resource
  <sub2>.py
  ...
  __init__.py       # re-exports every name the old flat file exported
```

Layer-specific extras seen in this repo:
- **Repository**: `_shared.py` for cross-cutting helpers (`_with_relationships`, `_apply_list_filters`) used by more than one sub-file; `full.py` for the atomic `create_full`/`patch_full` methods that touch every sub-resource at once.
- **Router**: `_responses.py` for the module-level `_SINGLE_200`/`_LIST_200`/`_SUBRES_*_200` `inline_schema()` constants shared across route files.
- **Schema input**: any nested grandchild model (e.g. `QualificationIdentifierCreate` nested inside `PractitionerQualificationCreate`) lives in the *same* file as its parent sub-resource, not its own file.
- **Schema response**: each sub-resource file also carries its `*ListResponse`/`FHIR*ListResponse`/`FHIR*ListItem` wrapper classes (see `/sub-resource-endpoints`) if the resource has sub-resource GET/DELETE routes. Organization has none of these (5-endpoint design, no sub-resource endpoints) — Patient and Practitioner do.

Assign every class/function in the old flat file to exactly one new file based on which sub-resource it belongs to. `core.py` gets only the parent-entity classes (`<Resource>CreateSchema`, `FHIR<Resource>Schema`, `PlainRepository` CRUD methods, etc.) plus imports from every sub-file it composes.

---

## Step 2 — Write the sub-files first, then `core.py` last

Write each sub-resource file with its own minimal imports (only what that file's classes/functions actually need — don't copy the old flat file's full import block into every new file). `core.py` is written last because it imports from all the others.

Preserve content **exactly** — same field names, same descriptions, same types, same validators. This is a mechanical split, not a rewrite. Don't "improve" anything while splitting; that's a separate task and makes the diff impossible to review.

---

## Step 3 — Write `__init__.py`

Re-export every name from the old file's export surface (Step 0), sourced from wherever it now actually lives:

```python
from .core import <Resource>CreateSchema, <Resource>PatchSchema
from .name import NameCreate, NamePatch
from .identifier import IdentifierCreate, IdentifierPatch
# ... one line per sub-file ...

__all__ = [
    "<Resource>CreateSchema",
    "<Resource>PatchSchema",
    "NameCreate",
    "NamePatch",
    # ... every exported name ...
]
```

---

## Step 4 — Delete the old flat file, clear `__pycache__`, verify

```bash
rm app/schemas/<resource>/input.py   # only after the package + __init__.py are both written
find app -type d -name "__pycache__" -exec rm -rf {} +
```

Then verify field-for-field parity — import every name the old file exported and diff the schema:

```bash
uv run python -c "
from app.schemas.<resource>.input import (
    <every name from the old __init__.py's import list>,
)
print('IMPORT OK')
print(sorted(<Resource>CreateSchema.model_json_schema()['properties'].keys()))
"
```

Compare that field list against what you'd get from the pre-split file (or just eyeball it against the fields you copied in Step 2 — nothing should be missing or renamed).

Finally, confirm the whole app still boots:

```bash
uv run python -c "import app.main; print('FULL APP IMPORT OK')"
```

For a router or schema-response split, also hit `/openapi.json` and confirm the paths/schemas count didn't drop:

```bash
uv run python -c "
from fastapi.testclient import TestClient
from app.main import app
r = TestClient(app).get('/openapi.json')
print(r.status_code, len(r.json()['paths']), len(r.json()['components']['schemas']))
"
```

---

## Checklist

- [ ] Step 0 safety-check grep run — no direct imports bypass the package root (or the one that does has been updated)
- [ ] Old file's full `__init__.py` export list captured before splitting
- [ ] Every sub-resource gets its own file, named exactly after the sub-resource
- [ ] Nested grandchild models stay in their parent sub-resource's file
- [ ] `core.py` written last, imports from every sub-file it composes
- [ ] `__init__.py` re-exports the complete original surface via `__all__`
- [ ] Old flat file deleted only after the package is complete
- [ ] `__pycache__` cleared before verification (stale `.pyc` can mask import errors)
- [ ] Targeted import + `model_json_schema()` field-parity check passed
- [ ] `import app.main` full-app boot check passed
- [ ] For router/response splits: `/openapi.json` paths + schemas count unchanged

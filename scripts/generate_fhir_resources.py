"""Generate fully-typed FHIR R4 resource models and every resource's request/response schemas.

    uv run python scripts/generate_fhir_resources.py

Writes:
  app/schemas/fhir_resources/<resource>.py   the whole R4 resource as Pydantic models: every element
      HL7 defines (down through every nested backbone element), HL7's own descriptions, required
      elements per HL7's schema, and for each element the search parameters that read it.
  app/schemas/<resource>/input/core.py       <R>CreateSchema / <R>PatchSchema (thin subclasses)
  app/schemas/<resource>/response/core.py    FHIR<R>Schema / FHIR<R>BundleEntry / FHIR<R>Bundle

Source of truth: app/fhir/spec/fhir.schema.json (see generate_fhir_datatypes.py for the datatype
models these build on). Per-resource request examples are carried over from the existing schema
classes, so regenerating never loses them; every resource needs one, because the response examples
are derived from it (app/schemas/common/examples.py).
"""

from __future__ import annotations

import importlib
import pprint
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate_fhir_datatypes as g

ROOT = g.ROOT
SCHEMAS = ROOT / "app" / "schemas"
OUT = SCHEMAS / "fhir_resources"

# Elements every DomainResource carries; modelled once on the base class.
BASE_ELEMENTS = {
    "resourceType",
    "id",
    "meta",
    "implicitRules",
    "language",
    "text",
    "contained",
    "extension",
    "modifierExtension",
}


def resources() -> dict[str, str]:
    """folder name -> FHIR resource name, for every resource package under app/schemas."""
    by_module = {
        g.module_name(d): d
        for d, v in g.DEFS.items()
        if "resourceType" in v.get("properties", {})
    }
    folders = sorted(
        p.name
        for p in SCHEMAS.iterdir()
        if p.is_dir() and (p / "input").is_dir() and p.name in by_module
    )
    return {f: by_module[f] for f in folders}


def search_hints(folder: str, resource: str) -> dict[str, str]:
    """element -> 'Search parameters: `a`, `b`.' from the resource's own SearchRegistry."""
    module = importlib.import_module(f"app.repository.{folder}.search")
    registry = getattr(module, f"{folder}_search")()
    by_element: dict[str, list[str]] = {}
    for param in registry.params.values():
        if param.name in ("_id", "_lastUpdated"):
            continue
        for match in re.finditer(rf"\b{resource}\.([A-Za-z]+)", param.expression):
            names = by_element.setdefault(match.group(1), [])
            if param.name not in names:
                names.append(param.name)
    return {
        el: "Search parameters: " + ", ".join(f"`{n}`" for n in names) + "."
        for el, names in by_element.items()
    }


def base_module() -> str:
    props = g.DEFS["Patient"]["properties"]

    def desc(name: str) -> str:
        return g.lit(props[name]["description"].strip())

    return f'''"""DomainResource: the elements every FHIR resource carries (generated, do not edit by hand)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.fhir_datatypes import Code, Extension, Id, Meta, Narrative, Uri


class DomainResource(BaseModel):
    "A resource that carries narrative, extensions and contained resources."

    # `extra=ignore`: the validated raw body, not these models, is what gets stored, so an element
    # a model does not declare is never lost.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Id | None = Field(
        None,
        description={desc("id")} + " Server-managed: assigned from the resource's public id sequence; ignored if sent.",
    )
    meta: Meta | None = Field(
        None,
        description={desc("meta")} + " Server-managed: stamped on at read time; ignored if sent.",
    )
    implicitRules: Uri | None = Field(None, description={desc("implicitRules")})
    language: Code | None = Field(None, description={desc("language")})
    text: Narrative | None = Field(None, description={desc("text")})
    contained: list[dict] | None = Field(None, description={desc("contained")})
    extension: list[Extension] | None = Field(None, description={desc("extension")})
    modifierExtension: list[Extension] | None = Field(
        None, description={desc("modifierExtension")}
    )
'''


def resource_module(resource: str, folder: str) -> tuple[str, set[str]]:
    schema = g.DEFS[resource]
    g.HINTS[resource] = search_hints(folder, resource)
    used: set[str] = set()
    props = {
        n: p
        for n, p in schema["properties"].items()
        if not n.startswith("_") and n not in BASE_ELEMENTS
    }
    top_required = (
        set(schema.get("required", [])) | g.MIN_ONE.get(resource, set())
    ) & set(props)
    body = g.field_lines(
        {"properties": props, "required": sorted(top_required)},
        used,
        set(),
        resource,
    )
    rt = (
        f'    resourceType: Literal["{resource}"] | None = Field(\n'
        f"        None, description=\"Optional; if supplied it must be '{resource}'.\"\n    )"
    )
    parts = [
        f"class {resource}(DomainResource):\n    {g.lit(schema['description'].strip())}\n\n"
        + "\n".join([rt, *body])
    ]
    exports = {resource, resource + "Patch"}
    for nested in g.nested_of(resource):
        ns = g.DEFS[nested]
        base = (
            "BackboneElement" if "modifierExtension" in ns["properties"] else "Element"
        )
        parts.append(
            g.render_class(g.class_name(nested), base, ns["description"], ns, used)
        )
        exports.add(g.class_name(nested))

    # Merge-patch variant: every top-level element optional (a supplied element replaces the
    # stored one wholesale, so nested minimums stay).
    required = sorted(top_required)
    patch_body = []
    if required:
        patch_body = g.field_lines(
            {"properties": {r: props[r] for r in required}, "required": []},
            used,
            set(),
            resource,
            force_optional=True,
        )
    patch = (
        f"class {resource}Patch({resource}):\n"
        f'    "Merge-patch variant: every top-level element is optional; a supplied element replaces the stored value."\n\n'
        + ("\n".join(patch_body) if patch_body else "")
    )
    parts.append(patch)

    own = {n for n in exports} | {g.class_name(n) for n in g.nested_of(resource)}
    external = sorted(used - own)
    uses_literal = "Literal[" in "\n".join(parts)
    lines = [
        '"""Generated by scripts/generate_fhir_resources.py from the HL7 R4 JSON schema - do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if uses_literal:
        lines += ["from typing import Literal", ""]
    lines += ["from pydantic import Field", ""]
    dt = list(external)
    if dt:
        lines += [
            "from app.schemas.fhir_datatypes import " + ", ".join(dt),
        ]
    base_names = ["Element"] if any("(Element)" in p for p in parts) else []
    if any("(BackboneElement)" in p for p in parts):
        base_names.append("BackboneElement")
    if base_names:
        lines += [
            "from app.schemas.fhir_datatypes.base import "
            + ", ".join(sorted(base_names))
        ]
    lines += ["from app.schemas.fhir_resources.base import DomainResource", ""]
    # Backbone classes refer to ones defined further down; resolve them now so that subclasses in
    # other modules see fully-built models.
    rebuild = "\n".join(f"{n}.model_rebuild()" for n in sorted(exports))
    text = "\n".join(lines) + "\n\n" + "\n\n\n".join(parts) + "\n\n\n" + rebuild + "\n"
    return text, exports


def existing_examples(folder: str, resource: str) -> tuple[dict | None, dict | None]:
    """The request examples on the current Create/Patch schemas (so regeneration keeps them)."""
    module = importlib.import_module(f"app.schemas.{folder}.input")
    out = []
    for suffix in ("CreateSchema", "PatchSchema"):
        cls = getattr(module, resource + suffix, None)
        extra = (getattr(cls, "model_config", {}) or {}).get("json_schema_extra")
        example = extra.get("example") if isinstance(extra, dict) else None
        out.append(example)
    return out[0], out[1]


def literal(value) -> str:
    return pprint.pformat(value, width=88, sort_dicts=False)


# Appended to every create schema's description: why its example has no `reference` strings.
_EXAMPLE_REFERENCES = (
    " The example can be sent as it is: where it points at another record it gives only `type` "
    "and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked "
    "on write."
)


def input_module(folder: str, resource: str, create, patch) -> str:
    lines = [
        '"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see',
        "scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from pydantic import ConfigDict",
        "",
        f"from app.schemas.fhir_resources.{folder} import {resource}, {resource}Patch",
        "",
    ]
    if create is not None:
        lines += [f"_CREATE_EXAMPLE = {literal(create)}", ""]
    if patch is not None:
        lines += [f"_PATCH_EXAMPLE = {literal(patch)}", ""]
    common = (
        "The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 "
        "element is kept, including ones nothing searches on. `id` and `meta` are server-managed "
        "and ignored if sent. The organization and the audit fields come from the verified token, "
        "never the body."
    )
    lines += [
        "",
        f"class {resource}CreateSchema({resource}):",
        f"    {g.lit('POST body - a FHIR R4 ' + resource + ' resource. ' + common + _EXAMPLE_REFERENCES)}",
        "",
    ]
    lines += (
        [
            '    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})'
        ]
        if create is not None
        else []
    )
    lines += [
        "",
        "",
        f"class {resource}PatchSchema({resource}Patch):",
        f"    {g.lit('PATCH body - a partial FHIR R4 ' + resource + ' (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). ' + common)}",
        "",
    ]
    lines += (
        ['    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})']
        if patch is not None
        else []
    )
    return "\n".join(lines) + "\n"


def example_facts(folder: str) -> tuple[str, str]:
    """(router prefix, first public id) - what a response example needs besides the body."""
    # app.main must be imported before any router: it breaks the DI import cycle.
    importlib.import_module("app.main")
    router = importlib.import_module(f"app.routers.{folder}").router
    models = importlib.import_module(f"app.models.{folder}.core")
    sequence = getattr(models, f"{folder}_id_seq")
    return router.prefix, str(sequence.start)


def response_module(folder: str, resource: str, path: str, first_id: str) -> str:
    return f'''"""Response schemas for {resource} (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.{folder}.input.core import _CREATE_EXAMPLE
from app.schemas.common import FHIRBundle
from app.schemas.common.examples import bundle_example, served_example
from app.schemas.fhir_datatypes import Meta
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_resources.{folder} import {resource}

_EXAMPLE = served_example("{resource}", "{first_id}", _CREATE_EXAMPLE)


class FHIR{resource}Schema({resource}):
    "A FHIR R4 {resource} as served: the stored document with `id` and `meta` stamped on."

    model_config = ConfigDict(json_schema_extra={{"example": _EXAMPLE}})

    resourceType: str = Field("{resource}", description="Always '{resource}'.")
    id: str = Field(..., description="Public {folder}_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIR{resource}BundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIR{resource}Schema | dict = Field(
        ...,
        description="A {resource} (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIR{resource}Bundle(FHIRBundle):
    model_config = ConfigDict(
        json_schema_extra={{"example": bundle_example("{path}", _EXAMPLE)}}
    )

    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIR{resource}BundleEntry] | None = None
'''


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    g.REQUIRED_CODES.update(g._load_required_codes())
    g.MIN_ONE.update(g._load_min_one())
    targets = resources()
    # Read every example before anything is rewritten.
    examples = {f: existing_examples(f, r) for f, r in targets.items()}
    facts = {f: example_facts(f) for f in targets}
    if OUT.exists():
        shutil.rmtree(OUT)
    write(OUT / "base.py", base_module())
    exported: dict[str, set[str]] = {}
    for folder, resource in targets.items():
        text, exports = resource_module(resource, folder)
        write(OUT / f"{folder}.py", text)
        exported[folder] = exports
        create, patch = examples[folder]
        write(
            SCHEMAS / folder / "input" / "core.py",
            input_module(folder, resource, create, patch),
        )
        write(
            SCHEMAS / folder / "response" / "core.py",
            response_module(folder, resource, *facts[folder]),
        )
    init = [
        '"""Fully-typed FHIR R4 resource models (generated; see scripts/generate_fhir_resources.py)."""',
        "",
    ]
    for folder, names in exported.items():
        top = sorted(
            n for n in names if n == targets[folder] or n == targets[folder] + "Patch"
        )
        init.append(f"from app.schemas.fhir_resources.{folder} import {', '.join(top)}")
    init += ["", "__all__ = ["]
    for folder in exported:
        init += [f'    "{targets[folder]}",', f'    "{targets[folder]}Patch",']
    init += ["]", ""]
    write(OUT / "__init__.py", "\n".join(init))
    for args in (["check", "--fix", "--select", "I,RUF022,F401"], ["format"]):
        subprocess.run(
            [sys.executable, "-m", "ruff", *args, str(OUT)]
            + [
                str(SCHEMAS / f / d / "core.py")
                for f in targets
                for d in ("input", "response")
            ],
            check=False,
            capture_output=True,
        )
    print(f"wrote {len(targets)} resources to {OUT}")


if __name__ == "__main__":
    main()

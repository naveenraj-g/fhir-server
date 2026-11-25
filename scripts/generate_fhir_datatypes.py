"""Generate app/schemas/fhir_datatypes/ from HL7's published R4 JSON schema.

    uv run python scripts/generate_fhir_datatypes.py

Source of truth: app/fhir/spec/fhir.schema.json (the file the native validator uses). Each FHIR
datatype becomes one Pydantic model in genuine FHIR camelCase, with HL7's own element
descriptions, so the OpenAPI spec (and so the MCP tools) describes every nested element. Categories
follow https://hl7.org/fhir/R4/datatypes.html:

    primitive/   the 20 primitive types, as constrained aliases
    general/     general-purpose types (Address ... Timing, the quantity family)
    metadata/    metadata types (ContactDetail ... UsageContext)
    special/     special-purpose types (Dosage, ElementDefinition, Extension, Meta, Narrative, ...)
    base.py      Element and BackboneElement, which every other model extends

Python modules are snake_case; the FHIR-facing field names stay camelCase. A FHIR name that is a
Python keyword (`class`, `from`, ...) gets a trailing underscore and an alias back to the FHIR name.
Primitive-extension siblings (`_status`) are not modelled.
"""

from __future__ import annotations

import json
import keyword
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SCHEMA = ROOT / "app" / "fhir" / "spec" / "fhir.schema.json"
PROFILES = ROOT / "app" / "fhir" / "spec" / "profiles-resources.json"
OUT = ROOT / "app" / "schemas" / "fhir_datatypes"

DEFS = json.loads(SCHEMA.read_text(encoding="utf-8"))["definitions"]

PRIMITIVES = {
    "base64Binary": "Base64Binary",
    "boolean": "Boolean",
    "canonical": "Canonical",
    "code": "Code",
    "date": "Date",
    "dateTime": "DateTime",
    "decimal": "Decimal",
    "id": "Id",
    "instant": "Instant",
    "integer": "Integer",
    "markdown": "Markdown",
    "oid": "Oid",
    "positiveInt": "PositiveInt",
    "string": "String",
    "time": "Time",
    "unsignedInt": "UnsignedInt",
    "uri": "Uri",
    "url": "Url",
    "uuid": "Uuid",
    "xhtml": "Xhtml",
}

# HL7's grouping on https://hl7.org/fhir/R4/datatypes.html
CATEGORIES = {
    "general": [
        "Address",
        "Age",
        "Annotation",
        "Attachment",
        "CodeableConcept",
        "Coding",
        "ContactPoint",
        "Count",
        "Distance",
        "Duration",
        "HumanName",
        "Identifier",
        "Money",
        "MoneyQuantity",
        "Period",
        "Quantity",
        "Range",
        "Ratio",
        "Reference",
        "SampledData",
        "Signature",
        "SimpleQuantity",
        "Timing",
    ],
    "metadata": [
        "ContactDetail",
        "Contributor",
        "DataRequirement",
        "Expression",
        "ParameterDefinition",
        "RelatedArtifact",
        "TriggerDefinition",
        "UsageContext",
    ],
    "special": [
        "Dosage",
        "ElementDefinition",
        "Extension",
        "MarketingStatus",
        "Meta",
        "Narrative",
        "Population",
        "ProdCharacteristic",
        "ProductShelfLife",
        "SubstanceAmount",
    ],
}
# Extra text appended to a field's description, keyed class name -> element name (set by the
# resource generator to list the search parameters that read an element).
HINTS: dict[str, dict[str, str]] = {}

# Elements R4 makes 1..1 that HL7's JSON schema does not list as required.
EXTRA_REQUIRED = {"Extension": {"url"}, "Annotation": {"text"}}

# Extension.value[x] may be any datatype, which would pull the whole datatype graph into every
# model's JSON schema (and so every resource's OpenAPI). Its complex values are typed as objects
# naming the FHIR type; its primitive values stay fully typed.

# Quantity profiles / specialisations that carry exactly Quantity's elements.
QUANTITY_FAMILY = {"Age", "Count", "Distance", "Duration"}

# Not in the JSON schema (they are profiles of Quantity); descriptions are HL7's.
SIMPLE_QUANTITY = (
    "A fixed quantity (no comparator): a Quantity profile that is the same as Quantity except "
    "that `comparator` is not allowed."
)
MONEY_QUANTITY = (
    "An amount of money, as a Quantity profile (no comparator). The currency is carried in `code` "
    "with `system` http://unitsofmeasure.org and `unit`; use Money when you need a "
    "value/currency pair."
)
BACKBONE_DESCRIPTION = (
    "Base definition for all elements that contain other elements: an Element that can also carry "
    "`modifierExtension`, which cannot be ignored if unrecognized."
)
ELEMENT_DESCRIPTION = (
    "Base definition for all elements in a resource: a unique `id` within the resource and "
    "(safe-to-ignore) `extension`s."
)


def class_name(def_name: str) -> str:
    return def_name.replace("_", "")


def module_name(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def lit(text: str) -> str:
    """A Python string literal for arbitrary text."""
    return json.dumps(text, ensure_ascii=False)


def annotation(prop: dict, used: set[str], flatten: bool = False) -> str:
    """The Python annotation for one schema property (names recorded in `used`)."""
    if "items" in prop:
        return f"list[{annotation(prop['items'], used, flatten)}]"
    if "$ref" in prop:
        ref = prop["$ref"].rsplit("/", 1)[-1]
        if ref in PRIMITIVES:
            used.add(PRIMITIVES[ref])
            return PRIMITIVES[ref]
        if ref == "ResourceList" or flatten:
            return "dict"
        name = class_name(ref)
        used.add(name)
        return name
    if "enum" in prop:
        return "Literal[" + ", ".join(lit(v) for v in prop["enum"]) + "]"
    if "const" in prop:
        return f"Literal[{lit(prop['const'])}]"
    return {"string": "str", "boolean": "bool", "number": "float"}.get(
        prop.get("type"), "object"
    )


def choice_groups(props: dict[str, dict]) -> dict[str, str]:
    """Property name -> choice prefix, for `value[x]`-style properties: a prefix followed by a type
    name, shared by at least two properties that carry the identical HL7 description (every member
    of a choice element has the one definition; `reasonCode` / `reasonReference` do not)."""
    type_names = {t[0].upper() + t[1:] for t in PRIMITIVES} | {
        class_name(k) for k in DEFS if k[0].isupper() and "_" not in k
    }
    by_key: dict[tuple[str, str], list[str]] = {}
    for name, prop in props.items():
        matches = [
            t
            for t in type_names
            if name.endswith(t) and len(name) > len(t) and name[0].islower()
        ]
        if not matches:
            continue
        longest = max(matches, key=len)
        prefix = name[: -len(longest)]
        # A choice element is never repeating, which rules out reasonCode / reasonReference.
        if prefix.isalpha() and prop.get("description") and "items" not in prop:
            by_key.setdefault((prefix, prop["description"]), []).append(name)
    return {n: prefix for (prefix, _d), ns in by_key.items() if len(ns) > 1 for n in ns}


def inline_primitive(name: str, prop: dict) -> dict:
    """HL7's schema inlines a primitive's type and pattern on some properties (Extension.valueInteger)
    instead of using a $ref; recover the FHIR primitive from the pattern plus the name suffix."""
    if "$ref" in prop or "items" in prop or "enum" in prop or "type" not in prop:
        return prop
    best = None
    for fhir in PRIMITIVES:
        suffix = fhir[0].upper() + fhir[1:]
        target = DEFS[fhir]
        if (
            name.endswith(suffix)
            and len(name) > len(suffix)
            and target.get("pattern") == prop.get("pattern")
            and target.get("type", "string") == prop["type"]
            and (best is None or len(fhir) > len(best))
        ):
            best = fhir
    if best is None:
        return prop
    return {"$ref": f"#/definitions/{best}", "description": prop.get("description", "")}


def _load_min_one() -> dict[str, set[str]]:
    """class name -> elements R4 makes 1..1 (min cardinality 1), primitives included.

    HL7's JSON schema only lists non-primitive elements as `required` (a primitive may arrive as a
    `_name` extension sibling), so the real minimums come from the resource profiles
    (profiles-resources.json) and, for datatypes, google-fhir-r4's validation annotations. A choice
    element (`value[x]`) cannot be a single required field and is skipped."""
    out: dict[str, set[str]] = {}
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    for entry in profiles["entry"]:
        sd = entry["resource"]
        if sd.get("resourceType") != "StructureDefinition":
            continue
        for el in sd["snapshot"]["element"]:
            parts = el["id"].split(".")
            if len(parts) < 2 or el.get("min", 0) < 1 or parts[-1].endswith("[x]"):
                continue
            owner = parts[0]
            if len(parts) > 2:
                owner += "_" + parts[-2][0].upper() + parts[-2][1:]
            if parts[-1] in DEFS.get(owner, {}).get("properties", {}):
                out.setdefault(class_name(owner), set()).add(parts[-1])

    from google.fhir.core.proto import annotations_pb2 as ann
    from google.fhir.r4.proto.core import datatypes_pb2

    def walk(desc, name):
        for f in desc.fields:
            options = f.GetOptions()
            if not (
                options.HasExtension(ann.validation_requirement)
                and options.Extensions[ann.validation_requirement]
                == ann.REQUIRED_BY_FHIR
            ):
                continue
            if f.message_type is not None and "choice" in f.message_type.oneofs_by_name:
                continue
            out.setdefault(class_name(name), set()).add(f.json_name)
        for nested in desc.nested_types:
            walk(nested, f"{name}_{nested.name}")

    for names in CATEGORIES.values():
        for name in names:
            message = getattr(datatypes_pb2, name, None)
            if message is not None and hasattr(message, "DESCRIPTOR"):
                walk(message.DESCRIPTOR, name)
    return out


MIN_ONE: dict[str, set[str]] = {}


def _code_lists() -> dict[str, list[str]]:
    """value-set name -> its codes, from google-fhir-r4's generated code enums (the codes HL7 defines
    for a value set with a required binding)."""
    from google.fhir.core.proto import annotations_pb2 as ann
    from google.fhir.r4.proto.core import codes_pb2

    out: dict[str, list[str]] = {}
    for attr in dir(codes_pb2):
        cls = getattr(codes_pb2, attr)
        if not attr.endswith("Code") or not hasattr(cls, "Value"):
            continue
        values = []
        for v in cls.Value.DESCRIPTOR.values:
            if v.name == "INVALID_UNINITIALIZED":
                continue
            opts = v.GetOptions()
            values.append(
                opts.Extensions[ann.fhir_original_code]
                if opts.HasExtension(ann.fhir_original_code)
                else v.name.lower().replace("_", "-")
            )
        out[attr[: -len("Code")].lower()] = values
    return out


def _load_required_codes() -> dict[tuple[str, str], list[str]]:
    """(class name, element) -> allowed codes, for `code` elements with a *required* binding that
    HL7's JSON schema leaves as a plain string (a large value set, e.g. the request statuses)."""
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    code_lists = _code_lists()
    # value sets google-fhir has no enum for, resolved from the project's own constants
    from app.models.shared.resource_types import ANY_RESOURCE_TYPES

    code_lists["resourcetypes"] = list(ANY_RESOURCE_TYPES)
    # ... and from the enums the project already holds for those value sets (audited against HL7
    # when each resource was rebuilt: they store the true FHIR codes).
    import importlib

    code_lists.update(LISTED_VALUE_SETS)
    for value_set, (module, cls) in MODEL_ENUM_VALUE_SETS.items():
        enum = getattr(importlib.import_module(module), cls)
        code_lists[value_set.replace("-", "").lower()] = [m.value for m in enum]
    out: dict[tuple[str, str], list[str]] = {}
    for entry in profiles["entry"]:
        sd = entry["resource"]
        if sd.get("resourceType") != "StructureDefinition":
            continue
        for el in sd["snapshot"]["element"]:
            binding = el.get("binding") or {}
            if binding.get("strength") != "required":
                continue
            if [t["code"] for t in el.get("type", [])] != ["code"]:
                continue
            parts = el["id"].split(".")
            # HL7 names a backbone type after the root and its own last segment only:
            # CarePlan.activity.detail -> CarePlan_Detail.
            owner = parts[0]
            if len(parts) > 2:
                owner += "_" + parts[-2][0].upper() + parts[-2][1:]
            prop = DEFS.get(owner, {}).get("properties", {}).get(parts[-1])
            if prop is None or "enum" in (prop.get("items") or prop):
                continue
            vs = binding.get("valueSet", "").rsplit("/", 1)[-1].split("|")[0]
            key = vs.replace("-", "").lower()
            codes = code_lists.get(key) or code_lists.get(key.rstrip("s"))
            if codes:
                out[(class_name(owner), parts[-1])] = codes
            else:
                UNRESOLVED.append((class_name(owner), parts[-1], vs))
    return out


MODEL_ENUM_VALUE_SETS = {
    "care-plan-intent": ("app.models.care_plan.enums", "CarePlanIntent"),
    "clinicalimpression-status": (
        "app.models.clinical_impression.enums",
        "ClinicalImpressionStatus",
    ),
    "immunization-status": ("app.models.immunization.enums", "ImmunizationStatus"),
    "immunization-evaluation-status": (
        "app.models.immunization_evaluation.enums",
        "ImmunizationEvaluationStatus",
    ),
    "medication-admin-status": (
        "app.models.medication_administration.enums",
        "MedicationAdministrationStatus",
    ),
    "medication-statement-status": (
        "app.models.medication_statement.enums",
        "MedicationStatementStatus",
    ),
}

# Value sets neither google-fhir nor a model enum covers, listed from HL7 (as audited when CarePlan
# was rebuilt): care-plan-activity-kind.
LISTED_VALUE_SETS = {
    "careplanactivitykind": [
        "Appointment",
        "CommunicationRequest",
        "DeviceRequest",
        "MedicationRequest",
        "NutritionOrder",
        "Task",
        "ServiceRequest",
        "VisionPrescription",
    ],
}

UNRESOLVED: list[tuple[str, str, str]] = []
REQUIRED_CODES: dict[tuple[str, str], list[str]] = {}


def field_lines(
    schema: dict,
    used: set[str],
    skip: set[str],
    owner: str = "",
    force_optional: bool = False,
) -> list[str]:
    props = {
        name: prop
        for name, prop in schema.get("properties", {}).items()
        if not name.startswith("_") and name not in skip
    }
    required = set(schema.get("required", []))
    required |= EXTRA_REQUIRED.get(owner, set()) | MIN_ONE.get(owner, set())
    if force_optional:
        required = set()
    choices = choice_groups(props)
    lines = []
    for name, prop in props.items():
        py_name, extra = name, ""
        if keyword.iskeyword(name) or hasattr(BaseModel, name):
            py_name, extra = name + "_", f", alias={lit(name)}"
        description = prop.get("description", "").strip()
        if name in choices:
            description += (
                f" Choice: at most one `{choices[name]}[x]` element may be present."
            )
        hint_map = HINTS.get(owner, {})
        hint_key = name if name in hint_map else choices.get(name)
        if hint_key in hint_map:
            description += " " + hint_map[hint_key]
        prop = inline_primitive(name, prop)
        flatten = owner == "Extension"
        codes = REQUIRED_CODES.get((owner, name))
        if codes:
            literal = "Literal[" + ", ".join(lit(c) for c in codes) + "]"
            ann = f"list[{literal}]" if "items" in prop else literal
        else:
            ann = annotation(prop, used, flatten)
        if flatten and ann == "dict":
            ref = prop["$ref"].rsplit("/", 1)[-1]
            description += f" (A FHIR {ref} object.)"
        if name in required:
            lines.append(
                f"    {py_name}: {ann} = Field(..., description={lit(description)}{extra})"
            )
        else:
            lines.append(
                f"    {py_name}: {ann} | None = Field(None, description={lit(description)}{extra})"
            )
    return lines


def render_class(
    name: str, base: str, description: str, schema: dict, used: set[str], skip=None
) -> str:
    skip = {"id", "extension", "modifierExtension"} | (skip or set())
    body = field_lines(schema, used, skip, name)
    doc = lit(description.strip())
    out = [f"class {name}({base}):", f"    {doc}", ""]
    out += body
    return "\n".join(out)


def header(
    imports: list[str],
    used: set[str],
    own: set[str],
    uses_literal: bool,
    uses_field: bool,
) -> str:
    """Module header: the future import, typing imports, and every cross-module name behind
    TYPE_CHECKING (pydantic resolves them in the package __init__)."""
    external = sorted(used - own)
    typing_names = (["TYPE_CHECKING"] if external else []) + (
        ["Literal"] if uses_literal else []
    )
    lines = [
        '"""Generated by scripts/generate_fhir_datatypes.py from the HL7 R4 JSON schema - do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if typing_names:
        lines += ["from typing import " + ", ".join(typing_names), ""]
    if uses_field:
        lines += ["from pydantic import Field", ""]
    lines += imports
    if external:
        lines += [
            "",
            "if TYPE_CHECKING:",
            "    from app.schemas.fhir_datatypes import " + ", ".join(external),
        ]
    lines.append("")
    return "\n".join(lines)


def nested_of(def_name: str) -> list[str]:
    return [k for k in DEFS if k.startswith(def_name + "_")]


def generate_type(def_name: str) -> tuple[str, set[str], set[str]]:
    """(source, exported class names, referenced names) for one top-level datatype module."""
    used: set[str] = set()
    exports: set[str] = set()
    parts = []
    imports = []

    if def_name in ("SimpleQuantity", "MoneyQuantity"):
        quantity = {
            "properties": {
                k: v
                for k, v in DEFS["Quantity"]["properties"].items()
                if k != "comparator"
            }
        }
        desc = SIMPLE_QUANTITY if def_name == "SimpleQuantity" else MONEY_QUANTITY
        imports.append("from app.schemas.fhir_datatypes.base import Element")
        parts.append(render_class(def_name, "Element", desc, quantity, used))
        exports.add(def_name)
    elif def_name in QUANTITY_FAMILY:
        imports.append(
            "from app.schemas.fhir_datatypes.general.quantity import Quantity"
        )
        parts.append(
            f"class {def_name}(Quantity):\n    {lit(DEFS[def_name]['description'].strip())}\n"
        )
        exports.add(def_name)
    else:
        for d in [def_name, *nested_of(def_name)]:
            schema = DEFS[d]
            base = (
                "BackboneElement"
                if "modifierExtension" in schema["properties"]
                else "Element"
            )
            imports_needed = f"from app.schemas.fhir_datatypes.base import {base}"
            if imports_needed not in imports:
                imports.append(imports_needed)
            parts.append(
                render_class(class_name(d), base, schema["description"], schema, used)
            )
            exports.add(class_name(d))
    return "\n\n\n".join(parts), exports, used


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def primitives_module() -> str:
    lines = [
        '"""Generated by scripts/generate_fhir_datatypes.py from HL7\'s R4 JSON schema - do not edit by hand.',
        "",
        "The 20 FHIR primitive types as constrained aliases. The patterns are HL7's own. A primitive",
        "carries no `id`/`extension` here (the `_element` siblings are not modelled).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Annotated",
        "",
        "from pydantic import Field, StringConstraints",
        "",
    ]
    for fhir, alias in PRIMITIVES.items():
        schema = DEFS[fhir]
        desc = schema.get("description", "").strip()
        kind = schema.get("type")
        pattern = schema.get("pattern")
        if kind == "boolean":
            expr = f"Annotated[bool, Field(description={lit(desc)})]"
        elif fhir == "integer":
            expr = f"Annotated[int, Field(description={lit(desc)})]"
        elif fhir == "positiveInt":
            expr = f"Annotated[int, Field(ge=1, description={lit(desc)})]"
        elif fhir == "unsignedInt":
            expr = f"Annotated[int, Field(ge=0, description={lit(desc)})]"
        elif fhir == "decimal":
            expr = f"Annotated[float, Field(description={lit(desc)})]"
        elif pattern and fhir not in ("string", "markdown"):
            expr = (
                f"Annotated[str, StringConstraints(pattern={lit(pattern)}), "
                f"Field(description={lit(desc)})]"
            )
        else:
            expr = f"Annotated[str, Field(description={lit(desc)})]"
        lines.append(f"{alias} = {expr}")
        lines.append("")
    return "\n".join(lines)


def base_module() -> str:
    return "\n".join(
        [
            '"""Element and BackboneElement: the bases of every FHIR datatype model (hand-kept)."""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import TYPE_CHECKING",
            "",
            "from pydantic import BaseModel, ConfigDict, Field",
            "",
            "if TYPE_CHECKING:",
            "    from app.schemas.fhir_datatypes import Extension, String",
            "",
            "",
            "class Element(BaseModel):",
            f"    {lit(ELEMENT_DESCRIPTION)}",
            "",
            "    # `extra=ignore`: the validated raw body, not these models, is what gets stored, so an element",
            "    # a model does not declare is never lost.",
            '    model_config = ConfigDict(extra="ignore", populate_by_name=True)',
            "",
            "    id: String | None = Field(",
            "        None,",
            f"        description={lit(DEFS['Element']['properties']['id']['description'])},",
            "    )",
            "    extension: list[Extension] | None = Field(",
            "        None,",
            f"        description={lit(DEFS['Element']['properties']['extension']['description'])},",
            "    )",
            "",
            "",
            "class BackboneElement(Element):",
            f"    {lit(BACKBONE_DESCRIPTION)}",
            "",
            "    modifierExtension: list[Extension] | None = Field(",
            "        None,",
            f"        description={lit(DEFS['Timing']['properties']['modifierExtension']['description'])},",
            "    )",
            "",
        ]
    )


def main() -> None:
    REQUIRED_CODES.update(_load_required_codes())
    MIN_ONE.update(_load_min_one())
    if OUT.exists():
        shutil.rmtree(OUT)
    write(OUT / "base.py", base_module())
    write(OUT / "primitive" / "__init__.py", "")
    write(OUT / "primitive" / "primitives.py", primitives_module())

    exported: list[tuple[str, str]] = []  # (module path, class)
    for category, names in CATEGORIES.items():
        write(OUT / category / "__init__.py", "")
        for def_name in names:
            source, exports, used = generate_type(def_name)
            imports = sorted(
                {
                    line
                    for line in source.splitlines()
                    if False  # placeholder - imports are computed below
                }
            )
            base_imports = []
            if def_name in ("SimpleQuantity", "MoneyQuantity"):
                base_imports.append(
                    "from app.schemas.fhir_datatypes.base import Element"
                )
            elif def_name in QUANTITY_FAMILY:
                base_imports.append(
                    "from app.schemas.fhir_datatypes.general.quantity import Quantity"
                )
            else:
                bases = set()
                for d in [def_name, *nested_of(def_name)]:
                    bases.add(
                        "BackboneElement"
                        if "modifierExtension" in DEFS[d]["properties"]
                        else "Element"
                    )
                base_imports.append(
                    "from app.schemas.fhir_datatypes.base import "
                    + ", ".join(sorted(bases))
                )
            del imports
            uses_literal = "Literal[" in source
            text = (
                header(base_imports, used, exports, uses_literal, "Field(" in source)
                + "\n\n"
                + source
                + "\n"
            )
            write(OUT / category / f"{module_name(def_name)}.py", text)
            for cls in sorted(exports):
                exported.append((f"{category}.{module_name(def_name)}", cls))

    init = [
        '"""FHIR R4 datatypes as Pydantic models, generated from HL7\'s own schema.',
        "",
        "Public (request/response) field names are FHIR camelCase; Python modules are snake_case.",
        "Regenerate with `uv run python scripts/generate_fhir_datatypes.py`. Categories follow",
        "https://hl7.org/fhir/R4/datatypes.html (primitive / general / metadata / special).",
        '"""',
        "",
        "from pydantic import BaseModel",
        "",
        "from app.schemas.fhir_datatypes.base import BackboneElement, Element",
        "from app.schemas.fhir_datatypes.primitive.primitives import (",
    ]
    init += [f"    {alias}," for alias in PRIMITIVES.values()]
    init.append(")")
    for module, cls in sorted(exported, key=lambda x: (x[0], x[1])):
        pass
    by_module: dict[str, list[str]] = {}
    for module, cls in exported:
        by_module.setdefault(module, []).append(cls)
    for module in sorted(by_module):
        init.append(f"from app.schemas.fhir_datatypes.{module} import (")
        init += [f"    {cls}," for cls in sorted(by_module[module])]
        init.append(")")
    all_names = sorted(
        ["Element", "BackboneElement", *PRIMITIVES.values(), *(c for _m, c in exported)]
    )
    init += ["", "__all__ = ["] + [f"    {lit(n)}," for n in all_names] + ["]", ""]
    init += [
        "# Models reference one another (Identifier -> Reference -> Identifier, Extension -> everything),",
        "# so every annotation is a string until all modules are loaded; resolve them here.",
        "_NAMESPACE = {name: globals()[name] for name in __all__}",
        "for _name in __all__:",
        "    _obj = globals()[_name]",
        "    if isinstance(_obj, type) and issubclass(_obj, BaseModel):",
        "        _obj.model_rebuild(_types_namespace=_NAMESPACE)",
        "",
    ]
    write(OUT / "__init__.py", "\n".join(init))
    # Keep the output lint-clean: sorted imports, then the formatter.
    for args in (["check", "--fix", "--select", "I,RUF022"], ["format"]):
        subprocess.run(
            [sys.executable, "-m", "ruff", *args, str(OUT)],
            check=False,
            capture_output=True,
        )
    print(f"wrote {len(exported)} models + {len(PRIMITIVES)} primitives to {OUT}")


if __name__ == "__main__":
    main()

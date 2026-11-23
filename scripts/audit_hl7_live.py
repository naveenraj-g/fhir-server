"""Audit every rebuilt resource against LIVE HL7 FHIR R4 data (https://hl7.org/fhir/R4/).

    uv run python scripts/audit_hl7_live.py            # use the cached download (offline after the first run)
    uv run python scripts/audit_hl7_live.py --refresh  # download again from hl7.org

Downloads four JSON files (~47 MB, cached in .cache/hl7-r4/, git-ignored): search-parameters,
profiles-resources, profiles-types, valuesets. For each resource in SEARCH_REGISTRIES it checks:

  1. the served search parameters equal the R4 list (extension-based parameters excluded);
  2. every parameter's type equals R4's, and its reference targets are a subset of R4's;
  3. every token parameter reading a `code` element with a *required* binding is an enum column
     (listed in tests/unit/test_hl7_alignment.py::REQUIRED_CODE_STORAGE), and that enum's members
     equal the live value set;
  4. every enum column in a rebuilt table is backed by such a parameter (no enum for an
     extensible/preferred/example code).

Exit code 1 when anything is wrong. Differences that are deliberate (a `patient` parameter narrowed
to Patient where R4 also lists Group; EpisodeOfCare, which is not rebuilt yet) are printed as notes.
"""

import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

CACHE = os.path.join(ROOT, ".cache", "hl7-r4")
BASE = "https://hl7.org/fhir/R4/"
FILES = (
    "search-parameters.json",
    "profiles-resources.json",
    "profiles-types.json",
    "valuesets.json",
)


def _load(refresh: bool) -> dict[str, dict]:
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for name in FILES:
        path = os.path.join(CACHE, name)
        if refresh or not os.path.exists(path):
            print(f"downloading {BASE}{name} ...", flush=True)
            with urllib.request.urlopen(BASE + name, timeout=300) as resp:
                data = resp.read()
            with open(path, "wb") as fh:
                fh.write(data)
        with open(path, encoding="utf8") as fh:
            out[name] = json.load(fh)
    return out


def main() -> int:
    data = _load("--refresh" in sys.argv)

    import sqlalchemy as sa

    import app.main  # noqa: F401 - imports every model and registry
    from app.core.database import FHIRBase
    from app.fhir.capability import SEARCH_REGISTRIES
    from tests.unit.test_hl7_alignment import REQUIRED_CODE_STORAGE

    structure = {}
    for key in ("profiles-resources.json", "profiles-types.json"):
        for e in data[key]["entry"]:
            r = e["resource"]
            if r["resourceType"] == "StructureDefinition":
                structure[r["name"]] = {el["id"]: el for el in r["snapshot"]["element"]}

    live: dict[str, dict] = {}
    for e in data["search-parameters.json"]["entry"]:
        sp = e["resource"]
        if sp["resourceType"] == "SearchParameter":
            for base in sp["base"]:
                live.setdefault(base, {})[sp["code"]] = sp

    code_systems, value_sets = {}, {}
    for e in data["valuesets.json"]["entry"]:
        r = e["resource"]
        if r["resourceType"] == "CodeSystem":
            code_systems[r["url"]] = r
        elif r["resourceType"] == "ValueSet":
            value_sets[r["url"]] = r

    def lookup(resource: str, element_id: str):
        els = structure[resource]
        el = els.get(element_id) or els.get(element_id + "[x]")
        if el:
            return el
        parts = element_id.split(".")
        for cut in range(len(parts) - 1, 0, -1):
            parent = els.get(".".join(parts[:cut]))
            if parent and len(parent.get("type", [])) == 1:
                dt = parent["type"][0]["code"]
                if (
                    dt in structure
                    and dt[0].isupper()
                    and dt not in ("BackboneElement", "Element")
                ):
                    return structure[dt].get(dt + "." + ".".join(parts[cut:]))
        return None

    def element_ids(expression: str, resource: str) -> list[str]:
        ids = []
        for alt in re.split(r"\s*\|\s*", expression):
            alt = re.sub(r"\s+as\s+.*$", "", alt.strip().strip("()"))
            alt = re.split(
                r"\.(?:where|as|ofType|exists|first|resolve|extension)\b", alt
            )[0]
            alt = alt.replace("(", "").replace(")", "")
            if alt.startswith(resource + "."):
                ids.append(alt)
        return ids

    def value_set_codes(url: str):
        vs = value_sets.get(url.split("|")[0])
        if not vs:
            return None
        out: set[str] = set()

        def walk(concepts):
            for c in concepts:
                out.add(c["code"])
                walk(c.get("concept", []))

        for inc in vs.get("compose", {}).get("include", []):
            if inc.get("concept"):
                out |= {c["code"] for c in inc["concept"]}
            elif inc.get("system") in code_systems:
                walk(code_systems[inc["system"]].get("concept", []))
        return out

    problems: list[str] = []
    notes: list[str] = []
    registries = {f().resource_type: f() for f in SEARCH_REGISTRIES.values()}

    for rt, reg in sorted(registries.items()):
        theirs = {
            c: s
            for c, s in live.get(rt, {}).items()
            if not c.startswith("_")
            and s.get("expression")
            and "xtension(" not in s["expression"]
        }
        ours = {n: p for n, p in reg.params.items() if not n.startswith("_")}
        if set(theirs) - set(ours):
            problems.append(
                f"{rt}: missing search parameters {sorted(set(theirs) - set(ours))}"
            )
        if set(ours) - set(theirs):
            problems.append(
                f"{rt}: parameters R4 does not define {sorted(set(ours) - set(theirs))}"
            )
        for code, sp in theirs.items():
            p = ours.get(code)
            if p is None:
                continue
            if p.type != sp["type"]:
                problems.append(f"{rt}.{code}: type {p.type}, R4 says {sp['type']}")
            if sp["type"] == "reference" and "Resource" not in (sp.get("target") or []):
                r4, mine = set(sp.get("target") or []), set(p.targets or ())
                if mine - r4:
                    problems.append(
                        f"{rt}.{code}: targets not allowed by R4: {sorted(mine - r4)}"
                    )
                if r4 - mine:
                    notes.append(f"{rt}.{code}: R4 also allows {sorted(r4 - mine)}")
            if sp["type"] != "token":
                continue
            for eid in element_ids(sp["expression"], rt):
                el = lookup(rt, eid)
                if not el or not any(t["code"] == "code" for t in el.get("type", [])):
                    continue
                if el.get("binding", {}).get("strength") != "required":
                    continue
                codes = value_set_codes(el["binding"]["valueSet"])
                if not codes:
                    # a required binding to an open-ended value set (e.g. every BCP 13 mime type)
                    # is not a closed list: it stays a string
                    notes.append(
                        f"{rt}.{code}: required binding to the open-ended value set "
                        f"{el['binding']['valueSet'].split('|')[0].rsplit('/', 1)[-1]} (a string, not an enum)"
                    )
                    break
                stored = REQUIRED_CODE_STORAGE.get((rt, code))
                if stored is None:
                    problems.append(
                        f"{rt}.{code}: required-binding code, no enum registered"
                    )
                    break
                table, column = stored
                ct = FHIRBase.metadata.tables[table].c[column].type
                item = ct.item_type if isinstance(ct, sa.ARRAY) else ct
                if not isinstance(item, sa.Enum):
                    problems.append(
                        f"{rt}.{code}: {table}.{column} is {ct!r}, not an enum"
                    )
                    break
                codes = value_set_codes(el["binding"]["valueSet"])
                if codes is None:
                    notes.append(
                        f"{rt}.{code}: value set {el['binding']['valueSet']} not in the bundle"
                    )
                elif set(item.enums) != codes:
                    problems.append(
                        f"{rt}.{code}: enum differs from the value set (ours only {sorted(set(item.enums) - codes)}, "
                        f"R4 only {sorted(codes - set(item.enums))})"
                    )
                break

    # enum columns in rebuilt tables must all be backed by a required-binding parameter
    declared = set(REQUIRED_CODE_STORAGE.values())
    rebuilt_tables = set()
    for f in SEARCH_REGISTRIES.values():
        pass
    from app.core.reference_resolver import RESOURCE_REGISTRY
    from app.repository._reference_check import checkable_types

    packages = {
        RESOURCE_REGISTRY[r][0].__module__.rsplit(".", 1)[0] for r in checkable_types()
    }
    for m in FHIRBase.registry.mappers:
        if m.class_.__module__.rsplit(".", 1)[0] in packages:
            rebuilt_tables.add(m.local_table.name)
    for table in sorted(rebuilt_tables):
        for col in FHIRBase.metadata.tables[table].columns:
            ct = col.type
            item = ct.item_type if isinstance(ct, sa.ARRAY) else ct
            if isinstance(item, sa.Enum) and (table, col.name) not in declared:
                problems.append(
                    f"{table}.{col.name} is an enum but no required-binding search parameter reads it"
                )

    print(
        f"resources audited: {len(registries)}  |  live R4 resource types with parameters: {len(live)}"
    )
    if notes:
        print("\nnotes (not failures):")
        for n in notes:
            print(" -", n[:200])
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(" -", p)
        return 1
    print(
        "\nOK: search parameters, types, targets, required-code enums and their values all match live R4."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

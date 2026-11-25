"""The emitted OpenAPI spec is what MCP callers and integrators read, so it must describe every
FHIR R4 element of every resource exactly as HL7 does, and document every route properly."""

import json
from pathlib import Path

import pytest

from app.main import app

HL7 = json.loads(
    (Path(__file__).parents[2] / "app/fhir/spec/fhir.schema.json").read_text(
        encoding="utf-8"
    )
)["definitions"]
VERBS = ("get", "post", "put", "patch", "delete")


@pytest.fixture(scope="module")
def spec() -> dict:
    return app.openapi()  # tests/conftest.py has already mounted the routers


def _ref(node: dict) -> str | None:
    return node["$ref"].rsplit("/", 1)[-1] if "$ref" in node else None


def _unwrap(node: dict) -> dict:
    """Follow Optional[...] (anyOf with null) down to the one real schema."""
    while True:
        for key in ("anyOf", "allOf", "oneOf"):
            real = [s for s in node.get(key, []) if s.get("type") != "null"]
            if len(real) == 1:
                node = real[0]
                break
        else:
            return node


def _is_array(node: dict) -> bool:
    return _unwrap(node).get("type") == "array"


def _resolve(node: dict, comps: dict) -> dict:
    node = _unwrap(node)
    if node.get("type") == "array":
        node = _unwrap(node["items"])
    while "$ref" in node:
        node = _unwrap(comps[_ref(node)])
    return node


def _name(node: dict) -> str | None:
    node = _unwrap(node)
    if node.get("type") == "array":
        node = _unwrap(node["items"])
    return _ref(node)


def _hl7(node: dict) -> dict:
    if node.get("type") == "array":
        node = node["items"]
    while "$ref" in node:
        node = HL7[_ref(node)]
    return node


def _compare(h: dict, o: dict, comps: dict, path: str, seen: set, out: list) -> None:
    key = (_ref(h.get("items", h)), _name(o))
    if key in seen:
        return
    seen.add(key)
    hp = {
        p: v
        for p, v in _hl7(h).get("properties", {}).items()
        if not p.startswith("_") and p != "resourceType"
    }
    op = _resolve(o, comps).get("properties", {})
    for name in sorted(set(hp) - set(op)):
        out.append(f"{path}.{name} is missing")
    for name in set(hp) & set(op):
        if (hp[name].get("type") == "array") != _is_array(op[name]):
            out.append(f"{path}.{name} has the wrong cardinality")
        if not (
            op[name].get("description") or _resolve(op[name], comps).get("description")
        ):
            out.append(f"{path}.{name} has no description")
        if "properties" in _hl7(hp[name]) and _name(op[name]):
            _compare(hp[name], op[name], comps, f"{path}.{name}", seen, out)


def _resources(comps: dict) -> list[str]:
    return sorted(
        d
        for d, v in HL7.items()
        if "resourceType" in v.get("properties", {}) and f"{d}CreateSchema" in comps
    )


def test_every_resource_is_published(spec):
    assert len(_resources(spec["components"]["schemas"])) == 52


def test_schemas_match_hl7_element_for_element(spec):
    comps = spec["components"]["schemas"]
    problems: list[str] = []
    seen: set = set()  # shared datatypes are compared once
    for resource in _resources(comps):
        for schema in (f"{resource}CreateSchema", f"FHIR{resource}Schema"):
            _compare(
                HL7[resource],
                {"$ref": f"#/components/schemas/{schema}"},
                comps,
                resource,
                seen,
                problems,
            )
    assert not problems, problems[:20]


def test_required_elements_are_required(spec):
    comps = spec["components"]["schemas"]
    for resource in _resources(comps):
        wanted = set(HL7[resource].get("required", [])) - {"resourceType"}
        got = set(comps[f"{resource}CreateSchema"].get("required", []))
        assert wanted <= got, (resource, wanted - got)


def test_writes_document_the_fhir_media_types(spec):
    for path, item in spec["paths"].items():
        for method, op in item.items():
            content = (op.get("requestBody") or {}).get("content", {})
            ref = content.get("application/json", {}).get("schema", {}).get("$ref", "")
            if ref.endswith("CreateSchema"):
                assert "application/fhir+json" in content, (method, path)
            if ref.endswith("PatchSchema"):
                assert {"application/fhir+json", "application/merge-patch+json"} <= set(
                    content
                ), (method, path)


def test_every_operation_is_documented(spec):
    ids: list[str] = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in VERBS:
                continue
            where = f"{method.upper()} {path}"
            assert op.get("operationId"), where
            assert op.get("summary"), where
            assert op.get("description"), where
            assert op.get("tags"), where
            for param in op.get("parameters", []):
                assert param.get("description"), (where, param["name"])
            if not path.startswith("/health"):
                assert {"401", "403"} <= set(op["responses"]), where
            ids.append(op["operationId"])
    assert len(ids) == len(set(ids)), "operation ids must be unique"


def test_no_dangling_schema_references(spec):
    comps = spec["components"]["schemas"]
    missing: set[str] = set()

    def scan(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref" and str(value).startswith("#/components/schemas/"):
                    if value.rsplit("/", 1)[-1] not in comps:
                        missing.add(value)
                else:
                    scan(value)
        elif isinstance(node, list):
            for item in node:
                scan(item)

    scan(spec)
    assert not missing, sorted(missing)[:5]

"""Shared helper for validating mapper output against google-fhir-r4.

`google-fhir-r4` carries HL7's published R4 StructureDefinitions as protobuf,
so its parser is an *independent* check on what our hand-written mappers emit.
The rest of the suite asserts what we believe the spec says; if we misread it,
those assertions encode the same misreading and pass. This does not.

It is a dev-only dependency (see pyproject's dev group): protobuf is pinned far
behind current, and parsing is orders of magnitude slower than our mappers.
Nothing in `app/` imports it — FHIR is output-only in this API, so there is
nothing to validate at runtime.

Scope: this checks the FHIR representation only. The plain snake_case format,
the DB, auth, and the search filters are covered by the integration suite.
"""

import json

from fastapi.encoders import jsonable_encoder


def fhir_json_text(mapper_output: dict) -> str:
    """Render a mapper's dict exactly as a client receives it.

    Deliberately goes through `jsonable_encoder` and `json.dumps` rather than
    handing the dict straight to the parser: `json_fhir_object_to_proto`
    rejects a Python `float` outright, because a FHIR `decimal` carries
    significant precision that a float has already lost. Our route returns
    JSON *text* (see app/core/content_negotiation.format_response), so the
    text path is both what ships and what the parser expects.
    """
    return json.dumps(jsonable_encoder(mapper_output))


def assert_valid(resource_proto_cls, mapper_output: dict) -> None:
    """Parse + validate mapper output, raising with the offending JSON attached."""
    from google.fhir.r4 import json_format

    text = fhir_json_text(mapper_output)
    try:
        json_format.json_fhir_string_to_proto(
            text, resource_proto_cls, validate=True
        )
    except Exception as exc:  # noqa: BLE001 — re-raised with context below
        raise AssertionError(
            f"mapper output is not valid FHIR R4: {type(exc).__name__}: {exc}\n"
            f"payload: {text}"
        ) from exc

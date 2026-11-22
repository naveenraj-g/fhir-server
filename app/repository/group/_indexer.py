"""
FHIR Group document -> search index. The only write-side mapper.

Group's whole resource is stored verbatim in GroupModel.content; this module derives every
*other* column and child row from it - exactly the values the FHIR R4 Group search parameters
filter on (https://www.hl7.org/fhir/R4/group.html#search), nothing more. See GroupModel's
docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.group import (
    MANAGING_ENTITY_TYPES,
    MEMBER_TYPES,
    GroupIdentifier,
    GroupMember,
    GroupToken,
    GroupType,
)
from app.repository._content_index import identifier_rows, type_rows

from ._shared import typed

_TYPES = {m.value for m in GroupType}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def index_columns(document: dict) -> dict:
    """Search columns on the group row itself."""
    group_type = document.get("type")
    actual = document.get("actual")
    return {
        "type": GroupType(group_type) if group_type in _TYPES else None,
        "actual": actual if isinstance(actual, bool) else None,
        **_ref_columns(
            "managing_entity", document.get("managingEntity"), MANAGING_ENTITY_TYPES
        ),
    }


def _concept_rows(param: str, slot: int, concept: dict | None) -> list:
    if not concept:
        return []
    return type_rows(partial(GroupToken, param=param, slot=slot), concept)


def _bool_row(param: str, slot: int, value) -> list:
    if isinstance(value, bool):
        return [GroupToken(param=param, slot=slot, code="true" if value else "false")]
    return []


def _token_rows(document: dict) -> list:
    rows = _concept_rows("code", 0, document.get("code"))
    for slot, characteristic in enumerate(
        document.get("characteristic") or [], start=1
    ):
        characteristic = characteristic or {}
        rows += _concept_rows("characteristic", slot, characteristic.get("code"))
        rows += _concept_rows("value", slot, characteristic.get("valueCodeableConcept"))
        rows += _bool_row("value", slot, characteristic.get("valueBoolean"))
        rows += _bool_row("exclude", slot, characteristic.get("exclude"))
    return rows


def _member_rows(document: dict) -> list:
    rows = []
    for member in document.get("member") or []:
        entity = (member or {}).get("entity") or {}
        reference = entity.get("reference")
        identifier = entity.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = typed(reference, MEMBER_TYPES)
        rows.append(
            GroupMember(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by GroupModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(GroupIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "members": _member_rows(document),
    }

"""
FHIR PlanDefinition document -> search index. The only write-side mapper.

PlanDefinition's whole resource is stored verbatim in PlanDefinitionModel.content; this
module derives every *other* column and child row from it - exactly the values the FHIR R4
PlanDefinition search parameters filter on
(https://www.hl7.org/fhir/R4/plandefinition.html#search), nothing more. See
PlanDefinitionModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.fhir.search.values import normalize
from app.models.plan_definition import (
    REFERENCE_PARAMS,
    PlanDefinitionContextQuantity,
    PlanDefinitionIdentifier,
    PlanDefinitionReference,
    PlanDefinitionStatus,
    PlanDefinitionToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import any_typed

_STATUSES = {m.value for m in PlanDefinitionStatus}


def index_columns(document: dict) -> dict:
    """Search columns on the plan_definition row itself."""
    status = document.get("status")
    date = document.get("date")
    date_start, date_end = (
        period_bounds({"start": date, "end": date}) if date else (None, None)
    )
    effective_start, effective_end = period_bounds(document.get("effectivePeriod"))
    return {
        "status": PlanDefinitionStatus(status) if status in _STATUSES else None,
        "url": document.get("url"),
        "version": document.get("version"),
        "name": document.get("name"),
        "name_norm": normalize(document.get("name")),
        "title": document.get("title"),
        "title_norm": normalize(document.get("title")),
        "description": document.get("description"),
        "description_norm": normalize(document.get("description")),
        "publisher": document.get("publisher"),
        "publisher_norm": normalize(document.get("publisher")),
        "date_start": date_start,
        "date_end": date_end,
        "effective_start": effective_start,
        "effective_end": effective_end,
    }


def _coding_row(model, coding: dict):
    if not (coding.get("system") or coding.get("code") or coding.get("display")):
        return None
    return model(
        system=coding.get("system"),
        code=coding.get("code"),
        display_norm=normalize(coding.get("display")),
    )


def _coding_row(model, coding: dict):
    if not (coding.get("system") or coding.get("code") or coding.get("display")):
        return None
    return model(
        system=coding.get("system"),
        code=coding.get("code"),
        display_norm=normalize(coding.get("display")),
    )


def _token_rows(document: dict) -> list:
    rows: list = []

    for param in ("jurisdiction", "topic"):
        model = partial(PlanDefinitionToken, param=param, slot=0)
        for concept in document.get(param) or []:
            rows += type_rows(model, concept)

    # type (0..1 CodeableConcept)
    if isinstance(document.get("type"), dict):
        rows += type_rows(
            partial(PlanDefinitionToken, param="type", slot=0), document["type"]
        )

    # useContext: the code and the value of the n-th useContext share slot n.
    for slot, context in enumerate(document.get("useContext") or [], start=1):
        context_type = partial(PlanDefinitionToken, param="context-type", slot=slot)
        row = _coding_row(context_type, context.get("code") or {})
        if row:
            rows.append(row)
        concept = context.get("valueCodeableConcept")
        if concept:
            rows += type_rows(
                partial(PlanDefinitionToken, param="context", slot=slot), concept
            )
    return rows


def _actions(actions) -> list[dict]:
    """Every action of the tree, at every depth, depth first."""
    out: list[dict] = []
    for action in actions or []:
        if isinstance(action, dict):
            out.append(action)
            out += _actions(action.get("action"))
    return out


def _reference_rows(document: dict) -> list:
    """One row per relatedArtifact.resource (by type -> parameter) and per `library` (also
    `depends-on`): the canonical URL as written, plus its resolved type and id when it is a
    relative `Type/<id>`."""
    values: list[tuple[str, str]] = []
    for artifact in document.get("relatedArtifact") or []:
        resource = artifact.get("resource") if isinstance(artifact, dict) else None
        if (
            isinstance(resource, str)
            and resource
            and artifact.get("type") in REFERENCE_PARAMS
        ):
            values.append((artifact["type"], resource))
    # every action's definitionCanonical, at every depth
    values += [
        ("definition", action["definitionCanonical"])
        for action in _actions(document.get("action"))
        if isinstance(action.get("definitionCanonical"), str)
        and action["definitionCanonical"]
    ]
    values += [
        ("depends-on", library)
        for library in document.get("library") or []
        if isinstance(library, str) and library
    ]
    rows = []
    for param, value in values:
        parsed = any_typed(value)
        rows.append(
            PlanDefinitionReference(
                param=param,
                reference_reference=value,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
            )
        )
    return rows


def _number(quantity: dict | None):
    value = (quantity or {}).get("value")
    return value if isinstance(value, (int, float)) else None


def _context_quantity_rows(document: dict) -> list:
    """One row per useContext whose value[x] is a Quantity (a point) or a Range."""
    rows = []
    for slot, context in enumerate(document.get("useContext") or [], start=1):
        quantity = context.get("valueQuantity")
        rng = context.get("valueRange")
        if quantity:
            low = high = _number(quantity)
            unit_source = quantity
        elif rng:
            low, high = _number(rng.get("low")), _number(rng.get("high"))
            unit_source = (rng.get("low") if low is not None else rng.get("high")) or {}
        else:
            continue
        if low is None and high is None:
            continue
        rows.append(
            PlanDefinitionContextQuantity(
                slot=slot,
                quantity_low=low,
                quantity_high=high,
                quantity_system=unit_source.get("system"),
                quantity_code=unit_source.get("code"),
                quantity_unit=unit_source.get("unit"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by PlanDefinitionModel relationship name."""
    return {
        "identifiers": [
            row
            for identifier in document.get("identifier") or []
            for row in identifier_rows(PlanDefinitionIdentifier, identifier)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "context_quantities": _context_quantity_rows(document),
    }

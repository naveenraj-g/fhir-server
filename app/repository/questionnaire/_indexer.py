"""
FHIR Questionnaire document -> search index. The only write-side mapper.

Questionnaire's whole resource is stored verbatim in QuestionnaireModel.content; this module
derives every *other* column and child row from it - exactly the values the FHIR R4 Questionnaire
search parameters filter on (https://www.hl7.org/fhir/R4/questionnaire.html#search), nothing
more. See QuestionnaireModel's docstring for the parameter -> storage table; the shared builders
are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.fhir.search.values import normalize
from app.models.questionnaire import (
    QuestionnaireContextQuantity,
    QuestionnaireDefinition,
    QuestionnaireIdentifier,
    QuestionnaireStatus,
    QuestionnaireSubjectType,
    QuestionnaireToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

_STATUSES = {m.value for m in QuestionnaireStatus}
_SUBJECT_TYPES = {m.value for m in QuestionnaireSubjectType}


def _subject_types(document: dict):
    """Questionnaire.subjectType (0..*) as enum members; None when there is none (a code outside
    the value set is dropped: the validator rejects it before we get here)."""
    values = [
        QuestionnaireSubjectType(c)
        for c in document.get("subjectType") or []
        if c in _SUBJECT_TYPES
    ]
    return values or None


def index_columns(document: dict) -> dict:
    """Search columns on the questionnaire row itself."""
    status = document.get("status")
    date = document.get("date")
    date_start, date_end = (
        period_bounds({"start": date, "end": date}) if date else (None, None)
    )
    effective_start, effective_end = period_bounds(document.get("effectivePeriod"))
    return {
        "status": QuestionnaireStatus(status) if status in _STATUSES else None,
        "subject_type": _subject_types(document),
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


def _items(items) -> list[dict]:
    """Every item of the tree, at every depth, depth first."""
    out: list[dict] = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(item)
            out += _items(item.get("item"))
    return out


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

    model = partial(QuestionnaireToken, param="jurisdiction", slot=0)
    for concept in document.get("jurisdiction") or []:
        rows += type_rows(model, concept)

    # item.code: every Coding of every item, at every depth.
    model = partial(QuestionnaireToken, param="code", slot=0)
    for item in _items(document.get("item")):
        rows += [
            r for r in (_coding_row(model, c) for c in item.get("code") or []) if r
        ]

    # useContext: the code and the value of the n-th useContext share slot n.
    for slot, context in enumerate(document.get("useContext") or [], start=1):
        context_type = partial(QuestionnaireToken, param="context-type", slot=slot)
        row = _coding_row(context_type, context.get("code") or {})
        if row:
            rows.append(row)
        concept = context.get("valueCodeableConcept")
        if concept:
            rows += type_rows(
                partial(QuestionnaireToken, param="context", slot=slot), concept
            )
    return rows


def _definition_rows(document: dict) -> list:
    return [
        QuestionnaireDefinition(uri=item["definition"])
        for item in _items(document.get("item"))
        if item.get("definition")
    ]


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
            QuestionnaireContextQuantity(
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
    """Child index rows, keyed by QuestionnaireModel relationship name."""
    return {
        "identifiers": [
            row
            for identifier in document.get("identifier") or []
            for row in identifier_rows(QuestionnaireIdentifier, identifier)
        ],
        "tokens": _token_rows(document),
        "definitions": _definition_rows(document),
        "context_quantities": _context_quantity_rows(document),
    }

"""
FHIR DocumentReference document -> search index. The only write-side mapper.

DocumentReference's whole resource is stored verbatim in DocumentReferenceModel.content; this
module derives every *other* column and child row from it - exactly the values the FHIR R4
DocumentReference search parameters filter on
(https://www.hl7.org/fhir/R4/documentreference.html#search), nothing more. See
DocumentReferenceModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import partial

from app.fhir.search.values import normalize, parse_date
from app.models.document_reference import (
    AUTHENTICATOR_TYPES,
    CUSTODIAN_TYPES,
    REFERENCE_TYPES,
    RELATES_TO_TYPES,
    SUBJECT_TYPES,
    DocumentReferenceContent,
    DocumentReferenceIdentifier,
    DocumentReferenceReference,
    DocumentReferenceRelatesTo,
    DocumentReferenceStatus,
    DocumentReferenceToken,
    DocumentRelationshipType,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import any_typed, typed

_STATUSES = {m.value for m in DocumentReferenceStatus}
_RELATIONS = {m.value for m in DocumentRelationshipType}


def _instant(value) -> datetime | None:
    """DocumentReference.date as a UTC datetime (None if absent or unparseable - a bad instant is
    the validator's to reject)."""
    if not value:
        return None
    try:
        return parse_date(str(value)).low.astimezone(UTC)
    except Exception:
        return None


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
    """Search columns on the document_reference row itself."""
    status = document.get("status")
    description = document.get("description")
    start, end = period_bounds((document.get("context") or {}).get("period"))
    return {
        "status": DocumentReferenceStatus(status) if status in _STATUSES else None,
        "date": _instant(document.get("date")),
        "description": description,
        "description_norm": normalize(description) if description else None,
        "context_period_start": start,
        "context_period_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns(
            "authenticator", document.get("authenticator"), AUTHENTICATOR_TYPES
        ),
        **_ref_columns("custodian", document.get("custodian"), CUSTODIAN_TYPES),
    }


def _identifier_rows(document: dict) -> list:
    identifiers = [
        document.get("masterIdentifier"),
        *(document.get("identifier") or []),
    ]
    return [
        r
        for i in identifiers
        if i
        for r in identifier_rows(DocumentReferenceIdentifier, i)
    ]


def _token_rows(document: dict) -> list:
    context = document.get("context") or {}
    concepts = [
        ("type", [document.get("type")]),
        ("category", document.get("category") or []),
        ("security-label", document.get("securityLabel") or []),
        ("event", context.get("event") or []),
        ("facility", [context.get("facilityType")]),
        ("setting", [context.get("practiceSetting")]),
    ]
    rows = []
    for param, values in concepts:
        for concept in values:
            if concept:
                rows += type_rows(partial(DocumentReferenceToken, param=param), concept)
    return rows


def _reference_row(param: str, ref: dict | None) -> DocumentReferenceReference | None:
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = (
        any_typed(reference)
        if param == "related"
        else typed(reference, REFERENCE_TYPES[param])
    )
    return DocumentReferenceReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    context = document.get("context") or {}
    rows = [_reference_row("author", r) for r in document.get("author") or []]
    rows += [_reference_row("encounter", r) for r in context.get("encounter") or []]
    rows += [_reference_row("related", r) for r in context.get("related") or []]
    return [r for r in rows if r]


def _relates_to_rows(document: dict) -> list:
    rows = []
    for entry in document.get("relatesTo") or []:
        entry = entry or {}
        code = entry.get("code")
        target = entry.get("target") or {}
        reference = target.get("reference")
        identifier = target.get("identifier") or {}
        if not (code or reference or identifier.get("value")):
            continue
        parsed = typed(reference, RELATES_TO_TYPES)
        rows.append(
            DocumentReferenceRelatesTo(
                code=DocumentRelationshipType(code) if code in _RELATIONS else None,
                target_reference=reference,
                target_type=parsed[0] if parsed else None,
                target_id=parsed[1] if parsed else None,
                target_identifier_system=identifier.get("system"),
                target_identifier_value=identifier.get("value"),
            )
        )
    return rows


def _content_rows(document: dict) -> list:
    rows = []
    for entry in document.get("content") or []:
        entry = entry or {}
        attachment = entry.get("attachment") or {}
        fmt = entry.get("format") or {}
        row = DocumentReferenceContent(
            content_type=attachment.get("contentType"),
            language=attachment.get("language"),
            url=attachment.get("url"),
            format_system=fmt.get("system"),
            format_code=fmt.get("code"),
            format_display_norm=normalize(fmt["display"])
            if fmt.get("display")
            else None,
        )
        if any(
            (
                row.content_type,
                row.language,
                row.url,
                row.format_system,
                row.format_code,
                row.format_display_norm,
            )
        ):
            rows.append(row)
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by DocumentReferenceModel relationship name."""
    return {
        "identifiers": _identifier_rows(document),
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "relates_to": _relates_to_rows(document),
        "contents": _content_rows(document),
    }

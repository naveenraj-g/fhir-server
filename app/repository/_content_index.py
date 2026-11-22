"""
Shared builders for the search index of resources stored Medplum-style
(Organization, Location): the derived columns / child rows a FHIR search
parameter matches on, computed from the stored FHIR document.

The child-row builders take the index model class, since each resource has
its own identical-shaped tables (OrganizationIdentifier / LocationIdentifier
...). Each resource's `_indexer.py` composes these.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.fhir.search import normalize
from app.fhir.search.values import parse_date


def period_bounds(period: dict | None) -> tuple[datetime | None, datetime | None]:
    """(start, end) instants for a FHIR Period's index columns — the half-open
    [start, end) range the period covers (see app.fhir.search.sql.period_match),
    in UTC. `start` is the first instant of Period.start (as precise as it was
    written: `2026-01` -> 2026-01-01T00:00Z); `end` is the first instant *after*
    Period.end at its written precision (`2026-12` -> 2027-01-01T00:00Z). A
    missing or unparseable bound is None (open)."""
    period = period or {}

    def bound(value, which):
        if not value:
            return None
        try:
            parsed = parse_date(str(value))
        except Exception:  # a malformed dateTime is the validator's to reject
            return None
        return getattr(parsed, which).astimezone(UTC)

    return bound(period.get("start"), "low"), bound(period.get("end"), "high")


def relative(reference: str | None, resource_type: str) -> str | None:
    """`reference` if it's a relative `<resource_type>/<id>` reference —
    the only shape that can resolve to a local row. Absolute URLs,
    contained (`#x`) and other types are matched by their raw string only."""
    if reference and reference.startswith(f"{resource_type}/"):
        return reference
    return None


def strings(values) -> list[str] | None:
    """Non-empty strings of a 0..* string list; None when there are none
    (so an array index column is NULL, and `:missing` is IS NULL)."""
    out = [v for v in values or [] if v]
    return out or None


def norms(values: list[str] | None) -> list[str] | None:
    return [normalize(v) for v in values] if values else None


def parse_relative(reference: str, resource_type: str) -> tuple[str, int]:
    """`Type/123` -> ("Type", 123): the type as a plain string and the target's public id.
    A reference whose id is not a number is a 422 (it can never resolve)."""
    _type, _, raw_id = reference.partition("/")
    try:
        return resource_type, int(raw_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{reference}'. Id must be an integer.",
        )


def reference_columns(prefix: str, ref: dict | None, resource_type: str) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the
    raw string), `{prefix}_type`/`{prefix}_id` (the type as a plain string and
    the public id - relative references only), and
    `{prefix}_identifier_system`/`_value` (Reference.identifier)."""
    ref = ref or {}
    local = relative(ref.get("reference"), resource_type)
    ref_type, ref_id = parse_relative(local, resource_type) if local else (None, None)
    identifier = ref.get("identifier") or {}
    return {
        f"{prefix}_reference": ref.get("reference"),
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def identifier_rows(model, identifier: dict) -> list:
    """One index row per Identifier.type.coding (one type-less row when
    there is no coded type), so `identifier:of-type` matches type and value
    on the same row. Nothing for an identifier with neither system nor value."""
    if not (identifier.get("system") or identifier.get("value")):
        return []
    id_type = identifier.get("type") or {}
    return [
        model(
            system=identifier.get("system"),
            value=identifier.get("value"),
            type_system=c.get("system"),
            type_code=c.get("code"),
            type_text_norm=normalize(id_type.get("text")),
            type_display_norm=normalize(c.get("display")),
        )
        for c in id_type.get("coding") or [{}]
    ]


def type_rows(model, concept: dict) -> list:
    """One index row per CodeableConcept.coding, plus a code-less row for a
    concept that only has `text` (so `:text` still finds it)."""
    text = normalize(concept.get("text"))
    rows = [
        model(
            system=c.get("system"),
            code=c.get("code"),
            display_norm=normalize(c.get("display")),
            text_norm=text,
        )
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    if not rows and text:
        rows.append(model(text_norm=text))
    return rows


def endpoint_row(model, endpoint: dict):
    """One index row for a Reference(Endpoint) with a `reference` or an
    `identifier` (display-only can't be matched by a reference search)."""
    reference = endpoint.get("reference")
    identifier = endpoint.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    local = relative(reference, "Endpoint")
    ref_type, ref_id = parse_relative(local, "Endpoint") if local else (None, None)
    return model(
        reference_reference=reference,
        reference_type=ref_type,
        reference_id=ref_id,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )

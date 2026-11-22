"""
FHIR Specimen document -> search index. The only write-side mapper.

Specimen's whole resource is stored verbatim in SpecimenModel.content; this module derives every
*other* column and child row from it — exactly the values the FHIR R4 Specimen search
parameters filter on (https://www.hl7.org/fhir/R4/specimen.html#search), nothing more. See
SpecimenModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.specimen import (
    COLLECTOR_TYPES,
    SUBJECT_TYPES,
    SpecimenContainerIdentifier,
    SpecimenIdentifier,
    SpecimenReference,
    SpecimenStatus,
    SpecimenToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import any_typed, typed

_STATUSES = {m.value for m in SpecimenStatus}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw
    string), `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an
    allowed type) and `{prefix}_identifier_system`/`_value`."""
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


def _collected_bounds(collection: dict):
    """The half-open range collection.collected[x] covers: a dateTime as the range of its
    precision, a Period from its start to the instant after its end (NULL = open)."""
    value = collection.get("collectedDateTime")
    if value:
        return period_bounds({"start": value, "end": value})
    return period_bounds(collection.get("collectedPeriod"))


def index_columns(document: dict) -> dict:
    """Search columns on the specimen row itself."""
    collection = document.get("collection") or {}
    start, end = _collected_bounds(collection)
    accession = document.get("accessionIdentifier") or {}
    status = document.get("status")
    return {
        "status": SpecimenStatus(status) if status in _STATUSES else None,
        "collected_start": start,
        "collected_end": end,
        "accession_system": accession.get("system"),
        "accession_value": accession.get("value"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("collector", collection.get("collector"), COLLECTOR_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return type_rows(partial(SpecimenToken, param=param), concept) if concept else []


def _token_rows(document: dict) -> list:
    rows = _concept("type", document.get("type"))
    rows += _concept("bodysite", (document.get("collection") or {}).get("bodySite"))
    for container in document.get("container") or []:
        rows += _concept("container", (container or {}).get("type"))
    return rows


def _reference_row(param: str, ref: dict | None) -> SpecimenReference | None:
    """One index row for a Reference with a `reference` or an `identifier` (display-only cannot
    be matched by a reference search). Any relative `Type/<id>` names a type."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference)
    return SpecimenReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by SpecimenModel relationship name."""
    references = [_reference_row("parent", r) for r in document.get("parent") or []]
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(SpecimenIdentifier, i)
        ],
        "container_identifiers": [
            r
            for container in document.get("container") or []
            for i in (container or {}).get("identifier") or []
            for r in identifier_rows(SpecimenContainerIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": [r for r in references if r],
    }

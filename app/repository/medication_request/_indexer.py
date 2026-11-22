"""
FHIR MedicationRequest document -> search index. The only write-side mapper.

MedicationRequest's whole resource is stored verbatim in MedicationRequestModel.content; this
module derives every *other* column and child row from it - exactly the values the FHIR R4
MedicationRequest search parameters filter on
(https://www.hl7.org/fhir/R4/medicationrequest.html#search), nothing more. See
MedicationRequestModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication_request import (
    DISPENSER_TYPES,
    MEDICATION_TYPES,
    PERFORMER_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    MedicationRequestIdentifier,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
    MedicationRequestTiming,
    MedicationRequestToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import typed

_STATUSES = {m.value for m in MedicationRequestStatus}
_INTENTS = {m.value for m in MedicationRequestIntent}
_PRIORITIES = {m.value for m in MedicationRequestPriority}


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


def _point(value):
    """The half-open range a dateTime covers at its written precision, or (None, None)."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _code(value, allowed, enum):
    return enum(value) if value in allowed else None


def index_columns(document: dict) -> dict:
    """Search columns on the medication_request row itself."""
    authored_start, authored_end = _point(document.get("authoredOn"))
    return {
        "status": _code(document.get("status"), _STATUSES, MedicationRequestStatus),
        "intent": _code(document.get("intent"), _INTENTS, MedicationRequestIntent),
        "priority": _code(
            document.get("priority"), _PRIORITIES, MedicationRequestPriority
        ),
        "authored_start": authored_start,
        "authored_end": authored_end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
        **_ref_columns("performer", document.get("performer"), PERFORMER_TYPES),
        **_ref_columns(
            "medication", document.get("medicationReference"), MEDICATION_TYPES
        ),
        **_ref_columns(
            "dispenser",
            (document.get("dispenseRequest") or {}).get("performer"),
            DISPENSER_TYPES,
        ),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(MedicationRequestToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    rows += _concept("code", document.get("medicationCodeableConcept"))
    rows += _concept("intended-performertype", document.get("performerType"))
    return rows


def _timing_rows(document: dict) -> list:
    """One row per dosageInstruction.timing.event (a dateTime) of every dosage instruction."""
    rows = []
    for dosage in document.get("dosageInstruction") or []:
        timing = (dosage or {}).get("timing") or {}
        for event in timing.get("event") or []:
            start, end = _point(event)
            if start or end:
                rows.append(MedicationRequestTiming(event_start=start, event_end=end))
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationRequestModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(MedicationRequestIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "timings": _timing_rows(document),
    }

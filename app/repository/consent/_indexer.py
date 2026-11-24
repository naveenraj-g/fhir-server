"""
FHIR Consent document -> search index. The only write-side mapper.

Consent's whole resource is stored verbatim in ConsentModel.content; this module derives every
*other* column and child row from it - exactly the values the FHIR R4 Consent search parameters
filter on (https://www.hl7.org/fhir/R4/consent.html#search), nothing more. See ConsentModel's
docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

R4's expressions read the top-level `provision` only (`Consent.provision.actor.reference`), so a
nested `provision.provision` is stored but not indexed.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.consent import (
    ACTOR_TYPES,
    CONSENTOR_TYPES,
    ORGANIZATION_TYPES,
    PATIENT_TYPES,
    SOURCE_TYPES,
    ConsentIdentifier,
    ConsentReference,
    ConsentStatus,
    ConsentToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import any_typed, typed

_STATUSES = {m.value for m in ConsentStatus}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
    ref = ref if isinstance(ref, dict) else {}
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


def _range(value) -> tuple:
    """The half-open range a FHIR dateTime covers (None, None when absent)."""
    if not isinstance(value, str) or not value:
        return None, None
    return period_bounds({"start": value, "end": value})


def _provision(document: dict) -> dict:
    provision = document.get("provision")
    return provision if isinstance(provision, dict) else {}


def index_columns(document: dict) -> dict:
    """Search columns on the consent row itself."""
    status = document.get("status")
    date = _range(document.get("dateTime"))
    period = _provision(document).get("period")
    period = period_bounds(period if isinstance(period, dict) else None)
    return {
        "status": ConsentStatus(status) if status in _STATUSES else None,
        "date_start": date[0],
        "date_end": date[1],
        "period_start": period[0],
        "period_end": period[1],
        **_ref_columns("patient", document.get("patient"), PATIENT_TYPES),
        **_ref_columns("source", document.get("sourceReference"), SOURCE_TYPES),
    }


def _concept(param: str, concept) -> list:
    return (
        type_rows(partial(ConsentToken, param=param), concept)
        if isinstance(concept, dict)
        else []
    )


def _coding(param: str, coding) -> list:
    """A Coding is searched like a one-coding CodeableConcept."""
    return _concept(param, {"coding": [coding]}) if isinstance(coding, dict) else []


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    rows += _concept("scope", document.get("scope"))
    provision = _provision(document)
    for action in provision.get("action") or []:
        rows += _concept("action", action)
    for purpose in provision.get("purpose") or []:
        rows += _coding("purpose", purpose)
    for label in provision.get("securityLabel") or []:
        rows += _coding("security-label", label)
    return rows


def _reference_row(param: str, ref, allowed: tuple[str, ...] | None):
    """One index row for a Reference that has a `reference` or an `identifier` (display-only
    cannot be matched by a reference search). `allowed` None means a Reference(Any)."""
    if not isinstance(ref, dict):
        return None
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return ConsentReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    provision = _provision(document)
    rows = [
        _reference_row("consentor", r, CONSENTOR_TYPES)
        for r in document.get("performer") or []
    ]
    rows += [
        _reference_row("organization", r, ORGANIZATION_TYPES)
        for r in document.get("organization") or []
    ]
    rows += [
        _reference_row("actor", (a or {}).get("reference"), ACTOR_TYPES)
        for a in provision.get("actor") or []
    ]
    rows += [
        _reference_row("data", (d or {}).get("reference"), None)
        for d in provision.get("data") or []
    ]
    return [r for r in rows if r is not None]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ConsentModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ConsentIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }

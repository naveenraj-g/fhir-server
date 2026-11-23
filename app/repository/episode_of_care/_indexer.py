"""
FHIR EpisodeOfCare document -> search index. The only write-side mapper.

EpisodeOfCare's whole resource is stored verbatim in EpisodeOfCareModel.content; this module
derives every *other* column and child row from it - exactly the values the FHIR R4 EpisodeOfCare
search parameters filter on (https://www.hl7.org/fhir/R4/episodeofcare.html#search), nothing more.
See EpisodeOfCareModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.episode_of_care import (
    CARE_MANAGER_TYPES,
    ORGANIZATION_TYPES,
    PATIENT_TYPES,
    REFERENCE_TYPES,
    EpisodeOfCareIdentifier,
    EpisodeOfCareReference,
    EpisodeOfCareStatus,
    EpisodeOfCareToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import typed

_STATUSES = {m.value for m in EpisodeOfCareStatus}


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
    """Search columns on the episode_of_care row itself."""
    start, end = period_bounds(document.get("period"))
    status = document.get("status")
    return {
        "status": EpisodeOfCareStatus(status) if status in _STATUSES else None,
        "period_start": start,
        "period_end": end,
        **_ref_columns("patient", document.get("patient"), PATIENT_TYPES),
        **_ref_columns(
            "managing_organization",
            document.get("managingOrganization"),
            ORGANIZATION_TYPES,
        ),
        **_ref_columns("care_manager", document.get("careManager"), CARE_MANAGER_TYPES),
    }


def _token_rows(document: dict) -> list:
    rows = []
    for concept in document.get("type") or []:
        if concept:
            rows += type_rows(partial(EpisodeOfCareToken, param="type"), concept)
    return rows


def _reference_row(param: str, ref: dict | None) -> EpisodeOfCareReference | None:
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, REFERENCE_TYPES[param])
    return EpisodeOfCareReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [
        _reference_row("condition", (diagnosis or {}).get("condition"))
        for diagnosis in document.get("diagnosis") or []
    ]
    rows += [
        _reference_row("incoming-referral", ref)
        for ref in document.get("referralRequest") or []
    ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by EpisodeOfCareModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(EpisodeOfCareIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }

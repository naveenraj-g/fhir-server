"""
FHIR CareTeam document -> search index. The only write-side mapper.

CareTeam's whole resource is stored verbatim in CareTeamModel.content; this module derives
every *other* column and child row from it - exactly the values the FHIR R4 CareTeam search
parameters filter on (https://www.hl7.org/fhir/R4/careteam.html#search), nothing more. See
CareTeamModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.care_team import (
    ENCOUNTER_TYPES,
    PARTICIPANT_TYPES,
    SUBJECT_TYPES,
    CareTeamIdentifier,
    CareTeamParticipant,
    CareTeamStatus,
    CareTeamToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import typed

_STATUSES = {m.value for m in CareTeamStatus}
# Annotation.author[x] reference targets in R4.
_NOTE_AUTHOR_TYPES = ("Practitioner", "Patient", "RelatedPerson", "Organization")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local reference that must
    exist in the caller's org on write: `identifier.assigner`, `subject` (a Patient or Group),
    `encounter`, every `participant.member` (Practitioner, PractitionerRole, RelatedPerson,
    Patient, Organization or CareTeam) and `participant.onBehalfOf`, `reasonReference`
    (Condition), every `managingOrganization` and every note's `authorReference`. Absolute
    URLs and logical (identifier-only) references point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    def add_typed(label, ref, allowed):
        parsed = typed((ref or {}).get("reference"), allowed)
        if parsed:
            refs.append((label, parsed[0], ref["reference"]))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add_typed("subject", document.get("subject"), SUBJECT_TYPES)
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    for participant in document.get("participant") or []:
        participant = participant or {}
        add_typed("participant.member", participant.get("member"), PARTICIPANT_TYPES)
        add(
            "participant.onBehalfOf",
            (participant.get("onBehalfOf") or {}).get("reference"),
            "Organization",
        )
    for ref in document.get("reasonReference") or []:
        add("reasonReference", (ref or {}).get("reference"), "Condition")
    for ref in document.get("managingOrganization") or []:
        add("managingOrganization", (ref or {}).get("reference"), "Organization")
    for note in document.get("note") or []:
        add_typed(
            "note.authorReference",
            (note or {}).get("authorReference"),
            _NOTE_AUTHOR_TYPES,
        )
    return refs


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
    """Search columns on the care_team row itself."""
    start, end = period_bounds(document.get("period"))
    status = document.get("status")
    return {
        "status": CareTeamStatus(status) if status in _STATUSES else None,
        "period_start": start,
        "period_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
    }


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        if category:
            rows += type_rows(partial(CareTeamToken, param="category"), category)
    return rows


def _participant_rows(document: dict) -> list:
    rows = []
    for participant in document.get("participant") or []:
        member = (participant or {}).get("member") or {}
        reference = member.get("reference")
        identifier = member.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = typed(reference, PARTICIPANT_TYPES)
        rows.append(
            CareTeamParticipant(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by CareTeamModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(CareTeamIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "participants": _participant_rows(document),
    }

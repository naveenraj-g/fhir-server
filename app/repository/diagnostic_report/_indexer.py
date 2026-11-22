"""
FHIR DiagnosticReport document -> search index. The only write-side mapper.

DiagnosticReport's whole resource is stored verbatim in
DiagnosticReportModel.content; this module derives every *other* column and child
row from it — exactly the values the FHIR R4 DiagnosticReport search parameters
filter on (https://www.hl7.org/fhir/R4/diagnosticreport.html#search), nothing
more. See DiagnosticReportModel's docstring for the parameter -> storage table; the
shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.diagnostic_report import (
    PERFORMER_PARAMS,
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    DiagnosticReportIdentifier,
    DiagnosticReportPerformer,
    DiagnosticReportReference,
    DiagnosticReportStatus,
    DiagnosticReportToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import ref_type_and_id, typed

# Of the four performer / resultsInterpreter targets, these are resources here.
_MODELED_PERFORMERS = ("Practitioner", "PractitionerRole", "Organization")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    `subject` (a Patient or a Location), `encounter`, and every `performer` /
    `resultsInterpreter` that is a Practitioner, PractitionerRole or Organization, and
    every `result` (an Observation), `specimen` (a Specimen) and `basedOn` that is a ServiceRequest.
    Absolute URLs, logical (identifier-only) references and targets that are not
    resources on this server (a Group or Device subject, a CareTeam, a CarePlan basedOn,
    media, imagingStudy) point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    subject = (document.get("subject") or {}).get("reference")
    add("subject", subject, "Patient")
    add("subject", subject, "Location")
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    for element in ("performer", "resultsInterpreter"):
        for ref in document.get(element) or []:
            parsed = typed(ref.get("reference"), _MODELED_PERFORMERS)
            if parsed:
                refs.append((element, parsed[0], ref["reference"]))
    for element, target in (
        ("result", "Observation"),
        ("specimen", "Specimen"),
        ("basedOn", "ServiceRequest"),
    ):
        for ref in document.get(element) or []:
            parsed = typed((ref or {}).get("reference"), (target,))
            if parsed:
                refs.append((element, parsed[0], ref["reference"]))
    return refs


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


def _instant_bounds(value):
    """(start, end) of the half-open range a dateTime covers at its written
    precision; (None, None) when absent."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _issued(value):
    """DiagnosticReport.issued as a UTC datetime (None if absent or unparseable —
    a bad instant is the validator's to reject)."""
    return _instant_bounds(value)[0]


def index_columns(document: dict) -> dict:
    """Search columns on the diagnostic_report row itself."""
    status = document.get("status")
    try:
        status = DiagnosticReportStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    if document.get("effectiveDateTime"):
        effective_start, effective_end = _instant_bounds(document["effectiveDateTime"])
    else:
        effective_start, effective_end = period_bounds(document.get("effectivePeriod"))
    return {
        "status": status,
        "effective_date_start": effective_start,
        "effective_date_end": effective_end,
        "issued": _issued(document.get("issued")),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(DiagnosticReportToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept_rows("category", category)
    rows += _concept_rows("code", document.get("code"))
    for conclusion in document.get("conclusionCode") or []:
        rows += _concept_rows("conclusion", conclusion)
    return rows


def _reference_row(param: str, ref: dict | None) -> DiagnosticReportReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return DiagnosticReportReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("based-on", r) for r in document.get("basedOn") or []]
    rows += [
        _reference_row("media", (m or {}).get("link"))
        for m in document.get("media") or []
    ]
    rows += [_reference_row("result", r) for r in document.get("result") or []]
    rows += [_reference_row("specimen", r) for r in document.get("specimen") or []]
    return [r for r in rows if r]


def _performer_rows(document: dict) -> list:
    rows = []
    for param, element in PERFORMER_PARAMS.items():
        for ref in document.get(element) or []:
            reference = (ref or {}).get("reference")
            identifier = (ref or {}).get("identifier") or {}
            if not (reference or identifier.get("value")):
                continue
            parsed = typed(reference, PERFORMER_TYPES)
            rows.append(
                DiagnosticReportPerformer(
                    param=param,
                    reference_reference=reference,
                    reference_type=parsed[0] if parsed else None,
                    reference_id=parsed[1] if parsed else None,
                    reference_identifier_system=identifier.get("system"),
                    reference_identifier_value=identifier.get("value"),
                )
            )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by DiagnosticReportModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(DiagnosticReportIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "performers": _performer_rows(document),
    }

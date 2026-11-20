from enum import Enum


class EncounterStatus(str, Enum):
    """FHIR R4 Encounter.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-encounter-status.html

    Stored in Postgres by *value*, so the true FHIR codes (`in-progress`,
    `entered-in-error`) are what the column holds; the Python member names are
    the underscore forms only because `in-progress` is not an identifier. See
    EncounterModel's `values_callable`."""

    planned = "planned"
    arrived = "arrived"
    triaged = "triaged"
    in_progress = "in-progress"
    onleave = "onleave"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"

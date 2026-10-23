from enum import Enum


class SlotStatus(str, Enum):
    """FHIR R4 Slot.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-slotstatus.html

    Member name intentionally equals member value (both underscore-only,
    not the true hyphenated FHIR code) — see CLAUDE.md's FHIR DB Model
    Design "Alembic autogenerate enum values are correct (key = value
    convention)" invariant: SQLAlchemy's `Enum(PyEnum)` stores each
    member's `.name` in Postgres by default, so fighting that with
    `values_callable` just to get hyphens into the DB buys nothing — the
    real `busy-unavailable`/`busy-tentative`/`entered-in-error` FHIR codes
    are rendered explicitly in app/fhir/mappers/slot/fhir.py instead.
    """

    busy = "busy"
    free = "free"
    busy_unavailable = "busy_unavailable"
    busy_tentative = "busy_tentative"
    entered_in_error = "entered_in_error"

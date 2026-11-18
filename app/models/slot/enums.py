from enum import Enum


class SlotStatus(str, Enum):
    """FHIR R4 Slot.status (1..1, required binding) — the free/busy status of
    the slot. https://www.hl7.org/fhir/R4/valueset-slotstatus.html

    Stored by VALUE, so the real hyphenated FHIR codes (`busy-unavailable`,
    `busy-tentative`, `entered-in-error`) are what the database and the search
    index hold — see the `values_callable` on SlotModel.status.
    """

    busy = "busy"
    free = "free"
    busy_unavailable = "busy-unavailable"
    busy_tentative = "busy-tentative"
    entered_in_error = "entered-in-error"

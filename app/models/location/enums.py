from enum import Enum


class LocationStatus(str, Enum):
    """FHIR R4 Location.status (0..1, required binding) — general availability
    of the location.
    https://www.hl7.org/fhir/R4/valueset-location-status.html
    """

    active = "active"
    suspended = "suspended"
    inactive = "inactive"


class LocationMode(str, Enum):
    """FHIR R4 Location.mode (0..1, required binding) — whether the row
    describes one specific place ("instance") or a class of places ("kind",
    e.g. "a general ward bed").
    https://www.hl7.org/fhir/R4/valueset-location-mode.html
    """

    instance = "instance"
    kind = "kind"

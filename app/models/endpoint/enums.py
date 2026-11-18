from enum import Enum


class EndpointStatus(str, Enum):
    """FHIR R4 Endpoint.status (1..1, required binding) — the interface
    status of the endpoint.
    https://www.hl7.org/fhir/R4/valueset-endpoint-status.html

    Stored by VALUE (`entered-in-error`, not the Python name) — see the
    `values_callable` on EndpointModel.status.
    """

    active = "active"
    suspended = "suspended"
    error = "error"
    off = "off"
    entered_in_error = "entered-in-error"
    test = "test"

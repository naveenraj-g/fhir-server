from enum import Enum


class ConsentStatus(str, Enum):
    """Consent.status (ConsentState, required) - stored by value, so `entered-in-error` is the
    real FHIR code. https://www.hl7.org/fhir/R4/valueset-consent-state-codes.html"""

    draft = "draft"
    proposed = "proposed"
    active = "active"
    rejected = "rejected"
    inactive = "inactive"
    entered_in_error = "entered-in-error"

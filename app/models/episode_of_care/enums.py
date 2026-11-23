from enum import Enum


class EpisodeOfCareStatus(str, Enum):
    """EpisodeOfCare.status (episode-of-care-status, required) - stored by value, so the
    real FHIR code `entered-in-error` is what the database holds."""

    planned = "planned"
    waitlist = "waitlist"
    active = "active"
    onhold = "onhold"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"

from enum import Enum


class CareTeamStatus(str, Enum):
    """CareTeam.status (care-team-status, required) - stored by value."""

    proposed = "proposed"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"
    entered_in_error = "entered-in-error"

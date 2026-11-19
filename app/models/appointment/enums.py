from enum import Enum


class AppointmentStatus(str, Enum):
    """FHIR R4 Appointment.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-appointmentstatus.html

    Stored by VALUE, so the real hyphenated FHIR codes (`entered-in-error`,
    `checked-in`) are what the database and the search index hold — see the
    `values_callable` on AppointmentModel.status.
    """

    proposed = "proposed"
    pending = "pending"
    booked = "booked"
    arrived = "arrived"
    fulfilled = "fulfilled"
    cancelled = "cancelled"
    noshow = "noshow"
    entered_in_error = "entered-in-error"
    checked_in = "checked-in"
    waitlist = "waitlist"

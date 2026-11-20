from enum import Enum


class AppointmentResponseParticipantStatus(str, Enum):
    """FHIR R4 AppointmentResponse.participantStatus (1..1, required
    binding) — https://www.hl7.org/fhir/R4/valueset-participationstatus.html

    Stored by VALUE, so the real hyphenated FHIR code (`needs-action`) is what
    the database and the search index hold — see the `values_callable` on
    AppointmentResponseModel.participant_status.
    """

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"

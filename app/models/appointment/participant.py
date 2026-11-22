from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

from .enums import AppointmentParticipantStatus

# The seven R4 targets of Appointment.participant.actor.
ACTOR_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Device",
    "HealthcareService",
    "Location",
)


class AppointmentParticipant(Base):
    """Search index for the participant parameters — `actor`, `patient`,
    `practitioner`, `location` (all the same element, narrowed by the type
    the actor resolves to) and `part-status`. One row per
    Appointment.participant (even one with no actor, so `part-status` still
    finds it). Derived from AppointmentModel.content — never read to build a
    response.

    `actor` can point at seven resource types, so `reference_type` records
    which one a relative `Type/<id>` names (a plain string, not an enum):

      actor                -> reference_type/reference_id or reference_reference
      patient / practitioner / location
                           -> the same row, with reference_type = Patient |
                              Practitioner | Location
      actor:identifier     -> reference_identifier_system/_value
      part-status          -> status (the raw participation status code)

    No ForeignKey on `reference_id` and no UniqueConstraint."""

    __tablename__ = "appointment_participant"
    __table_args__ = (
        Index("ix_appointment_participant_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    # participant.status (1..1 code, required binding `participationstatus`): an Enum stored by
    # value, so `needs-action` is the real FHIR code. NULL when the code is not one of the four.
    status = Column(
        Enum(
            AppointmentParticipantStatus,
            name="appointment_participant_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    appointment = relationship("AppointmentModel", back_populates="participants")

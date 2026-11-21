from sqlalchemy import BigInteger, Column, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import AppointmentResponseParticipantStatus

appointment_response_id_seq = Sequence(
    "appointment_response_pub_seq", start=370000, increment=1, metadata=Base.metadata
)

# The seven R4 targets of AppointmentResponse.actor.
ACTOR_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Device",
    "HealthcareService",
    "Location",
)


class AppointmentResponseModel(TenantAuditMixin, Base):
    """FHIR R4 AppointmentResponse — Medplum-style storage, same as
    Organization, Location, Practitioner, HealthcareService, Endpoint,
    PractitionerRole, Schedule, Slot, Patient and Appointment.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.appointment_response). Nothing else in this table or
    its child table is a second copy of the resource: every other column
    exists only because a FHIR R4 AppointmentResponse search parameter filters
    on it (https://www.hl7.org/fhir/R4/appointmentresponse.html#search), and
    is derived from `content` on every write by
    app.repository.appointment_response._indexer.

    Search parameter -> storage:
      part-status       -> participant_status (1..1 code, Enum column, stored
                           by value so `needs-action` is the real FHIR code)
      appointment       -> appointment_reference/_type/_id/_identifier_*
                           (1..1 Reference(Appointment))
      actor, patient, practitioner, location
                        -> actor_reference/_type/_id/_identifier_* (0..1
                           Reference to one of seven types; `patient`,
                           `practitioner` and `location` read the same
                           columns, narrowed by `actor_type`)
      identifier        -> AppointmentResponseIdentifier (0..*)
      _id               -> appointment_response_id;  _lastUpdated ->
                           updated_at/created_at

    `start`, `end`, `participantType`, `comment` and `extension` have no
    search parameter and live only in `content`.

    `actor` can point at seven resource types, so `actor_type` records which
    one a relative `Type/<id>` names (a plain string, not a Postgres enum): a
    search by bare id is ambiguous (`actor=Type/id` or `actor:Type=id`).

    All index columns are nullable: R4 makes `appointment` and
    `participantStatus` mandatory (and apr-1 requires `participantType` or
    `actor`), but those are the validator's rules (enforced by the
    `java_validator` backend), not the database's. No `user_id`: an
    AppointmentResponse is a shared tenant-level entity. No DB-level CHECK
    constraints."""

    __tablename__ = "appointment_response"
    __table_args__ = (
        Index("ix_appointment_response_actor_type_id", "actor_type", "actor_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    appointment_response_id = Column(
        BigInteger,
        appointment_response_id_seq,
        server_default=appointment_response_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    participant_status = Column(
        Enum(
            AppointmentResponseParticipantStatus,
            name="appointment_response_participant_status",
            # Store `needs-action`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # appointment (1..1 Reference(Appointment))
    appointment_reference = Column(String, nullable=True)
    appointment_type = Column(String, nullable=True)
    appointment_id = Column(BigInteger, nullable=True, index=True)
    appointment_identifier_system = Column(String, nullable=True)
    appointment_identifier_value = Column(String, nullable=True)

    # actor (0..1 Reference to one of ACTOR_TYPES)
    actor_reference = Column(String, nullable=True)
    actor_type = Column(String, nullable=True)
    actor_id = Column(BigInteger, nullable=True)
    actor_identifier_system = Column(String, nullable=True)
    actor_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "AppointmentResponseIdentifier",
        back_populates="appointment_response",
        cascade="all, delete-orphan",
    )

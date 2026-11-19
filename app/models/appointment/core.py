from sqlalchemy import BigInteger, Column, DateTime, Enum, Sequence
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import AppointmentStatus

appointment_id_seq = Sequence("appointment_pub_seq", start=40000, increment=1, metadata=Base.metadata)


class AppointmentModel(TenantAuditMixin, Base):
    """FHIR R4 Appointment — Medplum-style storage, same as Organization,
    Location, Practitioner, HealthcareService, Endpoint, PractitionerRole,
    Schedule, Slot and Patient.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.appointment). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Appointment search parameter filters on it
    (https://www.hl7.org/fhir/R4/appointment.html#search), and is derived from
    `content` on every write by app.repository.appointment._indexer.

    Search parameter -> storage:
      status            -> status (1..1 code, Enum column, stored by value)
      date              -> start (0..1 instant, column)
      identifier        -> AppointmentIdentifier (0..*)
      service-category, service-type, specialty, appointment-type,
      reason-code       -> AppointmentToken (one row per coding, `param` says
                           which search parameter it feeds)
      based-on, reason-reference, slot, supporting-info
                        -> AppointmentReference (one row per Reference, `param`
                           says which; `reference_type` is the target type)
      actor, patient, practitioner, location, part-status
                        -> AppointmentParticipant (one row per participant)
      _id               -> appointment_id;  _lastUpdated -> updated_at/created_at

    `end`, `minutesDuration`, `created`, `priority`, `description`, `comment`,
    `patientInstruction`, `cancelationReason`, `requestedPeriod`,
    `participant.type/required/period` and `extension` have no search parameter
    and live only in `content`.

    All index columns are nullable: R4 makes `status` and `participant`
    mandatory, but that is the validator's rule (enforced by the
    `java_validator` backend), not the database's. No `user_id`: an
    Appointment is a shared tenant-level entity. No DB-level CHECK
    constraints."""

    __tablename__ = "appointment"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    appointment_id = Column(
        BigInteger,
        appointment_id_seq,
        server_default=appointment_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    start = Column(DateTime(timezone=True), nullable=True, index=True)

    identifiers = relationship("AppointmentIdentifier", back_populates="appointment", cascade="all, delete-orphan")
    tokens = relationship("AppointmentToken", back_populates="appointment", cascade="all, delete-orphan")
    references = relationship("AppointmentReference", back_populates="appointment", cascade="all, delete-orphan")
    participants = relationship("AppointmentParticipant", back_populates="appointment", cascade="all, delete-orphan")

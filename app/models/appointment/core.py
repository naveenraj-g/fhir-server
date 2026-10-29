from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, Sequence, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.appointment.enums import AppointmentStatus
from app.models.shared import TenantAuditMixin

appointment_id_seq = Sequence(
    "appointment_pub_seq", start=40000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class AppointmentModel(TenantAuditMixin, Base):
    """FHIR R4 Appointment — https://www.hl7.org/fhir/R4/appointment.html

    A booking of a healthcare event among patient(s), practitioner(s),
    related person(s) and/or device(s) for a specific date/time.

    Modeled to the same conventions as Organization/Location/
    HealthcareService/PractitionerRole/Schedule/Slot: BigInteger internal PK
    + public sequence ID, TenantAuditMixin (tenant_id, not a hand-declared
    org_id), flattened references with an Identifier logical-reference
    fallback where the target may live outside this system (participant.actor,
    reasonReference, supportingInformation, slot, basedOn), and every
    CodeableConcept's coding[] as a real 0..* child/grandchild table rather
    than a single flattened coding (cancelationReason, serviceCategory,
    serviceType, specialty, appointmentType, reasonCode, participant.type —
    see identifier.py/service_category.py/service_type.py/specialty.py/
    reason_code.py/participant.py) — this applies even to cancelationReason
    and appointmentType themselves, both 0..1 CodeableConcept living
    directly on this row, because a CodeableConcept's own `coding[]` is
    always 0..* regardless of the containing field's cardinality (same
    reasoning as SlotModel.appointmentType's promotion).

    participant (1..* per spec) is modeled as 0..* at the DB layer, same as
    Schedule.actor — see app.models.schedule.actor.ScheduleActor's docstring;
    the minimum-one rule is enforced by the FHIR validator layer, not a DB
    constraint.

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like Organization/Location/
    HealthcareService/PractitionerRole/Schedule/Slot, an Appointment is a
    shared tenant-level entity (any participant — patient, practitioner, or
    other — may need to see it), not scoped to one end user's own account.
    """

    __tablename__ = "appointment"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    appointment_id = Column(
        BigInteger,
        appointment_id_seq,
        server_default=appointment_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── status (1..1 code) — required ─────────────────────────────────────────

    status = Column(Enum(AppointmentStatus, name="appointment_status"), nullable=False)

    # ── cancelationReason (0..1 CodeableConcept) — text flattened here, ──────
    # coding[] promoted to a dedicated child table (see
    # AppointmentCancelationReasonCoding in cancelation_reason.py)

    cancelation_reason_text = Column(String, nullable=True)

    # ── appointmentType (0..1 CodeableConcept) — text flattened here, ────────
    # coding[] promoted to a dedicated child table (appointment_type.py)

    appointment_type_text = Column(String, nullable=True)

    # ── priority (0..1 unsignedInt) ───────────────────────────────────────────

    priority = Column(Integer, nullable=True)

    # ── description (0..1 string) ─────────────────────────────────────────────

    description = Column(String, nullable=True)

    # ── start / end (0..1 instant each) ───────────────────────────────────────
    # Both independently 0..1 per spec — not a jointly-required pair the way
    # Location.position.longitude/.latitude are, so no CheckConstraint here.

    start = Column(DateTime(timezone=True), nullable=True)
    end = Column(DateTime(timezone=True), nullable=True)

    # ── minutesDuration (0..1 positiveInt) ────────────────────────────────────

    minutes_duration = Column(Integer, nullable=True)

    # ── created (0..1 dateTime) — date this appointment record was created ───
    # Distinct from TenantAuditMixin's created_at (infra audit timestamp,
    # always set); this is the FHIR business field, optional.

    created = Column(DateTime(timezone=True), nullable=True)

    # ── comment / patientInstruction (0..1 string each) ───────────────────────

    comment = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not Appointment-specific). Raw
    # [{url, valueType, value}, ...]; validated against registered
    # extension definitions by the (not-yet-built) profile pipeline, not by
    # the database. Same shape as OrganizationModel.extension.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/LocationModel/.../SlotModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "AppointmentIdentifier", back_populates="appointment", cascade="all, delete-orphan"
    )
    service_categories = relationship(
        "AppointmentServiceCategory", back_populates="appointment", cascade="all, delete-orphan"
    )
    service_types = relationship(
        "AppointmentServiceType", back_populates="appointment", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "AppointmentSpecialty", back_populates="appointment", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "AppointmentReasonCode", back_populates="appointment", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "AppointmentReasonReference", back_populates="appointment", cascade="all, delete-orphan"
    )
    supporting_informations = relationship(
        "AppointmentSupportingInformation",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )
    slots = relationship(
        "AppointmentSlot", back_populates="appointment", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "AppointmentBasedOn", back_populates="appointment", cascade="all, delete-orphan"
    )
    participants = relationship(
        "AppointmentParticipant", back_populates="appointment", cascade="all, delete-orphan"
    )
    requested_periods = relationship(
        "AppointmentRequestedPeriod", back_populates="appointment", cascade="all, delete-orphan"
    )
    cancelation_reason_codings = relationship(
        "AppointmentCancelationReasonCoding",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )
    appointment_type_codings = relationship(
        "AppointmentAppointmentTypeCoding",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Sequence, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, ScheduleReferenceType
from app.models.shared import TenantAuditMixin
from app.models.slot.enums import SlotStatus

slot_id_seq = Sequence(
    "slot_pub_seq", start=220000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class SlotModel(TenantAuditMixin, Base):
    """FHIR R4 Slot — https://www.hl7.org/fhir/R4/slot.html

    A slot of time on a schedule that may be available for booking
    appointments.

    Modeled to the same conventions as Organization/Location/
    HealthcareService/PractitionerRole/Schedule: BigInteger internal PK +
    public sequence ID, TenantAuditMixin (tenant_id, not a hand-declared
    org_id), flattened references (`{prefix}_type`/`_id`/`_display`,
    storing the target's PUBLIC sequence ID with no ForeignKey/relationship
    — see CLAUDE.md's FHIR DB Model Design section) with an Identifier
    logical-reference fallback where the target may live outside this
    system, and every CodeableConcept's coding[] as a real 0..* child/
    grandchild table rather than a single flattened coding (see
    identifier.py/service_category.py/service_type.py/specialty.py/
    appointment_type.py) — this applies even to `appointmentType` itself,
    a 0..1 CodeableConcept living directly on this row, because a
    CodeableConcept's own `coding[]` is always 0..* regardless of the
    containing field's cardinality (same reasoning as
    HealthcareServiceEligibility.code's promotion).

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like Organization/Location/
    HealthcareService/PractitionerRole/Schedule, a Slot is a shared
    tenant-level entity, not scoped to one end user's own account.
    """

    __tablename__ = "slot"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    slot_id = Column(
        BigInteger,
        slot_id_seq,
        server_default=slot_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── schedule (1..1 Reference(Schedule)) — required ───────────────────────
    # schedule_id stores Schedule's PUBLIC schedule_id — no FK, no
    # relationship (see PractitionerRoleModel.practitioner_* for the same
    # pattern). Shared PG enum type — create_type=False since the
    # migration owns creation and it's registered in app/models/enums.py
    # for reuse by any future resource referencing Schedule.

    schedule_type = Column(
        Enum(ScheduleReferenceType, name="schedule_reference_type", create_type=False),
        nullable=False,
    )
    schedule_id = Column(BigInteger, nullable=False, index=True)
    schedule_display = Column(String, nullable=True)

    # schedule.identifier (0..1 Identifier) — logical-reference fallback;
    # in practice always empty since Schedule is a modeled resource here,
    # but kept for the same reason every other resolved reference carries
    # one (FHIR's own Reference datatype always has it).
    schedule_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    schedule_identifier_type_system = Column(String, nullable=True)
    schedule_identifier_type_version = Column(String, nullable=True)
    schedule_identifier_type_code = Column(String, nullable=True)
    schedule_identifier_type_display = Column(String, nullable=True)
    schedule_identifier_type_text = Column(String, nullable=True)
    schedule_identifier_type_user_selected = Column(Boolean, nullable=True)
    schedule_identifier_system = Column(String, nullable=True)
    schedule_identifier_value = Column(String, nullable=True)
    schedule_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    schedule_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── status (1..1 code) — required ─────────────────────────────────────────

    status = Column(Enum(SlotStatus, name="slot_status"), nullable=False)

    # ── start / end (1..1 instant each) — required ────────────────────────────

    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)

    # ── appointmentType (0..1 CodeableConcept) — text flattened here, ────────
    # coding[] promoted to a dedicated child table (appointment_type.py)

    appointment_type_text = Column(String, nullable=True)

    # ── overbooked (0..1 boolean) ─────────────────────────────────────────────

    overbooked = Column(Boolean, nullable=True)

    # ── comment (0..1 string) ─────────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/LocationModel/HealthcareServiceModel/
    # PractitionerRoleModel/ScheduleModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "SlotIdentifier", back_populates="slot", cascade="all, delete-orphan"
    )
    service_categories = relationship(
        "SlotServiceCategory", back_populates="slot", cascade="all, delete-orphan"
    )
    service_types = relationship(
        "SlotServiceType", back_populates="slot", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "SlotSpecialty", back_populates="slot", cascade="all, delete-orphan"
    )
    appointment_type_codings = relationship(
        "SlotAppointmentTypeCoding",
        back_populates="slot",
        cascade="all, delete-orphan",
    )

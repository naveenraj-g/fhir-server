from sqlalchemy import BigInteger, Boolean, Column, DateTime, Sequence, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

schedule_id_seq = Sequence(
    "schedule_pub_seq", start=200000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class ScheduleModel(TenantAuditMixin, Base):
    """FHIR R4 Schedule — https://www.hl7.org/fhir/R4/schedule.html

    A container for slots of time that may be available for booking
    appointments.

    Modeled to the same conventions as Organization/Location/
    HealthcareService/PractitionerRole: BigInteger internal PK + public
    sequence ID, TenantAuditMixin (tenant_id, not a hand-declared org_id),
    flattened references (`{prefix}_type`/`_id`/`_display`, storing the
    target's PUBLIC sequence ID with no ForeignKey/relationship — see
    CLAUDE.md's FHIR DB Model Design section) with an Identifier
    logical-reference fallback where the target may live outside this
    system, and every CodeableConcept's coding[] as a real 0..* child/
    grandchild table rather than a single flattened coding (see
    identifier.py/service_category.py/service_type.py/specialty.py).

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like Organization/Location/
    HealthcareService/PractitionerRole, a Schedule is a shared
    tenant-level entity, not scoped to one end user's own account.
    """

    __tablename__ = "schedule"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    schedule_id = Column(
        BigInteger,
        schedule_id_seq,
        server_default=schedule_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── active (0..1 boolean) ─────────────────────────────────────────────────
    # Historically NOT NULL on this resource (predates the later nullable=True
    # convention adopted for Organization/Practitioner's own active column) —
    # kept as-is since this mirrors this resource's own pre-existing
    # documented behavior from before it was removed in the mass resource
    # cleanup (same precedent HealthcareServiceModel.active follows).

    active = Column(Boolean, nullable=False, default=False)

    # ── planningHorizon (0..1 Period) ─────────────────────────────────────────

    planning_horizon_start = Column(DateTime(timezone=True), nullable=True)
    planning_horizon_end = Column(DateTime(timezone=True), nullable=True)

    # ── comment (0..1 string) ─────────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/LocationModel/HealthcareServiceModel/PractitionerRoleModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "ScheduleIdentifier",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    service_categories = relationship(
        "ScheduleServiceCategory",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    service_types = relationship(
        "ScheduleServiceType",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    specialties = relationship(
        "ScheduleSpecialty",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    actors = relationship(
        "ScheduleActor",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )

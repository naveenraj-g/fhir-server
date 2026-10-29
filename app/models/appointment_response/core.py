from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.appointment_response.enums import (
    AppointmentResponseActorReferenceType,
    AppointmentResponseParticipantStatus,
)
from app.models.enums import AppointmentReferenceType, IdentifierUse
from app.models.shared import TenantAuditMixin

appointment_response_id_seq = Sequence(
    "appointment_response_pub_seq", start=370000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class AppointmentResponseModel(TenantAuditMixin, Base):
    """FHIR R4 AppointmentResponse —
    https://www.hl7.org/fhir/R4/appointmentresponse.html

    A reply to an appointment request for a patient and/or practitioner(s),
    such as a confirmation or rejection.

    Modeled to the same conventions as Organization/.../Appointment:
    BigInteger internal PK + public sequence ID, TenantAuditMixin
    (tenant_id, not a hand-declared org_id), flattened references with an
    Identifier logical-reference fallback (`appointment`, `actor`), and
    `participantType`'s coding[] as a real 0..* child/grandchild table
    rather than a single flattened coding (see participant_type.py) — same
    reasoning as every other CodeableConcept-list promotion in this
    codebase.

    `appointment` (1..1 Reference(Appointment)) is required and resolves
    against RESOURCE_REGISTRY — Appointment is a modeled resource here
    (registered specifically for this field, see
    app/core/reference_resolver.py), so its existence is actually enforced,
    unlike `actor`'s polymorphic targets (see
    AppointmentResponseActorReferenceType's docstring for which of those
    are modeled).

    apr-1 ("participantType.exists() or actor.exists()") is a cross-field/
    cross-table rule — enforced by the FHIR validator layer, not a DB
    constraint, same reasoning as every other R4 structural rule in this
    codebase (see OrganizationModel's docstring).

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like Organization/Location/.../
    Appointment, an AppointmentResponse is a shared tenant-level entity,
    not scoped to one end user's own account.
    """

    __tablename__ = "appointment_response"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    appointment_response_id = Column(
        BigInteger,
        appointment_response_id_seq,
        server_default=appointment_response_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── appointment (1..1 Reference(Appointment)) — required ─────────────────
    # appointment_reference is the raw literal string exactly as received —
    # see OrganizationModel.partof_reference for the full reasoning. Kept
    # nullable even though appointment_type/appointment_id are themselves
    # required (1..1) — an unresolvable absolute URL would otherwise have
    # nowhere to live, same as every other Reference field's `_reference`.
    appointment_reference = Column(String, nullable=True)
    appointment_type = Column(
        Enum(
            AppointmentReferenceType,
            name="appointment_reference_type",
            create_type=False,
        ),
        nullable=False,
    )
    appointment_id = Column(BigInteger, nullable=False, index=True)
    appointment_display = Column(String, nullable=True)

    # appointment.identifier (0..1 Identifier) — logical-reference fallback;
    # in practice always empty since Appointment is a modeled resource
    # here, but kept for the same reason every other resolved reference
    # carries one (FHIR's own Reference datatype always has it).
    appointment_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    appointment_identifier_type_system = Column(String, nullable=True)
    appointment_identifier_type_version = Column(String, nullable=True)
    appointment_identifier_type_code = Column(String, nullable=True)
    appointment_identifier_type_display = Column(String, nullable=True)
    appointment_identifier_type_text = Column(String, nullable=True)
    appointment_identifier_type_user_selected = Column(Boolean, nullable=True)
    appointment_identifier_system = Column(String, nullable=True)
    appointment_identifier_value = Column(String, nullable=True)
    appointment_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    appointment_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── start / end (0..1 instant each) ───────────────────────────────────────

    start = Column(DateTime(timezone=True), nullable=True)
    end = Column(DateTime(timezone=True), nullable=True)

    # ── actor (0..1 Reference, polymorphic) ───────────────────────────────────

    actor_reference = Column(String, nullable=True)
    actor_type = Column(
        Enum(
            AppointmentResponseActorReferenceType,
            name="appointment_response_actor_reference_type",
        ),
        nullable=True,
    )
    actor_id = Column(BigInteger, nullable=True, index=True)
    actor_display = Column(String, nullable=True)

    actor_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    actor_identifier_type_system = Column(String, nullable=True)
    actor_identifier_type_version = Column(String, nullable=True)
    actor_identifier_type_code = Column(String, nullable=True)
    actor_identifier_type_display = Column(String, nullable=True)
    actor_identifier_type_text = Column(String, nullable=True)
    actor_identifier_type_user_selected = Column(Boolean, nullable=True)
    actor_identifier_system = Column(String, nullable=True)
    actor_identifier_value = Column(String, nullable=True)
    actor_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    actor_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── participantStatus (1..1 code) — required ──────────────────────────────

    participant_status = Column(
        Enum(
            AppointmentResponseParticipantStatus,
            name="appointment_response_participant_status",
        ),
        nullable=False,
    )

    # ── comment (0..1 string) ─────────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not AppointmentResponse-specific). Raw
    # [{url, valueType, value}, ...]; validated against registered
    # extension definitions by the (not-yet-built) profile pipeline, not by
    # the database. Same shape as OrganizationModel.extension.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/LocationModel/.../AppointmentModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "AppointmentResponseIdentifier",
        back_populates="appointment_response",
        cascade="all, delete-orphan",
    )
    participant_types = relationship(
        "AppointmentResponseParticipantType",
        back_populates="appointment_response",
        cascade="all, delete-orphan",
    )

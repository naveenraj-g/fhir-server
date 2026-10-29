from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.appointment.enums import AppointmentSlotReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# slot (0..*) Reference(Slot) child table
# ---------------------------------------------------------------------------


class AppointmentSlot(TenantAuditMixin, Base):
    """slot[] — the slots from the participants' schedules that will be
    filled by the appointment.

    Unlike reasonReference/basedOn/supportingInformation, Slot IS a modeled
    resource in this system (registered in RESOURCE_REGISTRY — see
    app/core/reference_resolver.py), so this reference's existence check is
    actually enforced at write time, the same as every other resolvable
    flattened reference in this codebase.

    No UniqueConstraint on (appointment_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment
    that wants that as a rule expresses it as a profile-layer invariant,
    not a base constraint."""

    __tablename__ = "appointment_slot"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(AppointmentSlotReferenceType, name="appointment_slot_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # slot.identifier (0..1 Identifier) — logical-reference fallback; in
    # practice always empty since Slot is a modeled resource here, but kept
    # for the same reason every other resolved reference carries one.
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="slots")

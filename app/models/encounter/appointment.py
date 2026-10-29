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
from app.models.enums import AppointmentReferenceType, IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# appointment (0..*) Reference(Appointment) child table
# ---------------------------------------------------------------------------


class EncounterAppointment(TenantAuditMixin, Base):
    """appointment[] — the appointment that scheduled this encounter.

    Unlike episodeOfCare/basedOn/reasonReference/account, Appointment IS
    a modeled resource in this system (registered in RESOURCE_REGISTRY —
    see app/core/reference_resolver.py), so this reference's existence
    check is actually enforced, the same as every other resolvable
    flattened reference in this codebase.

    No UniqueConstraint on (encounter_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment
    that wants that as a rule expresses it as a profile-layer invariant,
    not a base constraint."""

    __tablename__ = "encounter_appointment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            AppointmentReferenceType,
            name="appointment_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

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

    encounter = relationship("EncounterModel", back_populates="appointments")

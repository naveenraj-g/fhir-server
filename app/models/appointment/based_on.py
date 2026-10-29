from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.appointment.enums import AppointmentBasedOnReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# basedOn (0..*) Reference(ServiceRequest) child table
# ---------------------------------------------------------------------------


class AppointmentBasedOn(TenantAuditMixin, Base):
    """basedOn[] — the service request this appointment is allocated to
    assess.

    ServiceRequest is not a modeled resource in this system, so
    reference_identifier_* columns are in practice the only way to record
    one — same situation as AppointmentReasonReference. The existence
    check is never attempted for this field."""

    __tablename__ = "appointment_based_on"
    __table_args__ = (
        UniqueConstraint(
            "appointment_pk",
            "reference_type",
            "reference_id",
            name="uq_appointment_based_on_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(AppointmentBasedOnReferenceType, name="appointment_based_on_reference_type"),
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

    appointment = relationship("AppointmentModel", back_populates="based_ons")

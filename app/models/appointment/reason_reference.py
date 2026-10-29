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
from app.models.appointment.enums import AppointmentReasonReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonReference (0..*) Reference(Condition|Procedure|Observation|
# ImmunizationRecommendation) child table
# ---------------------------------------------------------------------------


class AppointmentReasonReference(TenantAuditMixin, Base):
    """reasonReference[] — reason the appointment is to take place (as
    opposed to resource reasonCode).

    None of Condition/Procedure/Observation/ImmunizationRecommendation are
    modeled resources in this system, so reference_identifier_* columns are
    in practice the only way to record one — same situation and same shape
    as HealthcareServiceEndpoint / LocationEndpoint. The existence check is
    never attempted for this field — see
    app.repository.appointment._shared's docstring.

    No UniqueConstraint on (appointment_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment
    that wants that as a rule expresses it as a profile-layer invariant,
    not a base constraint."""

    __tablename__ = "appointment_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            AppointmentReasonReferenceType,
            name="appointment_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # reasonReference.identifier (0..1 Identifier) — logical-reference
    # fallback
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

    appointment = relationship("AppointmentModel", back_populates="reason_references")

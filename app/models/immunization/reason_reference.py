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
from app.models.enums import IdentifierUse
from app.models.immunization.enums import ImmunizationReasonReferenceType
from app.models.shared import TenantAuditMixin


class ImmunizationReasonReferenceModel(TenantAuditMixin, Base):
    """Immunization.reasonReference (0..* Reference(Condition|Observation|DiagnosticReport)) child table."""

    __tablename__ = "immunization_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ImmunizationReasonReferenceType,
            name="immunization_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference.identifier fallback (11 columns)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="reason_references")

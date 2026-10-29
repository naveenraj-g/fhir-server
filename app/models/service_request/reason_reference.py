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
from app.models.enums import IdentifierUse
from app.models.service_request.enums import ServiceRequestReasonReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonReference (0..*) Reference(Condition|Observation|DiagnosticReport|
# DocumentReference) child table
# ---------------------------------------------------------------------------


class ServiceRequestReasonReference(TenantAuditMixin, Base):
    """reasonReference[] — none of the four allowed types is a modeled
    resource in this system; the existence check is never attempted for
    this field."""

    __tablename__ = "service_request_reason_reference"
    __table_args__ = (
        UniqueConstraint(
            "service_request_pk", "reference_type", "reference_id",
            name="uq_service_request_reason_reference_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ServiceRequestReasonReferenceType, name="service_request_reason_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
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

    service_request = relationship("ServiceRequestModel", back_populates="reason_references")

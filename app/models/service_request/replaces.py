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
from app.models.enums import IdentifierUse, ServiceRequestReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# replaces (0..*) Reference(ServiceRequest) child table
# ---------------------------------------------------------------------------


class ServiceRequestReplaces(TenantAuditMixin, Base):
    """replaces[] — the request this ServiceRequest supersedes.
    ServiceRequest IS a modeled resource here (self-referential, same
    reasoning as Location.partOf/Encounter.partOf's own self-referential
    RESOURCE_REGISTRY entry), so this one's existence check is always
    enforced — see app.repository.service_request._shared."""

    __tablename__ = "service_request_replaces"
    __table_args__ = (
        UniqueConstraint(
            "service_request_pk", "reference_id",
            name="uq_service_request_replaces_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ServiceRequestReferenceType, name="service_request_reference_type", create_type=False),
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

    service_request = relationship("ServiceRequestModel", back_populates="replaces")

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
from app.models.service_request.enums import ServiceRequestBasedOnReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# basedOn (0..*) Reference(CarePlan|ServiceRequest|MedicationRequest) child table
# ---------------------------------------------------------------------------


class ServiceRequestBasedOn(TenantAuditMixin, Base):
    """basedOn[] — a plan/proposal/order fulfilled in whole or in part by
    this ServiceRequest. Of the three allowed types, only ServiceRequest
    is a modeled resource in this system — CarePlan/MedicationRequest
    rows always rely on the identifier fallback instead; the existence
    check is only ever attempted for the ServiceRequest subset (see
    app.repository.service_request._shared._MODELED_BASED_ON_TYPES).

    No UniqueConstraint on (service_request_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same reference twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint."""

    __tablename__ = "service_request_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ServiceRequestBasedOnReferenceType, name="service_request_based_on_reference_type"),
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

    service_request = relationship("ServiceRequestModel", back_populates="based_ons")

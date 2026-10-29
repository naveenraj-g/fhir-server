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
from app.models.enums import IdentifierUse, LocationReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# locationReference (0..*) Reference(Location) child table
# ---------------------------------------------------------------------------


class ServiceRequestLocationReference(TenantAuditMixin, Base):
    """locationReference[] — resolved Location(s) where the procedure
    should occur. Location IS a modeled resource, so this one's existence
    check is always enforced.

    No UniqueConstraint on (service_request_pk, reference_id): R4 doesn't
    forbid listing the same reference twice — a deployment that wants
    that as a rule expresses it as a profile-layer invariant, not a base
    constraint."""

    __tablename__ = "service_request_location_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(LocationReferenceType, name="location_reference_type", create_type=False),
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

    service_request = relationship("ServiceRequestModel", back_populates="location_references")

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
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.practitioner_role.enums import PractitionerRoleEndpointReferenceType

# ---------------------------------------------------------------------------
# endpoint (0..*) Reference(Endpoint) child table
# ---------------------------------------------------------------------------


class PractitionerRoleEndpoint(Base):
    """endpoint[] — technical endpoints providing access to services operated
    for this role. No Endpoint model exists in this system, so — like
    HealthcareServiceEndpoint — there is no existence check for this
    reference; the identifier fallback is often the only populated half.
    """

    __tablename__ = "practitioner_role_endpoint"
    __table_args__ = (
        UniqueConstraint(
            "practitioner_role_id",
            "reference_type",
            "reference_id",
            name="uq_practitioner_role_endpoint_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    reference_type = Column(
        Enum(
            PractitionerRoleEndpointReferenceType,
            name="practitioner_role_endpoint_reference_type",
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="endpoints"
    )

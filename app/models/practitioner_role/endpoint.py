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
from app.models.practitioner_role.enums import PractitionerRoleEndpointReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# endpoint (0..*) Reference(Endpoint) child table
# ---------------------------------------------------------------------------


class PractitionerRoleEndpoint(TenantAuditMixin, Base):
    """endpoint[] — technical endpoints providing access to services
    operated for this role.

    Endpoint is not a modeled resource in this system, so the
    reference_identifier_* columns are in practice the only way to record one
    — same situation and same shape as HealthcareServiceEndpoint.
    """

    __tablename__ = "practitioner_role_endpoint"
    __table_args__ = (
        UniqueConstraint(
            "practitioner_role_pk",
            "reference_type",
            "reference_id",
            name="uq_practitioner_role_endpoint_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            PractitionerRoleEndpointReferenceType,
            name="practitioner_role_endpoint_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # endpoint.identifier (0..1 Identifier) — logical-reference fallback
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

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="endpoints"
    )

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
from app.models.practitioner_role.enums import (
    PractitionerRoleHealthcareServiceReferenceType,
)
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# healthcareService (0..*) Reference(HealthcareService) child table
# ---------------------------------------------------------------------------


class PractitionerRoleHealthcareService(TenantAuditMixin, Base):
    """healthcareService[] — the list of healthcare services that this
    worker provides for this role's organization/location(s).

    reference_id stores HealthcareService's PUBLIC healthcare_service_id —
    no FK/relationship, same flattened-reference convention as
    PractitionerRoleModel.practitioner_* and HealthcareServiceLocation.
    """

    __tablename__ = "practitioner_role_healthcare_service"
    __table_args__ = (
        UniqueConstraint(
            "practitioner_role_pk",
            "reference_type",
            "reference_id",
            name="uq_practitioner_role_healthcare_service_reference",
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
            PractitionerRoleHealthcareServiceReferenceType,
            name="practitioner_role_healthcare_service_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # healthcareService.identifier (0..1 Identifier) — logical-reference
    # fallback for a healthcare service held in another system
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
        "PractitionerRoleModel", back_populates="healthcare_services"
    )

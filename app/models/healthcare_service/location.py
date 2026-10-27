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
from app.models.healthcare_service.enums import HealthcareServiceLocationReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# location (0..*) Reference(Location) child table
# ---------------------------------------------------------------------------


class HealthcareServiceLocation(TenantAuditMixin, Base):
    """location[] — Location(s) where this service may be provided.

    reference_id stores Location's PUBLIC location_id — no FK/relationship,
    same flattened-reference convention as HealthcareServiceModel.provided_by_*
    and PatientGeneralPractitioner.
    """

    __tablename__ = "healthcare_service_location"
    __table_args__ = (
        UniqueConstraint(
            "healthcare_service_pk",
            "reference_type",
            "reference_id",
            name="uq_healthcare_service_location_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named healthcare_service_pk, not healthcare_service_id,
    # so it can never be confused with the public sequence ID.
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            HealthcareServiceLocationReferenceType,
            name="healthcare_service_location_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # location.identifier (0..1 Identifier) — logical-reference fallback for a
    # location held in another system
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

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="locations"
    )

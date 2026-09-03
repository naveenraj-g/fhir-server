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
from app.models.healthcare_service.enums import HealthcareServiceLocationReferenceType

# ---------------------------------------------------------------------------
# location (0..*) Reference(Location) child table
# ---------------------------------------------------------------------------


class HealthcareServiceLocation(Base):
    """location[] — Location(s) where this service may be provided.

    reference_id stores Location's PUBLIC location_id — no FK/relationship,
    same flattened-reference convention as HealthcareServiceModel.provided_by_*
    and PatientGeneralPractitioner.
    """

    __tablename__ = "healthcare_service_location"
    __table_args__ = (
        UniqueConstraint(
            "healthcare_service_id",
            "reference_type",
            "reference_id",
            name="uq_healthcare_service_location_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_id = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    healthcare_service = relationship("HealthcareServiceModel", back_populates="locations")

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
from app.models.location.enums import LocationEndpointReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# endpoint (0..*) Reference(Endpoint) child table
# ---------------------------------------------------------------------------


class LocationEndpoint(TenantAuditMixin, Base):
    """Location.endpoint[] — technical endpoints providing access to services
    operated for the location.

    Endpoint is not a modeled resource in this system, so the
    reference_identifier_* columns are in practice the only way to record one
    — same situation and same shape as OrganizationEndpoint.
    """

    __tablename__ = "location_endpoint"
    __table_args__ = (
        UniqueConstraint(
            "location_pk",
            "reference_type",
            "reference_id",
            name="uq_location_endpoint_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    reference_type = Column(
        Enum(LocationEndpointReferenceType, name="location_endpoint_reference_type"),
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

    # Audit columns come from TenantAuditMixin above.

    location = relationship("LocationModel", back_populates="endpoints")

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# type (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class LocationType(TenantAuditMixin, Base):
    """Location.type (0..* CodeableConcept). `text` stays flattened here
    (sibling of `coding[]`, not part of it); `coding[]` itself is a real
    0..* child table (LocationTypeCoding, below) rather than a single
    flattened coding — same org-custom-code-plus-standard-crosswalk
    reasoning as OrganizationType's own coding[] promotion (see
    app.models.organization.type).
    """

    __tablename__ = "location_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="types")
    codings = relationship(
        "LocationTypeCoding",
        back_populates="type",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class LocationTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Location.type.coding (0..*)."""

    __tablename__ = "location_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_type_id = Column(
        BigInteger, ForeignKey("location_type.id"), nullable=False, index=True
    )

    type = relationship("LocationType", back_populates="codings")

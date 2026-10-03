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


class OrganizationType(TenantAuditMixin, Base):
    """Organization.type (0..* CodeableConcept). `text` stays flattened here
    (it's a sibling field of `coding[]`, not part of it); `coding[]` itself
    is a real 0..* child table (OrganizationTypeCoding) rather than a single
    flattened coding — an organization may need its own custom code for this
    AND a crosswalk to a standard terminology (e.g. SNOMED CT) at the same
    time, which is exactly the multi-vocabulary case CodeableConcept.coding
    being 0..* exists for. See organization-reference-design.md and
    docs/architecture/fhir-profiling-and-extensibility-strategy.md for the
    org-defined-coding motivation.
    """

    __tablename__ = "organization_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="types")
    codings = relationship(
        "OrganizationTypeCoding",
        back_populates="type",
        cascade="all, delete-orphan",
    )


class OrganizationTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Organization.type.coding (0..*)."""

    __tablename__ = "organization_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_type_id = Column(
        BigInteger, ForeignKey("organization_type.id"), nullable=False, index=True
    )

    type = relationship("OrganizationType", back_populates="codings")

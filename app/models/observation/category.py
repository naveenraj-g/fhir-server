from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# category (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ObservationCategory(TenantAuditMixin, Base):
    """One entry of Observation.category (0..* CodeableConcept)."""

    __tablename__ = "observation_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="categories")
    codings = relationship("ObservationCategoryCoding", back_populates="category", cascade="all, delete-orphan")


class ObservationCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.category.coding (0..*)."""

    __tablename__ = "observation_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_category_id = Column(
        BigInteger, ForeignKey("observation_category.id"), nullable=False, index=True
    )

    category = relationship("ObservationCategory", back_populates="codings")

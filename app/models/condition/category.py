from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionCategory(TenantAuditMixin, Base):
    """One entry of Condition.category (0..* CodeableConcept)."""

    __tablename__ = "condition_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="categories")
    codings = relationship(
        "ConditionCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class ConditionCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.category.coding (0..*)."""

    __tablename__ = "condition_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_category_id = Column(
        BigInteger, ForeignKey("condition_category.id"), nullable=False, index=True
    )

    category = relationship("ConditionCategory", back_populates="codings")

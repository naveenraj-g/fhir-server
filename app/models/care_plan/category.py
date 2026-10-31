from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CarePlanCategory(TenantAuditMixin, Base):
    """CarePlan.category (0..*) child table."""

    __tablename__ = "care_plan_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="categories")
    codings = relationship(
        "CarePlanCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CarePlanCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CarePlan.category.coding (0..*) grandchild table."""

    __tablename__ = "care_plan_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(
        BigInteger,
        ForeignKey("care_plan_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("CarePlanCategory", back_populates="codings")

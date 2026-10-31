from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class GoalCategory(TenantAuditMixin, Base):
    """Goal.category (0..*) CodeableConcept child table."""

    __tablename__ = "goal_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="categories")
    codings = relationship(
        "GoalCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class GoalCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.category.coding (0..*) grandchild table."""

    __tablename__ = "goal_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_category_id = Column(
        BigInteger,
        ForeignKey("goal_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("GoalCategory", back_populates="codings")

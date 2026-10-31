from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionGoal(TenantAuditMixin, Base):
    """PlanDefinition.goal (0..* BackboneElement) child table."""

    __tablename__ = "plan_definition_goal"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    goal_id = Column(String, nullable=True)  # Element.id for internal cross-references
    category_text = Column(String, nullable=True)
    description_text = Column(String, nullable=True)
    priority_text = Column(String, nullable=True)
    start_text = Column(String, nullable=True)

    addresses = Column(JSONB, nullable=True)  # 0..* CodeableConcept
    documentation = Column(JSONB, nullable=True)  # 0..* RelatedArtifact
    target = Column(JSONB, nullable=True)  # 0..* PlanDefinition.goal.target

    plan_definition = relationship("PlanDefinitionModel", back_populates="goals")

    category_codings = relationship(
        "PlanDefinitionGoalCategoryCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    description_codings = relationship(
        "PlanDefinitionGoalDescriptionCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    priority_codings = relationship(
        "PlanDefinitionGoalPriorityCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    start_codings = relationship(
        "PlanDefinitionGoalStartCoding",
        back_populates="goal",
        cascade="all, delete-orphan",
    )


class PlanDefinitionGoalCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.goal.category.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_goal_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_id = Column(
        BigInteger,
        ForeignKey("plan_definition_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal = relationship("PlanDefinitionGoal", back_populates="category_codings")


class PlanDefinitionGoalDescriptionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.goal.description.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_goal_description_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_id = Column(
        BigInteger,
        ForeignKey("plan_definition_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal = relationship("PlanDefinitionGoal", back_populates="description_codings")


class PlanDefinitionGoalPriorityCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.goal.priority.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_goal_priority_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_id = Column(
        BigInteger,
        ForeignKey("plan_definition_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal = relationship("PlanDefinitionGoal", back_populates="priority_codings")


class PlanDefinitionGoalStartCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.goal.start.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_goal_start_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_id = Column(
        BigInteger,
        ForeignKey("plan_definition_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal = relationship("PlanDefinitionGoal", back_populates="start_codings")

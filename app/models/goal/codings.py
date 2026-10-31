from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class GoalAchievementStatusCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.achievementStatus.coding (0..*) child table."""

    __tablename__ = "goal_achievement_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    goal = relationship("GoalModel", back_populates="achievement_status_codings")


class GoalPriorityCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.priority.coding (0..*) child table."""

    __tablename__ = "goal_priority_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    goal = relationship("GoalModel", back_populates="priority_codings")


class GoalDescriptionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.description.coding (0..*) child table."""

    __tablename__ = "goal_description_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    goal = relationship("GoalModel", back_populates="description_codings")


class GoalStartCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.startCodeableConcept.coding (0..*) child table."""

    __tablename__ = "goal_start_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    goal = relationship("GoalModel", back_populates="start_codings")


class GoalOutcomeCode(TenantAuditMixin, Base):
    """Goal.outcomeCode (0..*) CodeableConcept child table."""

    __tablename__ = "goal_outcome_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="outcome_codes")
    codings = relationship(
        "GoalOutcomeCodeCoding",
        back_populates="outcome_code",
        cascade="all, delete-orphan",
    )


class GoalOutcomeCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Goal.outcomeCode.coding (0..*) grandchild table."""

    __tablename__ = "goal_outcome_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_outcome_code_id = Column(
        BigInteger,
        ForeignKey("goal_outcome_code.id"),
        nullable=False,
        index=True,
    )

    outcome_code = relationship("GoalOutcomeCode", back_populates="codings")

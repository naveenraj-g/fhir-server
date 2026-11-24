from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class GoalTarget(Base):
    """Search index for `target-date` (`(Goal.target.due as date)`): one row per target that has a
    `dueDate`, holding the half-open range the date covers (a `dueDuration` is not a date, so it
    is not indexed). Derived from GoalModel.content - never read to build a response."""

    __tablename__ = "goal_target"
    __table_args__ = (Index("ix_goal_target_due", "due_start", "due_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(BigInteger, ForeignKey("goal.id"), nullable=False, index=True)
    due_start = Column(DateTime(timezone=True), nullable=True)
    due_end = Column(DateTime(timezone=True), nullable=True)

    goal = relationship("GoalModel", back_populates="targets")

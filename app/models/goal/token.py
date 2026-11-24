from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in GoalToken, and the Goal element each reads.
TOKEN_PARAMS = {
    "achievement-status": "achievementStatus",
    "category": "category",
}


class GoalToken(Base):
    """Search index for the two CodeableConcept token parameters (`achievement-status`,
    `category`): one row per coding of each concept - a token search matches any coding of any
    entry - plus one code-less row for a concept with only `text`, so `:text` still finds it.
    `param` says which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    GoalModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "goal_token"
    __table_args__ = (Index("ix_goal_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(BigInteger, ForeignKey("goal.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="tokens")

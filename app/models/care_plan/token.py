from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in CarePlanToken, and the element each reads.
TOKEN_PARAMS = {
    "category": "category",
    "activity-code": "activity.detail.code",
}


class CarePlanToken(Base):
    """Search index for the two CodeableConcept token parameters of CarePlan - `category`
    (CarePlan.category) and `activity-code` (activity.detail.code of *every* activity): one row
    per coding of each concept - a token search matches any coding - plus one code-less row for a
    concept with only `text`, so `:text` still finds it. `param` says which search parameter the
    row belongs to (see TOKEN_PARAMS). Derived from CarePlanModel.content - never read to build a
    response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of two identical ones."""

    __tablename__ = "care_plan_token"
    __table_args__ = (Index("ix_care_plan_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="tokens")

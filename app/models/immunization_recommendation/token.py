from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ImmunizationRecommendationToken, and the element each
# reads (all three live inside the 1..* `recommendation` backbone).
TOKEN_PARAMS = {
    "status": "recommendation.forecastStatus",
    "target-disease": "recommendation.targetDisease",
    "vaccine-type": "recommendation.vaccineCode",
}


class ImmunizationRecommendationToken(Base):
    """Search index for the three CodeableConcept token parameters (`status`,
    `target-disease`, `vaccine-type`): one row per coding of each concept — a token
    search matches any coding of any recommendation entry — plus one code-less row
    for a concept with only `text`, so `:text` still finds it. `param` says which
    search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    ImmunizationRecommendationModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "immunization_recommendation_token"
    __table_args__ = (Index("ix_immunization_recommendation_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_recommendation_pk = Column(
        BigInteger, ForeignKey("immunization_recommendation.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    immunization_recommendation = relationship("ImmunizationRecommendationModel", back_populates="tokens")

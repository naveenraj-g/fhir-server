from sqlalchemy import BigInteger, Column, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class RiskAssessmentPrediction(Base):
    """Search index for `probability` (RiskAssessment.prediction.probability[x], 0..1 per
    prediction, a decimal or a Range): one row per prediction that has a probability, holding
    its lower and upper bound. A decimal is a point (low == high); a Range has the two bounds,
    either of which may be absent (NULL = open on that side). A `number` search matches the
    range per R4's prefix table (see app.fhir.search.quantity.number_range_match). Derived
    from RiskAssessmentModel.content — never read to build a response.

    `outcome`, `qualitativeRisk` (see RiskAssessmentToken), `relativeRisk`, `when[x]` and
    `rationale` are not stored here."""

    __tablename__ = "risk_assessment_prediction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_pk = Column(BigInteger, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    probability_low = Column(Numeric, nullable=True)
    probability_high = Column(Numeric, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="predictions")

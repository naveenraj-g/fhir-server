from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class QuestionnaireDefinition(Base):
    """Search index for the `definition` uri parameter: one row per `item.definition` of every
    item at every depth of the item tree. Derived from QuestionnaireModel.content - never read to
    build a response.

      definition             -> uri (exact, case-sensitive)
      definition:below/above -> uri (prefix comparisons)"""

    __tablename__ = "questionnaire_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="definitions")

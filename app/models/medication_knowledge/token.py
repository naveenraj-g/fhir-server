from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in MedicationKnowledgeToken, and the MedicationKnowledge element each
# reads. The last two are token searches over a plain string (the string is the `code`, there
# is no system).
TOKEN_PARAMS = {
    "code": "code",
    "doseform": "doseForm",
    "ingredient-code": "ingredient.itemCodeableConcept",
    "classification": "medicineClassification.classification",
    "classification-type": "medicineClassification.type",
    "monograph-type": "monograph.type",
    "monitoring-program-type": "monitoringProgram.type",
    "monitoring-program-name": "monitoringProgram.name",
    "source-cost": "cost.source",
}


class MedicationKnowledgeToken(Base):
    """Search index for the nine token parameters (see TOKEN_PARAMS): one row per coding of
    each CodeableConcept - a token search matches any coding of any entry - plus one
    code-less row for a concept with only `text`, so `:text` still finds it; for the two
    string-valued parameters one row holding the string as `code`. `param` says which
    search parameter the row belongs to. Derived from MedicationKnowledgeModel.content -
    never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of nine identical ones."""

    __tablename__ = "medication_knowledge_token"
    __table_args__ = (
        Index("ix_medication_knowledge_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger, ForeignKey("medication_knowledge.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="tokens"
    )

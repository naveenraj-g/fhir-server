from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in QuestionnaireToken, and the Questionnaire element each reads.
TOKEN_PARAMS = {
    "jurisdiction": "jurisdiction",
    "code": "item.code",
    "context-type": "useContext.code",
    "context": "useContext.value as CodeableConcept",
}


class QuestionnaireToken(Base):
    """Search index for the four token parameters held in one shared table, told apart by
    `param` (see TOKEN_PARAMS). Derived from QuestionnaireModel.content - never read to build a
    response.

      <param>            -> system, code
      <param>:text       -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below  -> system, code, resolved through the terminology service

    `slot` is which `useContext` an entry came from (0 for the other parameters, n for the n-th
    useContext): `context-type` (the useContext's code) and `context` (its value) must come from
    the *same* useContext for the `context-type-value` composite to match, exactly as
    Observation's composites pair a component's code with its value.

    `code` reads every `item.code` Coding at any depth of the item tree."""

    __tablename__ = "questionnaire_token"
    __table_args__ = (Index("ix_questionnaire_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    slot = Column(Integer, nullable=False, default=0, server_default="0")
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="tokens")

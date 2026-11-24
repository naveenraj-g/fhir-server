from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ActivityDefinitionToken, and the ActivityDefinition element each reads.
TOKEN_PARAMS = {
    "jurisdiction": "jurisdiction",
    "topic": "topic",
    "context-type": "useContext.code",
    "context": "useContext.value as CodeableConcept",
}


class ActivityDefinitionToken(Base):
    """Search index for the four token parameters held in one shared table, told apart by
    `param` (see TOKEN_PARAMS). Derived from ActivityDefinitionModel.content - never read to build a
    response.

      <param>            -> system, code
      <param>:text       -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below  -> system, code, resolved through the terminology service

    `slot` is which `useContext` an entry came from (0 for the other parameters, n for the n-th
    useContext): `context-type` (the useContext's code) and `context` (its value) must come from
    the *same* useContext for the `context-type-value` composite to match, exactly as
    Observation's composites pair a component's code with its value."""

    __tablename__ = "activity_definition_token"
    __table_args__ = (
        Index("ix_activity_definition_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    slot = Column(Integer, nullable=False, default=0, server_default="0")
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    activity_definition = relationship(
        "ActivityDefinitionModel", back_populates="tokens"
    )

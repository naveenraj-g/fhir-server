from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in SpecimenDefinitionToken, and the SpecimenDefinition element each reads.
TOKEN_PARAMS = {
    "type": "typeCollected",
    "container": "typeTested.container.type",
}


class SpecimenDefinitionToken(Base):
    """Search index for the two CodeableConcept token parameters (`type`, `container`): one row
    per coding of each concept - a token search matches any coding of any entry - plus one
    code-less row for a concept with only `text`, so `:text` still finds it. `param` says which
    search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    SpecimenDefinitionModel.content - never read to build a response.

    `container` reads `container.type` of **every** `typeTested` entry.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "specimen_definition_token"
    __table_args__ = (
        Index("ix_specimen_definition_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="tokens"
    )

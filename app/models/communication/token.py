from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in CommunicationToken, and the Communication element each reads.
TOKEN_PARAMS = {"category": "category", "medium": "medium"}


class CommunicationToken(Base):
    """Search index for the two CodeableConcept token parameters (`category`, `medium`): one row
    per coding of each concept - a token search matches any coding of any entry - plus one
    code-less row for a concept with only `text`, so `:text` still finds it. `param` says which
    search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    CommunicationModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "communication_token"
    __table_args__ = (Index("ix_communication_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger, ForeignKey("communication.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    communication = relationship("CommunicationModel", back_populates="tokens")

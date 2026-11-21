from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in FamilyMemberHistoryToken, and the element each reads
# (`code` reads condition.code of every condition).
TOKEN_PARAMS = {
    "code": "condition.code",
    "relationship": "relationship",
    "sex": "sex",
}


class FamilyMemberHistoryToken(Base):
    """Search index for the three CodeableConcept token parameters (`code`, `relationship`,
    `sex`): one row per coding of each concept — a token search matches any coding — plus
    one code-less row for a concept with only `text`, so `:text` still finds it. `param`
    says which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    FamilyMemberHistoryModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "family_member_history_token"
    __table_args__ = (
        Index("ix_family_member_history_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="tokens"
    )

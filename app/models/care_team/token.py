from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameter held in CareTeamToken, and the element it reads.
TOKEN_PARAMS = {
    "category": "category",
}


class CareTeamToken(Base):
    """Search index for the CodeableConcept token parameter `category` (CareTeam.category,
    0..*): one row per coding of each category - a token search matches any coding - plus one
    code-less row for a concept with only `text`, so `:text` still finds it. `param` says
    which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    CareTeamModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    A shared `param`-keyed table like the other resources', so a further token parameter
    needs no new table."""

    __tablename__ = "care_team_token"
    __table_args__ = (Index("ix_care_team_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="tokens")

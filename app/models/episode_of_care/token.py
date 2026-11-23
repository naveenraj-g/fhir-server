from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameter held in EpisodeOfCareToken, and the element it reads.
TOKEN_PARAMS = {
    "type": "type",
}


class EpisodeOfCareToken(Base):
    """Search index for the CodeableConcept token parameter `type` (EpisodeOfCare.type, 0..*):
    one row per coding of each type - a token search matches any coding - plus one code-less row
    for a concept with only `text`, so `:text` still finds it. `param` says which search
    parameter the row belongs to (see TOKEN_PARAMS). Derived from EpisodeOfCareModel.content -
    never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "episode_of_care_token"
    __table_args__ = (Index("ix_episode_of_care_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="tokens")

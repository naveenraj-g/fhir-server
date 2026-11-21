from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in EncounterToken. `participant-type` reads
# Encounter.participant.type, `special-arrangement` reads
# Encounter.hospitalization.specialArrangement; the other two read the
# top-level element of the same name (`reason-code` -> reasonCode).
TOKEN_PARAMS = ("participant-type", "reason-code", "special-arrangement", "type")


class EncounterToken(Base):
    """Search index for the four CodeableConcept token parameters
    (`participant-type`, `reason-code`, `special-arrangement`, `type`): one row
    per coding of each concept — a token search matches any coding of any
    entry — plus one code-less row for a concept with only `text`, so `:text`
    still finds it. `param` says which search parameter the row belongs to.
    Derived from EncounterModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of four identical ones."""

    __tablename__ = "encounter_token"
    __table_args__ = (Index("ix_encounter_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="tokens")

from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ObservationToken, and the element each reads. `slot` 0 is the
# Observation itself; slot n >= 1 is its n-th component.
TOKEN_PARAMS = {
    "category": "category",
    "code": "code",
    "method": "method",
    "data-absent-reason": "dataAbsentReason",
    "value-concept": "value[x] as CodeableConcept",
    "component-code": "component.code",
    "component-data-absent-reason": "component.dataAbsentReason",
    "component-value-concept": "component.value[x] as CodeableConcept",
}


class ObservationToken(Base):
    """Search index for every CodeableConcept token parameter of Observation: one row per coding
    of each concept — a token search matches any coding — plus one code-less row for a concept
    with only `text`, so `:text` still finds it. `param` says which search parameter the row
    belongs to (see TOKEN_PARAMS) and `slot` which element of the resource it came from: 0 for
    the Observation itself, n for its n-th component. The slot is what lets a *composite*
    search (`code-value-concept`, `component-code-value-concept`, ...) require the code and the
    value to belong to the same element. Derived from ObservationModel.content — never read to
    build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    `combo-*` searches are the union of an Observation-level and a component-level parameter
    (`combo-code` = `code` + `component-code`), so they read this table with `param IN (...)`."""

    __tablename__ = "observation_token"
    __table_args__ = (Index("ix_observation_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(
        BigInteger, ForeignKey("observation.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    slot = Column(Integer, nullable=False, default=0)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="tokens")

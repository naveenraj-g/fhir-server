from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in GroupToken, and the Group element each reads. `slot` 0 is the Group
# itself (`code`); slot n >= 1 is its n-th characteristic (`characteristic`, `value`, `exclude`).
TOKEN_PARAMS = {
    "code": "code",
    "characteristic": "characteristic.code",
    "value": "characteristic.value[CodeableConcept | boolean]",
    "exclude": "characteristic.exclude",
}


class GroupToken(Base):
    """Search index for the four token parameters `code`, `characteristic`, `value` and
    `exclude`: one row per coding of each CodeableConcept - a token search matches any coding
    of any entry - plus one code-less row for a concept with only `text`, so `:text` still
    finds it. A boolean (`value` of a valueBoolean, `exclude`) is one row with code `true` /
    `false`. `param` says which search parameter the row belongs to (see TOKEN_PARAMS) and
    `slot` which element it came from: 0 for the Group itself, n for its n-th characteristic.
    The slot is what lets the `characteristic-value` *composite* require a characteristic code
    and a value of the *same* characteristic. Derived from GroupModel.content - never read to
    build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "group_token"
    __table_args__ = (Index("ix_group_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(BigInteger, ForeignKey("group.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    slot = Column(Integer, nullable=False, default=0)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    group = relationship("GroupModel", back_populates="tokens")

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in SpecimenToken, and the element each reads.
TOKEN_PARAMS = {
    "type": "type",
    "bodysite": "collection.bodySite",
    "container": "container.type",
}


class SpecimenToken(Base):
    """Search index for the three CodeableConcept token parameters of Specimen — `type`,
    `bodysite` (collection.bodySite) and `container` (container.type of *every* container): one
    row per coding of each concept — a token search matches any coding — plus one code-less row
    for a concept with only `text`, so `:text` still finds it. `param` says which search
    parameter the row belongs to (see TOKEN_PARAMS). Derived from SpecimenModel.content — never
    read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "specimen_token"
    __table_args__ = (Index("ix_specimen_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="tokens")

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class PractitionerCommunication(Base):
    """Search index for the `communication` token parameter: one row per
    Practitioner.communication[].coding[] (a token search matches any coding
    of any entry) — plus one code-less row for an entry that has only
    `text`, so `communication:text` still finds it. Derived from
    PractitionerModel.content — never read to build a response.

      communication            -> system, code
      communication:text       -> text_norm (CodeableConcept.text) / display_norm
      communication:in/:below  -> system, code, via the terminology service"""

    __tablename__ = "practitioner_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="communications")

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class RelatedPersonRelationship(Base):
    """Search index for `relationship` (RelatedPerson.relationship, 0..*): one
    row per coding of each CodeableConcept — a token search matches any coding
    of any entry — plus one code-less row for a concept with only `text`, so
    `:text` still finds it. Derived from RelatedPersonModel.content — never
    read to build a response.

      relationship              -> system, code
      relationship:text         -> text_norm (CodeableConcept.text) / display_norm
      relationship:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "related_person_relationship"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_pk = Column(BigInteger, ForeignKey("related_person.id"), nullable=False, index=True)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    related_person = relationship("RelatedPersonModel", back_populates="relationships")

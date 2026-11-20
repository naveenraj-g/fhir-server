from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class RelatedPersonName(Base):
    """Search index for `name` and `phonetic` (0..*): one
    row per RelatedPerson.name, holding only what those parameters match on.
    Derived from RelatedPersonModel.content — never read to build a response.

      name      -> any of text, family, given, prefix, suffix (R4: "any of
                   the string fields in the HumanName")
      phonetic  -> phonetic: Soundex of every family and given word,
                   space-padded (" G564 H213 ") so a code matches as a whole token

    Every string is stored as written (for `:exact`) and normalized
    (`*_norm`: accents stripped, case-folded — for the default starts-with
    and `:contains`)."""

    __tablename__ = "related_person_name"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_pk = Column(
        BigInteger, ForeignKey("related_person.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)
    family = Column(String, nullable=True)
    family_norm = Column(String, nullable=True, index=True)
    given = Column(ARRAY(String), nullable=True)
    given_norm = Column(ARRAY(String), nullable=True)
    prefix = Column(ARRAY(String), nullable=True)
    prefix_norm = Column(ARRAY(String), nullable=True)
    suffix = Column(ARRAY(String), nullable=True)
    suffix_norm = Column(ARRAY(String), nullable=True)
    phonetic = Column(String, nullable=True)

    related_person = relationship("RelatedPersonModel", back_populates="names")

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in AllergyIntoleranceToken. The five CodeableConcept
# ones read: `clinical-status` -> clinicalStatus, `verification-status` ->
# verificationStatus, `code` -> code and reaction.substance, `manifestation`
# -> reaction.manifestation, `route` -> reaction.exposureRoute. The two `code`
# ones read: `category` -> category (0..*) and `severity` ->
# reaction.severity; their rows carry the code's FHIR system and no text.
TOKEN_PARAMS = (
    "category",
    "clinical-status",
    "code",
    "manifestation",
    "route",
    "severity",
    "verification-status",
)

# The code system of each `code`-typed element (R4 value sets).
CODE_SYSTEMS = {
    "category": "http://hl7.org/fhir/allergy-intolerance-category",
    "severity": "http://hl7.org/fhir/reaction-event-severity",
}
TYPE_SYSTEM = "http://hl7.org/fhir/allergy-intolerance-type"
CRITICALITY_SYSTEM = "http://hl7.org/fhir/allergy-intolerance-criticality"


class AllergyIntoleranceToken(Base):
    """Search index for the seven token parameters held in one shared table
    (`category`, `clinical-status`, `code`, `manifestation`, `route`,
    `severity`, `verification-status`): one row per coding of each concept — a
    token search matches any coding of any entry — plus one code-less row for a
    concept with only `text`, so `:text` still finds it. `param` says which
    search parameter the row belongs to. Derived from
    AllergyIntoleranceModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    `category` and `severity` are plain `code` elements, so their rows hold the
    code and its fixed FHIR system and nothing else."""

    __tablename__ = "allergy_intolerance_token"
    __table_args__ = (
        Index("ix_allergy_intolerance_token_param_code", "param", "code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger, ForeignKey("allergy_intolerance.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel", back_populates="tokens"
    )

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class PatientCommunication(Base):
    """Search index for the `language` token parameter: one row per
    Patient.communication[].language.coding[] (a token search matches any
    coding of any entry; `preferred` has no search parameter) — plus one
    code-less row for a language that has only `text`, so `language:text`
    still finds it. Derived from PatientModel.content — never read to build a
    response.

      language            -> system, code
      language:text       -> text_norm (CodeableConcept.text) / display_norm
      language:in/:below  -> system, code, via the terminology service"""

    __tablename__ = "patient_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="communications")

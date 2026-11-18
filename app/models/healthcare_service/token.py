from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a HealthcareServiceToken row feeds, and the
# HealthcareService element it is read from.
TOKEN_PARAMS = {
    "service-category": "category",
    "service-type": "type",
    "specialty": "specialty",
    "program": "program",
    "characteristic": "characteristic",
}


class HealthcareServiceToken(Base):
    """Search index for the five CodeableConcept token parameters
    (`service-category`, `service-type`, `specialty`, `program`,
    `characteristic`), all 0..*: one row per coding of each concept — a token
    search matches any coding of any entry — plus one code-less row for a
    concept that has only `text`, so `:text` still finds it. `param` says
    which search parameter the row belongs to (see TOKEN_PARAMS). Derived
    from HealthcareServiceModel.content — never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of five identical ones: the parameters have the
    same shape and are never read together."""

    __tablename__ = "healthcare_service_token"
    __table_args__ = (Index("ix_healthcare_service_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    healthcare_service = relationship("HealthcareServiceModel", back_populates="tokens")

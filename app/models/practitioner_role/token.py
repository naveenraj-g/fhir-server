from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a PractitionerRoleToken row feeds, and the
# PractitionerRole element it is read from.
TOKEN_PARAMS = {
    "role": "code",
    "specialty": "specialty",
}


class PractitionerRoleToken(Base):
    """Search index for the two CodeableConcept token parameters `role`
    (PractitionerRole.code) and `specialty`, both 0..*: one row per coding of
    each concept — a token search matches any coding of any entry — plus one
    code-less row for a concept that has only `text`, so `:text` still finds
    it. `param` says which search parameter the row belongs to (see
    TOKEN_PARAMS). Derived from PractitionerRoleModel.content — never read to
    build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of two identical ones (same design as
    HealthcareServiceToken)."""

    __tablename__ = "practitioner_role_token"
    __table_args__ = (Index("ix_practitioner_role_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="tokens")

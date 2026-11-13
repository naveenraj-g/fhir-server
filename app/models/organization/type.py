from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class OrganizationType(Base):
    """Search index for the `type` token parameter: one row per
    Organization.type[].coding[] (a token search matches any coding of any
    type, so the CodeableConcept grouping doesn't need to be kept here) —
    plus one code-less row for a type that has only `text`, so `type:text`
    still finds it. Derived from OrganizationModel.content — never read to
    build a response.

      type              -> system, code
      type:text         -> text_norm (CodeableConcept.text) / display_norm (Coding.display)
      type:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "organization_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="types")

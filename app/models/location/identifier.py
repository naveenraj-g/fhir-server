from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class LocationIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*) — same
    shape as OrganizationIdentifier: one row per Location.identifier per
    Identifier.type.coding (one type-less row when there is no coded
    type), so `identifier:of-type` matches type and value on one row.
    Derived from LocationModel.content — never read to build a response.

      identifier          -> system, value
      identifier:of-type  -> type_system, type_code, value
      identifier:text     -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness — that's a profile decision, not a base rule."""

    __tablename__ = "location_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="identifiers")

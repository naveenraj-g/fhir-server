from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a HealthcareServiceReference row feeds, the
# HealthcareService element it is read from, and the resource type it points at.
REFERENCE_PARAMS = {
    "location": ("location", "Location"),
    "coverage-area": ("coverageArea", "Location"),
    "endpoint": ("endpoint", "Endpoint"),
}


class HealthcareServiceReference(Base):
    """Search index for the three 0..* reference parameters `location`,
    `coverage-area` and `endpoint`: one row per Reference that has a
    `reference` or an `identifier` (one with only `display` can't be matched
    by a reference search). `param` says which search parameter the row
    belongs to (see REFERENCE_PARAMS). Derived from
    HealthcareServiceModel.content — never read to build a response.

      <param>             -> reference_type/reference_id (a relative
                             Location/<id> or Endpoint/<id>) or
                             reference_reference (the raw string, for an
                             absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    `reference_type` is a plain string ("Location" / "Endpoint"), not a
    Postgres enum: the value is already fixed by `param`. No ForeignKey on
    `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 doesn't forbid listing the same reference twice."""

    __tablename__ = "healthcare_service_reference"
    __table_args__ = (
        Index("ix_healthcare_service_reference_param_id", "param", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="references"
    )

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class EncounterLocation(Base):
    """Search index for `location` and `location-period`
    (Encounter.location.location / .period). One row per Encounter.location
    entry, so a location and the period the patient was there stay together.
    Derived from EncounterModel.content — never read to build a response.

      location              -> reference_type (always Location)/reference_id or
                               reference_reference
      location:identifier   -> reference_identifier_system/_value
      location-period       -> period_start / period_end, the half-open range
                               the Period covers (NULL = open); see
                               app.repository._content_index.period_bounds

    `location.status` and `location.physicalType` have no search parameter and
    live only in `content`. No ForeignKey on `reference_id`, no
    UniqueConstraint."""

    __tablename__ = "encounter_location"
    __table_args__ = (
        Index("ix_encounter_location_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="locations")

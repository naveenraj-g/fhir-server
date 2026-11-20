from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The three R4 targets of Encounter.participant.individual.
PARTICIPANT_TYPES = ("Practitioner", "PractitionerRole", "RelatedPerson")


class EncounterParticipant(Base):
    """Search index for `participant` and `practitioner` (both
    Encounter.participant.individual — `practitioner` is the same element
    narrowed to the Practitioners). One row per participant that has an
    individual. Derived from EncounterModel.content — never read to build a
    response.

    `individual` can point at three resource types, so `reference_type`
    records which one a relative `Type/<id>` names (a plain string):

      participant              -> reference_type/reference_id or reference_reference
      practitioner             -> the same row, with reference_type = Practitioner
      participant:identifier   -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint."""

    __tablename__ = "encounter_participant"
    __table_args__ = (Index("ix_encounter_participant_type_id", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(BigInteger, ForeignKey("encounter.id"), nullable=False, index=True)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="participants")

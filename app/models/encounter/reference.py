from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter an EncounterReference row feeds, the Encounter element
# it is read from, and the resource types that element can point at (R4:
# account -> Account, appointment -> Appointment, basedOn -> ServiceRequest,
# diagnosis.condition -> Condition | Procedure, episodeOfCare -> EpisodeOfCare,
# reasonReference -> Condition | Observation | Procedure |
# ImmunizationRecommendation).
REFERENCE_PARAMS = {
    "account": "account",
    "appointment": "appointment",
    "based-on": "basedOn",
    "diagnosis": "diagnosis.condition",
    "episode-of-care": "episodeOfCare",
    "reason-reference": "reasonReference",
}
REFERENCE_TYPES = {
    "account": ("Account",),
    "appointment": ("Appointment",),
    "based-on": ("ServiceRequest",),
    "diagnosis": ("Condition", "Procedure"),
    "episode-of-care": ("EpisodeOfCare",),
    "reason-reference": ("Condition", "Observation", "Procedure", "ImmunizationRecommendation"),
}


class EncounterReference(Base):
    """Search index for the six 0..* reference parameters `account`,
    `appointment`, `based-on`, `diagnosis`, `episode-of-care` and
    `reason-reference`: one row per Reference that has a `reference` or an
    `identifier` (one with only `display` cannot be matched by a reference
    search). `param` says which search parameter the row belongs to (see
    REFERENCE_PARAMS). Derived from EncounterModel.content — never read to
    build a response.

    `reference_type` records which resource type a relative `Type/<id>` names —
    a plain string, not a Postgres enum, because `diagnosis` and
    `reason-reference` have several targets (a search by bare id is then
    ambiguous: `diagnosis=Type/id` or `:Type=id`).

      <param>             -> reference_type/reference_id (a relative
                             Type/<id>) or reference_reference (the raw
                             string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 does not forbid listing the same reference twice."""

    __tablename__ = "encounter_reference"
    __table_args__ = (Index("ix_encounter_reference_param_type_id", "param", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(BigInteger, ForeignKey("encounter.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="references")

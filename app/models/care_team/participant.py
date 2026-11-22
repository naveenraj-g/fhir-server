from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The six R4 targets of CareTeam.participant.member.
PARTICIPANT_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Patient",
    "Organization",
    "CareTeam",
)


class CareTeamParticipant(Base):
    """Search index for `participant` (CareTeam.participant.member, 0..* participants, each with
    one member Reference): one row per participant whose member has a `reference` or an
    `identifier`. Derived from CareTeamModel.content - never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names - a plain string, not a
    Postgres enum, because the member can be one of six types (a search by bare id is
    ambiguous: `participant=Type/id` or `:Type=id`).

      participant             -> reference_type/reference_id or reference_reference
      participant:identifier  -> reference_identifier_system/_value

    `role`, `onBehalfOf` and `period` live only in `content`."""

    __tablename__ = "care_team_participant"
    __table_args__ = (
        Index("ix_care_team_participant_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="participants")

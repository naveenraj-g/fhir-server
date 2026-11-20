from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The three R4 targets of Immunization.performer.actor.
PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization")
# The three R4 targets of Immunization.reasonReference.
REASON_TYPES = ("Condition", "Observation", "DiagnosticReport")


class ImmunizationPerformer(Base):
    """Search index for `performer` (Immunization.performer.actor, 0..* performers,
    each with one actor Reference): one row per performer whose actor has a
    `reference` or an `identifier`. Derived from ImmunizationModel.content — never
    read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum (a search by bare id is ambiguous:
    `performer=Type/id` or `:Type=id`).

      performer             -> reference_type/reference_id or reference_reference
      performer:identifier  -> reference_identifier_system/_value

    `performer.function` lives only in `content`."""

    __tablename__ = "immunization_performer"
    __table_args__ = (Index("ix_immunization_performer_type_id", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(BigInteger, ForeignKey("immunization.id"), nullable=False, index=True)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="performers")


class ImmunizationReasonReference(Base):
    """Search index for `reason-reference` (Immunization.reasonReference, 0..*):
    one row per Reference that has a `reference` or an `identifier` (one with only
    `display` cannot be matched by a reference search). Derived from
    ImmunizationModel.content — never read to build a response.

      reason-reference             -> reference_type/reference_id or reference_reference
      reason-reference:identifier  -> reference_identifier_system/_value"""

    __tablename__ = "immunization_reason_reference"
    __table_args__ = (Index("ix_immunization_reason_reference_type_id", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(BigInteger, ForeignKey("immunization.id"), nullable=False, index=True)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="reason_references")


class ImmunizationReaction(Base):
    """Search index for `reaction` (Immunization.reaction.detail, a Reference(Observation))
    and `reaction-date` (Immunization.reaction.date): one row per reaction that has
    either, so the two stay together. Derived from ImmunizationModel.content — never
    read to build a response.

      reaction                -> detail_type/detail_id or detail_reference
      reaction:identifier     -> detail_identifier_system/_value
      reaction-date           -> date_start/_end (the half-open range the dateTime
                                 covers; matched with period_match)

    `reaction.reported` lives only in `content`."""

    __tablename__ = "immunization_reaction"
    __table_args__ = (Index("ix_immunization_reaction_detail", "detail_type", "detail_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(BigInteger, ForeignKey("immunization.id"), nullable=False, index=True)
    detail_reference = Column(String, nullable=True)
    detail_type = Column(String, nullable=True)
    detail_id = Column(BigInteger, nullable=True)
    detail_identifier_system = Column(String, nullable=True)
    detail_identifier_value = Column(String, nullable=True)
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="reactions")

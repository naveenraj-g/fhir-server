from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The six R4 targets of Procedure.performer.actor.
PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "RelatedPerson",
    "Device",
)


class ProcedurePerformer(Base):
    """Search index for `performer` (Procedure.performer.actor, 0..* performers,
    each with one actor Reference): one row per performer whose actor has a
    `reference` or an `identifier`. Derived from ProcedureModel.content — never
    read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum, because the actor can be one of six types (a
    search by bare id is ambiguous: `performer=Type/id` or `:Type=id`).

      performer             -> reference_type/reference_id or reference_reference
      performer:identifier  -> reference_identifier_system/_value

    `function` and `onBehalfOf` live only in `content`."""

    __tablename__ = "procedure_performer"
    __table_args__ = (
        Index("ix_procedure_performer_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="performers")

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class GoalIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*). Derived from
    GoalModel.content - never read to build a response.

    One row per Goal.identifier *per Identifier.type.coding* (one row with no type when the
    identifier has no coded type), so that `identifier:of-type=type-system|type-code|value` can
    match type and value on the same row. A plain `identifier=` search is an EXISTS, so the
    repetition never duplicates results.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 does not require identifier uniqueness."""

    __tablename__ = "goal_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named goal_pk (not goal_id) so it cannot be confused with GoalModel.goal_id, the public id.
    goal_pk = Column(BigInteger, ForeignKey("goal.id"), nullable=False, index=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="identifiers")

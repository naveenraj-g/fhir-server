from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

from .enums import AllergyIntoleranceReactionSeverity


class AllergyIntoleranceReaction(Base):
    """Search index for the `onset` and `severity` parameters, which read
    AllergyIntolerance.reaction.onset and .severity (0..* reactions, each with at
    most one of each): one row per reaction that has an onset or a severity. Derived
    from AllergyIntoleranceModel.content — never read to build a response.

      onset -> onset_start/_end  (the half-open [start, end) range the dateTime
               covers, so a partial dateTime like `2024-03` works — see
               period_bounds; matched with period_match)
      severity -> severity (0..1 code, Enum column, required binding)

    The reaction's other elements (description, severity, substance,
    manifestation, exposureRoute, note) live in `content`; the ones a search
    parameter reads are in AllergyIntoleranceToken."""

    __tablename__ = "allergy_intolerance_reaction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger, ForeignKey("allergy_intolerance.id"), nullable=False, index=True
    )
    onset_start = Column(DateTime(timezone=True), nullable=True)
    onset_end = Column(DateTime(timezone=True), nullable=True)
    severity = Column(
        Enum(
            AllergyIntoleranceReactionSeverity,
            name="allergy_intolerance_reaction_severity",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel", back_populates="reactions"
    )

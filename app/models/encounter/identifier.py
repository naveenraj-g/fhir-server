from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class EncounterIdentifier(Base):
    """Search index for `identifier` (Encounter.identifier, 0..*): one row per
    identifier x type.coding (a type-less row when the identifier has no coded
    type), so `identifier:of-type` matches type and value on the same row.
    Derived from EncounterModel.content — never read to build a response.

      identifier           -> system, value
      identifier:text      -> type_text_norm / type_display_norm
      identifier:of-type   -> type_system, type_code, value

    No UniqueConstraint: R4 does not require identifier uniqueness."""

    __tablename__ = "encounter_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="identifiers")

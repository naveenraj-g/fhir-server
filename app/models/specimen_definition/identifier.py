from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class SpecimenDefinitionIdentifier(Base):
    """Search index for the `identifier` token parameter (SpecimenDefinition.identifier, 0..*).
    Derived from SpecimenDefinitionModel.content - never read to build a response.

    One row per Identifier.type.coding (one row with no type when the identifier has no coded
    type), so that `identifier:of-type=type-system|type-code|value` can match type and value on the
    same row.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 does not require identifier uniqueness."""

    __tablename__ = "specimen_definition_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named specimen_definition_pk (not specimen_definition_id) so it cannot be confused with
    # SpecimenDefinitionModel.specimen_definition_id, the public id.
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="identifiers"
    )

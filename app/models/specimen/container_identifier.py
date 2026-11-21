from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class SpecimenContainerIdentifier(Base):
    """Search index for the `container-id` token parameter (Specimen.container.identifier, 0..* per container). Derived
    from SpecimenModel.content — never read to build a response.

    One row per Specimen.container.identifier *per Identifier.type.coding*
    (one row with no type when the identifier has no coded type), so that
    `identifier:of-type=type-system|type-code|value` can match type and
    value on the same row. A plain `identifier=` search is an EXISTS, so
    the repetition never duplicates results.

      container-id          -> system, value
      container-id:of-type    -> type_system, type_code, value
      container-id:text     -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness — that's a profile decision, not a base rule."""

    __tablename__ = "specimen_container_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named specimen_pk (not specimen_id) so it can't be
    # confused with SpecimenModel.specimen_id, the public id.
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="container_identifiers")

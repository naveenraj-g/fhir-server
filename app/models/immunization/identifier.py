from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ImmunizationIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*). Derived
    from ImmunizationModel.content — never read to build a response.

    One row per Immunization.identifier *per Identifier.type.coding*
    (one row with no type when the identifier has no coded type), so that
    `identifier:of-type=type-system|type-code|value` can match type and
    value on the same row. A plain `identifier=` search is an EXISTS, so
    the repetition never duplicates results.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness — that's a profile decision, not a base rule."""

    __tablename__ = "immunization_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named immunization_pk (not immunization_id) so it can't be
    # confused with ImmunizationModel.immunization_id, the public id.
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="identifiers")

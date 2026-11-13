from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class OrganizationIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*). Derived
    from OrganizationModel.content — never read to build a response.

    One row per Organization.identifier *per Identifier.type.coding* (one
    row with no type when the identifier has no coded type), so that
    `identifier:of-type=type-system|type-code|value` can match type and
    value on the same row. A plain `identifier=` search is an EXISTS, so
    the repetition never duplicates results.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm (Identifier.type.text) /
                               type_display_norm (type.coding.display)

    No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness — that's a profile decision, not a base rule."""

    __tablename__ = "organization_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named organization_pk (not organization_id) so it can't be confused
    # with OrganizationModel.organization_id, the public sequence id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="identifiers")

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenDefinitionIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of SpecimenDefinition.identifier.type.coding (0..*).

    FKs directly to specimen_definition table since identifier is 0..1.
    """

    __tablename__ = "specimen_definition_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="identifier_type_codings"
    )

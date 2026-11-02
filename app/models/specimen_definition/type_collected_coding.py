from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenDefinitionTypeCollectedCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One coding entry in SpecimenDefinition.typeCollected.coding (0..*)."""

    __tablename__ = "specimen_definition_type_collected_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="type_collected_codings"
    )

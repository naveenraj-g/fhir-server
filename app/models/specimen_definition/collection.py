from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenDefinitionCollection(TenantAuditMixin, Base):
    """SpecimenDefinition.collection (0..* CodeableConcept)."""

    __tablename__ = "specimen_definition_collection"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="collections"
    )
    codings = relationship(
        "SpecimenDefinitionCollectionCoding",
        back_populates="collection",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionCollectionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.collection."""

    __tablename__ = "specimen_definition_collection_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    collection_pk = Column(
        BigInteger, ForeignKey("specimen_definition_collection.id"), nullable=False, index=True
    )

    collection = relationship(
        "SpecimenDefinitionCollection", back_populates="codings"
    )

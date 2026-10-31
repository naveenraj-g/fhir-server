from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin
from app.models.specimen.enums import SpecimenAdditiveReferenceType


class SpecimenContainer(TenantAuditMixin, Base):
    """One entry of Specimen.container (0..* BackboneElement)."""

    __tablename__ = "specimen_container"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    description = Column(String, nullable=True)
    type_text = Column(String, nullable=True)

    # capacity (0..1 SimpleQuantity)
    capacity_value = Column(Numeric, nullable=True)
    capacity_unit = Column(String, nullable=True)
    capacity_system = Column(String, nullable=True)
    capacity_code = Column(String, nullable=True)

    # specimenQuantity (0..1 SimpleQuantity)
    specimen_quantity_value = Column(Numeric, nullable=True)
    specimen_quantity_unit = Column(String, nullable=True)
    specimen_quantity_system = Column(String, nullable=True)
    specimen_quantity_code = Column(String, nullable=True)

    # additive[x] (0..1 CodeableConcept | Reference(Substance))
    additive_codeable_concept_text = Column(String, nullable=True)
    additive_reference_reference = Column(String, nullable=True)
    additive_reference_type = Column(
        Enum(
            SpecimenAdditiveReferenceType,
            name="specimen_additive_reference_type",
        ),
        nullable=True,
    )
    additive_reference_id = Column(BigInteger, nullable=True, index=True)
    additive_reference_display = Column(String, nullable=True)

    # additive.reference identifier fallback
    additive_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    additive_reference_identifier_system = Column(String, nullable=True)
    additive_reference_identifier_value = Column(String, nullable=True)
    additive_reference_identifier_type_text = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="containers")
    identifiers = relationship(
        "SpecimenContainerIdentifier",
        back_populates="container",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "SpecimenContainerTypeCoding",
        back_populates="container",
        cascade="all, delete-orphan",
    )
    additive_codings = relationship(
        "SpecimenContainerAdditiveCoding",
        back_populates="container",
        cascade="all, delete-orphan",
    )


class SpecimenContainerIdentifier(TenantAuditMixin, Base):
    """Specimen.container.identifier (0..*) grandchild table."""

    __tablename__ = "specimen_container_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_container_id = Column(
        BigInteger, ForeignKey("specimen_container.id"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    assigner_reference = Column(String, nullable=True)
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_display = Column(String, nullable=True)

    # assigner.identifier fallback
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)

    container = relationship("SpecimenContainer", back_populates="identifiers")
    type_codings = relationship(
        "SpecimenContainerIdentifierTypeCoding",
        back_populates="container_identifier",
        cascade="all, delete-orphan",
    )


class SpecimenContainerIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.container.identifier.type.coding (0..*)."""

    __tablename__ = "specimen_container_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_container_identifier_id = Column(
        BigInteger,
        ForeignKey("specimen_container_identifier.id"),
        nullable=False,
        index=True,
    )

    container_identifier = relationship(
        "SpecimenContainerIdentifier", back_populates="type_codings"
    )


class SpecimenContainerTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.container.type.coding (0..*)."""

    __tablename__ = "specimen_container_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_container_id = Column(
        BigInteger, ForeignKey("specimen_container.id"), nullable=False, index=True
    )

    container = relationship("SpecimenContainer", back_populates="type_codings")


class SpecimenContainerAdditiveCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.container.additiveCodeableConcept.coding (0..*)."""

    __tablename__ = "specimen_container_additive_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_container_id = Column(
        BigInteger, ForeignKey("specimen_container.id"), nullable=False, index=True
    )

    container = relationship("SpecimenContainer", back_populates="additive_codings")

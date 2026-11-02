from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin
from app.models.specimen_definition.enums import (
    SpecimenDefinitionAdditiveReferenceType,
    SpecimenDefinitionPreference,
    SpecimenDefinitionQuantityComparator,
)


class SpecimenDefinitionTypeTested(TenantAuditMixin, Base):
    """SpecimenDefinition.typeTested (0..* BackboneElement)."""

    __tablename__ = "specimen_definition_type_tested"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )

    is_derived = Column(Boolean, nullable=True)
    type_text = Column(String, nullable=True)
    preference = Column(
        Enum(SpecimenDefinitionPreference, name="specimen_definition_preference"),
        nullable=False,
    )
    requirement = Column(String, nullable=True)

    # retentionTime (0..1 Duration)
    retention_time_value = Column(Numeric, nullable=True)
    retention_time_comparator = Column(
        Enum(
            SpecimenDefinitionQuantityComparator,
            name="specimen_definition_quantity_comparator",
        ),
        nullable=True,
    )
    retention_time_unit = Column(String, nullable=True)
    retention_time_system = Column(String, nullable=True)
    retention_time_code = Column(String, nullable=True)

    # container (0..1 BackboneElement) — flattened
    container_description = Column(String, nullable=True)
    container_preparation = Column(String, nullable=True)
    container_material_text = Column(String, nullable=True)
    container_type_text = Column(String, nullable=True)
    container_cap_text = Column(String, nullable=True)

    # container.capacity (0..1 SimpleQuantity)
    container_capacity_value = Column(Numeric, nullable=True)
    container_capacity_unit = Column(String, nullable=True)
    container_capacity_system = Column(String, nullable=True)
    container_capacity_code = Column(String, nullable=True)

    # container.minimumVolume[x] (0..1 Quantity | string)
    container_minimum_volume_string = Column(String, nullable=True)
    container_minimum_volume_quantity_value = Column(Numeric, nullable=True)
    container_minimum_volume_quantity_comparator = Column(
        Enum(
            SpecimenDefinitionQuantityComparator,
            name="specimen_definition_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    container_minimum_volume_quantity_unit = Column(String, nullable=True)
    container_minimum_volume_quantity_system = Column(String, nullable=True)
    container_minimum_volume_quantity_code = Column(String, nullable=True)

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="types_tested"
    )
    type_codings = relationship(
        "SpecimenDefinitionTypeTestedTypeCoding",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    container_material_codings = relationship(
        "SpecimenDefinitionContainerMaterialCoding",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    container_type_codings = relationship(
        "SpecimenDefinitionContainerTypeCoding",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    container_cap_codings = relationship(
        "SpecimenDefinitionContainerCapCoding",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    container_additives = relationship(
        "SpecimenDefinitionContainerAdditive",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    rejection_criteria = relationship(
        "SpecimenDefinitionTypeTestedRejectionCriterion",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )
    handlings = relationship(
        "SpecimenDefinitionTypeTestedHandling",
        back_populates="type_tested",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionTypeTestedTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.type."""

    __tablename__ = "specimen_definition_type_tested_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="type_codings"
    )


class SpecimenDefinitionContainerMaterialCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.container.material."""

    __tablename__ = "specimen_definition_container_material_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="container_material_codings"
    )


class SpecimenDefinitionContainerTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.container.type."""

    __tablename__ = "specimen_definition_container_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="container_type_codings"
    )


class SpecimenDefinitionContainerCapCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.container.cap."""

    __tablename__ = "specimen_definition_container_cap_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="container_cap_codings"
    )


class SpecimenDefinitionContainerAdditive(TenantAuditMixin, Base):
    """SpecimenDefinition.typeTested.container.additive (0..* BackboneElement)."""

    __tablename__ = "specimen_definition_container_additive"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    # additive[x] (1..1 CodeableConcept | Reference(Substance))
    additive_codeable_concept_text = Column(String, nullable=True)
    additive_reference_reference = Column(String, nullable=True)
    additive_reference_type = Column(
        Enum(
            SpecimenDefinitionAdditiveReferenceType,
            name="specimen_definition_additive_reference_type",
        ),
        nullable=True,
    )
    additive_reference_id = Column(BigInteger, nullable=True, index=True)
    additive_reference_display = Column(String, nullable=True)

    # additive_reference identifier fallback columns
    additive_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    additive_reference_identifier_type_system = Column(String, nullable=True)
    additive_reference_identifier_type_version = Column(String, nullable=True)
    additive_reference_identifier_type_code = Column(String, nullable=True)
    additive_reference_identifier_type_display = Column(String, nullable=True)
    additive_reference_identifier_type_text = Column(String, nullable=True)
    additive_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    additive_reference_identifier_system = Column(String, nullable=True)
    additive_reference_identifier_value = Column(String, nullable=True)
    additive_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    additive_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="container_additives"
    )
    additive_codings = relationship(
        "SpecimenDefinitionContainerAdditiveCoding",
        back_populates="container_additive",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionContainerAdditiveCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.container.additive.additiveCodeableConcept."""

    __tablename__ = "specimen_definition_container_additive_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    container_additive_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_container_additive.id"),
        nullable=False,
        index=True,
    )

    container_additive = relationship(
        "SpecimenDefinitionContainerAdditive", back_populates="additive_codings"
    )


class SpecimenDefinitionTypeTestedRejectionCriterion(TenantAuditMixin, Base):
    """SpecimenDefinition.typeTested.rejectionCriterion (0..* CodeableConcept)."""

    __tablename__ = "specimen_definition_type_tested_rejection_criterion"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )
    text = Column(String, nullable=True)

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="rejection_criteria"
    )
    codings = relationship(
        "SpecimenDefinitionTypeTestedRejectionCriterionCoding",
        back_populates="rejection_criterion",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionTypeTestedRejectionCriterionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.rejectionCriterion."""

    __tablename__ = "specimen_definition_type_tested_rejection_criterion_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rejection_criterion_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested_rejection_criterion.id"),
        nullable=False,
        index=True,
    )

    rejection_criterion = relationship(
        "SpecimenDefinitionTypeTestedRejectionCriterion", back_populates="codings"
    )


class SpecimenDefinitionTypeTestedHandling(TenantAuditMixin, Base):
    """SpecimenDefinition.typeTested.handling (0..* BackboneElement)."""

    __tablename__ = "specimen_definition_type_tested_handling"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_tested_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested.id"),
        nullable=False,
        index=True,
    )

    temperature_qualifier_text = Column(String, nullable=True)

    # temperatureRange (0..1 Range)
    temperature_range_low_value = Column(Numeric, nullable=True)
    temperature_range_low_unit = Column(String, nullable=True)
    temperature_range_low_system = Column(String, nullable=True)
    temperature_range_low_code = Column(String, nullable=True)
    temperature_range_high_value = Column(Numeric, nullable=True)
    temperature_range_high_unit = Column(String, nullable=True)
    temperature_range_high_system = Column(String, nullable=True)
    temperature_range_high_code = Column(String, nullable=True)

    # maxDuration (0..1 Duration)
    max_duration_value = Column(Numeric, nullable=True)
    max_duration_comparator = Column(
        Enum(
            SpecimenDefinitionQuantityComparator,
            name="specimen_definition_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    max_duration_unit = Column(String, nullable=True)
    max_duration_system = Column(String, nullable=True)
    max_duration_code = Column(String, nullable=True)

    instruction = Column(String, nullable=True)

    type_tested = relationship(
        "SpecimenDefinitionTypeTested", back_populates="handlings"
    )
    temperature_qualifier_codings = relationship(
        "SpecimenDefinitionHandlingTempQualCoding",
        back_populates="handling",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionHandlingTempQualCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.typeTested.handling.temperatureQualifier."""

    __tablename__ = "specimen_definition_handling_temp_qual_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    handling_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_type_tested_handling.id"),
        nullable=False,
        index=True,
    )

    handling = relationship(
        "SpecimenDefinitionTypeTestedHandling", back_populates="temperature_qualifier_codings"
    )

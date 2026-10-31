from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionDosage(TenantAuditMixin, Base):
    """ActivityDefinition.dosage (0..* Dosage) child table."""

    __tablename__ = "activity_definition_dosage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    sequence = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)
    timing = Column(JSONB, nullable=True)
    as_needed_boolean = Column(Boolean, nullable=True)
    as_needed_codeable_concept_text = Column(String, nullable=True)
    site_text = Column(String, nullable=True)
    route_text = Column(String, nullable=True)
    method_text = Column(String, nullable=True)
    dose_and_rate = Column(JSONB, nullable=True)
    max_dose_per_period = Column(JSONB, nullable=True)

    max_dose_per_administration_value = Column(Numeric, nullable=True)
    max_dose_per_administration_unit = Column(String, nullable=True)
    max_dose_per_administration_system = Column(String, nullable=True)
    max_dose_per_administration_code = Column(String, nullable=True)

    max_dose_per_lifetime_value = Column(Numeric, nullable=True)
    max_dose_per_lifetime_unit = Column(String, nullable=True)
    max_dose_per_lifetime_system = Column(String, nullable=True)
    max_dose_per_lifetime_code = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="dosages")

    site_codings = relationship(
        "ActivityDefinitionDosageSiteCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    route_codings = relationship(
        "ActivityDefinitionDosageRouteCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    method_codings = relationship(
        "ActivityDefinitionDosageMethodCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    as_needed_codings = relationship(
        "ActivityDefinitionDosageAsNeededCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionDosageSiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.dosage.site.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_dosage_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_dosage_id = Column(
        BigInteger,
        ForeignKey("activity_definition_dosage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dosage = relationship("ActivityDefinitionDosage", back_populates="site_codings")


class ActivityDefinitionDosageRouteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.dosage.route.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_dosage_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_dosage_id = Column(
        BigInteger,
        ForeignKey("activity_definition_dosage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dosage = relationship("ActivityDefinitionDosage", back_populates="route_codings")


class ActivityDefinitionDosageMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.dosage.method.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_dosage_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_dosage_id = Column(
        BigInteger,
        ForeignKey("activity_definition_dosage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dosage = relationship("ActivityDefinitionDosage", back_populates="method_codings")


class ActivityDefinitionDosageAsNeededCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.dosage.asNeededCodeableConcept.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_dosage_as_needed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_dosage_id = Column(
        BigInteger,
        ForeignKey("activity_definition_dosage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dosage = relationship("ActivityDefinitionDosage", back_populates="as_needed_codings")

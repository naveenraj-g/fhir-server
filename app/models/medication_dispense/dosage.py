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


class MedicationDispenseDosageInstruction(TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction (0..* Dosage) child table."""

    __tablename__ = "medication_dispense_dosage_instruction"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )

    sequence = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)

    # timing (0..1 Timing) — raw JSONB
    timing = Column(JSONB, nullable=True)

    # asNeeded[x] (0..1 choice: boolean | CodeableConcept)
    as_needed_boolean = Column(Boolean, nullable=True)
    as_needed_codeable_concept_text = Column(String, nullable=True)

    # site / route / method (each 0..1 CodeableConcept) — text flattened
    site_text = Column(String, nullable=True)
    route_text = Column(String, nullable=True)
    method_text = Column(String, nullable=True)

    # doseAndRate (0..*) — raw JSONB
    dose_and_rate = Column(JSONB, nullable=True)

    # maxDosePerPeriod (0..1 Ratio) — raw JSONB
    max_dose_per_period = Column(JSONB, nullable=True)

    # maxDosePerAdministration / maxDosePerLifetime (each 0..1 SimpleQuantity)
    max_dose_per_administration_value = Column(Numeric, nullable=True)
    max_dose_per_administration_unit = Column(String, nullable=True)
    max_dose_per_administration_system = Column(String, nullable=True)
    max_dose_per_administration_code = Column(String, nullable=True)

    max_dose_per_lifetime_value = Column(Numeric, nullable=True)
    max_dose_per_lifetime_unit = Column(String, nullable=True)
    max_dose_per_lifetime_system = Column(String, nullable=True)
    max_dose_per_lifetime_code = Column(String, nullable=True)

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="dosage_instructions"
    )
    additional_instructions = relationship(
        "MedicationDispenseDosageAdditionalInstruction",
        back_populates="dosage_instruction",
        cascade="all, delete-orphan",
    )
    site_codings = relationship(
        "MedicationDispenseDosageSiteCoding",
        back_populates="dosage_instruction",
        cascade="all, delete-orphan",
    )
    route_codings = relationship(
        "MedicationDispenseDosageRouteCoding",
        back_populates="dosage_instruction",
        cascade="all, delete-orphan",
    )
    method_codings = relationship(
        "MedicationDispenseDosageMethodCoding",
        back_populates="dosage_instruction",
        cascade="all, delete-orphan",
    )
    as_needed_codings = relationship(
        "MedicationDispenseDosageAsNeededCoding",
        back_populates="dosage_instruction",
        cascade="all, delete-orphan",
    )


class MedicationDispenseDosageAdditionalInstruction(TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction.additionalInstruction (0..* CodeableConcept) child table."""

    __tablename__ = "medication_dispense_dosage_additional_instruction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_instruction.id"),
        nullable=False,
        index=True,
    )
    text = Column(String, nullable=True)

    dosage_instruction = relationship(
        "MedicationDispenseDosageInstruction", back_populates="additional_instructions"
    )
    codings = relationship(
        "MedicationDispenseDosageAdditionalInstructionCoding",
        back_populates="additional_instruction",
        cascade="all, delete-orphan",
    )


class MedicationDispenseDosageAdditionalInstructionCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MedicationDispense.dosageInstruction.additionalInstruction.coding (0..*) grandchild table."""

    __tablename__ = "medication_dispense_dosage_additional_instruction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_additional_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_additional_instruction.id"),
        nullable=False,
        index=True,
    )

    additional_instruction = relationship(
        "MedicationDispenseDosageAdditionalInstruction", back_populates="codings"
    )


class MedicationDispenseDosageSiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction.site.coding (0..*) child table."""

    __tablename__ = "medication_dispense_dosage_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_instruction.id"),
        nullable=False,
        index=True,
    )

    dosage_instruction = relationship(
        "MedicationDispenseDosageInstruction", back_populates="site_codings"
    )


class MedicationDispenseDosageRouteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction.route.coding (0..*) child table."""

    __tablename__ = "medication_dispense_dosage_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_instruction.id"),
        nullable=False,
        index=True,
    )

    dosage_instruction = relationship(
        "MedicationDispenseDosageInstruction", back_populates="route_codings"
    )


class MedicationDispenseDosageMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction.method.coding (0..*) child table."""

    __tablename__ = "medication_dispense_dosage_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_instruction.id"),
        nullable=False,
        index=True,
    )

    dosage_instruction = relationship(
        "MedicationDispenseDosageInstruction", back_populates="method_codings"
    )


class MedicationDispenseDosageAsNeededCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.dosageInstruction.asNeededCodeableConcept.coding (0..*) child table."""

    __tablename__ = "medication_dispense_dosage_as_needed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_dosage_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_dosage_instruction.id"),
        nullable=False,
        index=True,
    )

    dosage_instruction = relationship(
        "MedicationDispenseDosageInstruction", back_populates="as_needed_codings"
    )

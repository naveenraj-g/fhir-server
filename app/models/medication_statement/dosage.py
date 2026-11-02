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


class MedicationStatementDosage(TenantAuditMixin, Base):
    """MedicationStatement.dosage (0..* Dosage) child table."""

    __tablename__ = "medication_statement_dosage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_pk = Column(
        BigInteger, ForeignKey("medication_statement.id"), nullable=False, index=True
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

    medication_statement = relationship(
        "MedicationStatementModel", back_populates="dosages"
    )

    site_codings = relationship(
        "MedicationStatementDosageSiteCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    route_codings = relationship(
        "MedicationStatementDosageRouteCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    method_codings = relationship(
        "MedicationStatementDosageMethodCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    as_needed_codings = relationship(
        "MedicationStatementDosageAsNeededCoding",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )
    additional_instructions = relationship(
        "MedicationStatementDosageAdditionalInstruction",
        back_populates="dosage",
        cascade="all, delete-orphan",
    )


class MedicationStatementDosageSiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.dosage.site.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_dosage_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage.id"),
        nullable=False,
        index=True,
    )

    dosage = relationship("MedicationStatementDosage", back_populates="site_codings")


class MedicationStatementDosageRouteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.dosage.route.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_dosage_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage.id"),
        nullable=False,
        index=True,
    )

    dosage = relationship("MedicationStatementDosage", back_populates="route_codings")


class MedicationStatementDosageMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.dosage.method.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_dosage_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage.id"),
        nullable=False,
        index=True,
    )

    dosage = relationship("MedicationStatementDosage", back_populates="method_codings")


class MedicationStatementDosageAsNeededCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.dosage.asNeededCodeableConcept.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_dosage_as_needed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage.id"),
        nullable=False,
        index=True,
    )

    dosage = relationship(
        "MedicationStatementDosage", back_populates="as_needed_codings"
    )


class MedicationStatementDosageAdditionalInstruction(TenantAuditMixin, Base):
    """MedicationStatement.dosage.additionalInstruction (0..* CodeableConcept) grandchild table."""

    __tablename__ = "medication_statement_dosage_additional_instruction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    dosage = relationship(
        "MedicationStatementDosage", back_populates="additional_instructions"
    )
    codings = relationship(
        "MedicationStatementDosageAdditionalInstructionCoding",
        back_populates="additional_instruction",
        cascade="all, delete-orphan",
    )


class MedicationStatementDosageAdditionalInstructionCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MedicationStatement.dosage.additionalInstruction.coding (0..*) great-grandchild table."""

    __tablename__ = "medication_statement_dosage_additional_instruction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_dosage_additional_instruction_id = Column(
        BigInteger,
        ForeignKey("medication_statement_dosage_additional_instruction.id"),
        nullable=False,
        index=True,
    )

    additional_instruction = relationship(
        "MedicationStatementDosageAdditionalInstruction", back_populates="codings"
    )

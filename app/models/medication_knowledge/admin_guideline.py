from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeAdminGuidelineIndicationReferenceType,
    MedicationKnowledgeQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeAdminGuideline(Base, TenantAuditMixin):
    """MedicationKnowledge.administrationGuidelines (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_admin_guideline"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    # indication[x] (0..1 choice: CodeableConcept | Reference(ObservationDefinition))
    indication_codeable_concept_text = Column(String, nullable=True)

    indication_reference = Column(String, nullable=True)
    indication_type = Column(
        Enum(
            MedicationKnowledgeAdminGuidelineIndicationReferenceType,
            name="medication_knowledge_ag_indication_ref_type",
        ),
        nullable=True,
    )
    indication_id = Column(BigInteger, nullable=True, index=True)
    indication_display = Column(String, nullable=True)

    indication_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    indication_identifier_type_system = Column(String, nullable=True)
    indication_identifier_type_version = Column(String, nullable=True)
    indication_identifier_type_code = Column(String, nullable=True)
    indication_identifier_type_display = Column(String, nullable=True)
    indication_identifier_type_user_selected = Column(Boolean, nullable=True)
    indication_identifier_type_text = Column(String, nullable=True)
    indication_identifier_system = Column(String, nullable=True)
    indication_identifier_value = Column(String, nullable=True)
    indication_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    indication_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="administration_guidelines"
    )
    indication_codings = relationship(
        "MedicationKnowledgeAdminGuidelineIndicationCoding",
        back_populates="admin_guideline",
        cascade="all, delete-orphan",
    )
    dosages = relationship(
        "MedicationKnowledgeAdminGuidelineDosage",
        back_populates="admin_guideline",
        cascade="all, delete-orphan",
    )
    patient_characteristics = relationship(
        "MedicationKnowledgeAdminGuidelinePatientCharacteristic",
        back_populates="admin_guideline",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeAdminGuidelineIndicationCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.administrationGuidelines.indicationCodeableConcept.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_ag_indication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_admin_guideline_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_admin_guideline.id"),
        nullable=False,
        index=True,
    )

    admin_guideline = relationship(
        "MedicationKnowledgeAdminGuideline", back_populates="indication_codings"
    )


class MedicationKnowledgeAdminGuidelineDosage(Base, TenantAuditMixin):
    """MedicationKnowledge.administrationGuidelines.dosage (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_ag_dosage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_admin_guideline_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_admin_guideline.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)
    # dosage (1..* Dosage) — JSONB array of Dosage elements
    dosage = Column(JSONB, nullable=False)

    admin_guideline = relationship(
        "MedicationKnowledgeAdminGuideline", back_populates="dosages"
    )
    type_codings = relationship(
        "MedicationKnowledgeAdminGuidelineDosageTypeCoding",
        back_populates="ag_dosage",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeAdminGuidelineDosageTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.administrationGuidelines.dosage.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_ag_dosage_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_ag_dosage_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_ag_dosage.id"),
        nullable=False,
        index=True,
    )

    ag_dosage = relationship(
        "MedicationKnowledgeAdminGuidelineDosage", back_populates="type_codings"
    )


class MedicationKnowledgeAdminGuidelinePatientCharacteristic(Base, TenantAuditMixin):
    """MedicationKnowledge.administrationGuidelines.patientCharacteristics (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_ag_patient_char"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_admin_guideline_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_admin_guideline.id"),
        nullable=False,
        index=True,
    )

    # characteristic[x] (1..1 choice: CodeableConcept | Quantity)
    characteristic_codeable_concept_text = Column(String, nullable=True)
    characteristic_quantity_value = Column(Numeric, nullable=True)
    characteristic_quantity_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    characteristic_quantity_unit = Column(String, nullable=True)
    characteristic_quantity_system = Column(String, nullable=True)
    characteristic_quantity_code = Column(String, nullable=True)

    # value (0..* string)
    value = Column(ARRAY(String), nullable=True)

    admin_guideline = relationship(
        "MedicationKnowledgeAdminGuideline", back_populates="patient_characteristics"
    )
    characteristic_codings = relationship(
        "MedicationKnowledgeAdminGuidelinePatientCharCoding",
        back_populates="patient_characteristic",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeAdminGuidelinePatientCharCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.administrationGuidelines.patientCharacteristics.characteristicCodeableConcept.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_ag_patient_char_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_ag_patient_char_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_ag_patient_char.id"),
        nullable=False,
        index=True,
    )

    patient_characteristic = relationship(
        "MedicationKnowledgeAdminGuidelinePatientCharacteristic",
        back_populates="characteristic_codings",
    )

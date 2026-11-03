from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeMedicineClassification(Base, TenantAuditMixin):
    """MedicationKnowledge.medicineClassification (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_medicine_classification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="medicine_classifications"
    )
    type_codings = relationship(
        "MedicationKnowledgeMedicineClassificationTypeCoding",
        back_populates="medicine_classification",
        cascade="all, delete-orphan",
    )
    classification_items = relationship(
        "MedicationKnowledgeMedicineClassificationItem",
        back_populates="medicine_classification",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeMedicineClassificationTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.medicineClassification.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_med_class_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_medicine_classification_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_medicine_classification.id"),
        nullable=False,
        index=True,
    )

    medicine_classification = relationship(
        "MedicationKnowledgeMedicineClassification", back_populates="type_codings"
    )


class MedicationKnowledgeMedicineClassificationItem(Base, TenantAuditMixin):
    """MedicationKnowledge.medicineClassification.classification (0..* CodeableConcept)."""

    __tablename__ = "medication_knowledge_med_class_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_medicine_classification_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_medicine_classification.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    medicine_classification = relationship(
        "MedicationKnowledgeMedicineClassification",
        back_populates="classification_items",
    )
    codings = relationship(
        "MedicationKnowledgeMedicineClassificationItemCoding",
        back_populates="classification_item",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeMedicineClassificationItemCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.medicineClassification.classification.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_med_class_item_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_med_class_item_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_med_class_item.id"),
        nullable=False,
        index=True,
    )

    classification_item = relationship(
        "MedicationKnowledgeMedicineClassificationItem",
        back_populates="codings",
    )

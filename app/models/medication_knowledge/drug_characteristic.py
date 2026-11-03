from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeDrugCharacteristic(Base, TenantAuditMixin):
    """MedicationKnowledge.drugCharacteristic (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_drug_characteristic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)

    # value[x] (0..1 choice: CodeableConcept | string | Quantity | base64Binary)
    value_codeable_concept_text = Column(String, nullable=True)
    value_string = Column(String, nullable=True)
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)
    value_base64_binary = Column(Text, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="drug_characteristics"
    )
    type_codings = relationship(
        "MedicationKnowledgeDrugCharacteristicTypeCoding",
        back_populates="drug_characteristic",
        cascade="all, delete-orphan",
    )
    value_codings = relationship(
        "MedicationKnowledgeDrugCharacteristicValueCoding",
        back_populates="drug_characteristic",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeDrugCharacteristicTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.drugCharacteristic.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_drug_char_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_drug_characteristic_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_drug_characteristic.id"),
        nullable=False,
        index=True,
    )

    drug_characteristic = relationship(
        "MedicationKnowledgeDrugCharacteristic", back_populates="type_codings"
    )


class MedicationKnowledgeDrugCharacteristicValueCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.drugCharacteristic.valueCodeableConcept.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_drug_char_val_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_drug_characteristic_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_drug_characteristic.id"),
        nullable=False,
        index=True,
    )

    drug_characteristic = relationship(
        "MedicationKnowledgeDrugCharacteristic", back_populates="value_codings"
    )

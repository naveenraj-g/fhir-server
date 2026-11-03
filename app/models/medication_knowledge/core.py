from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeManufacturerReferenceType,
    MedicationKnowledgeQuantityComparator,
    MedicationKnowledgeStatus,
)
from app.models.shared import TenantAuditMixin


class MedicationKnowledgeModel(Base, TenantAuditMixin):
    """MedicationKnowledge resource ORM model (FHIR R4).
    https://www.hl7.org/fhir/R4/medicationknowledge.html
    """

    __tablename__ = "medication_knowledge"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_id = Column(
        BigInteger,
        Sequence(
            "medication_knowledge_pub_seq",
            start=600000,
            increment=1,
            metadata=Base.metadata,
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # code (0..1 CodeableConcept) — text flattened, codings in child table
    code_text = Column(String, nullable=True)

    # status (0..1 code)
    status = Column(
        Enum(
            MedicationKnowledgeStatus,
            name="medication_knowledge_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # manufacturer (0..1 Reference(Organization)) with identifier fallback (15 columns)
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(
        Enum(
            MedicationKnowledgeManufacturerReferenceType,
            name="medication_knowledge_manufacturer_reference_type",
        ),
        nullable=True,
    )
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_display = Column(String, nullable=True)

    manufacturer_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    manufacturer_identifier_type_system = Column(String, nullable=True)
    manufacturer_identifier_type_version = Column(String, nullable=True)
    manufacturer_identifier_type_code = Column(String, nullable=True)
    manufacturer_identifier_type_display = Column(String, nullable=True)
    manufacturer_identifier_type_user_selected = Column(Boolean, nullable=True)
    manufacturer_identifier_type_text = Column(String, nullable=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)
    manufacturer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    manufacturer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # doseForm (0..1 CodeableConcept) — text flattened, codings in child table
    dose_form_text = Column(String, nullable=True)

    # amount (0..1 SimpleQuantity)
    amount_value = Column(Numeric, nullable=True)
    amount_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
        ),
        nullable=True,
    )
    amount_unit = Column(String, nullable=True)
    amount_system = Column(String, nullable=True)
    amount_code = Column(String, nullable=True)

    # synonym (0..* string)
    synonym = Column(ARRAY(String), nullable=True)

    # preparationInstruction (0..1 markdown)
    preparation_instruction = Column(Text, nullable=True)

    # packaging (0..1 BackboneElement)
    packaging_type_text = Column(String, nullable=True)
    packaging_quantity_value = Column(Numeric, nullable=True)
    packaging_quantity_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    packaging_quantity_unit = Column(String, nullable=True)
    packaging_quantity_system = Column(String, nullable=True)
    packaging_quantity_code = Column(String, nullable=True)

    # Relationships
    code_codings = relationship(
        "MedicationKnowledgeCodeCoding",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    dose_form_codings = relationship(
        "MedicationKnowledgeDoseFormCoding",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    packaging_type_codings = relationship(
        "MedicationKnowledgePackagingTypeCoding",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    related_knowledge = relationship(
        "MedicationKnowledgeRelated",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    associated_medications = relationship(
        "MedicationKnowledgeAssociatedMedication",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    product_types = relationship(
        "MedicationKnowledgeProductType",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    monographs = relationship(
        "MedicationKnowledgeMonograph",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    ingredients = relationship(
        "MedicationKnowledgeIngredient",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    intended_routes = relationship(
        "MedicationKnowledgeIntendedRoute",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    costs = relationship(
        "MedicationKnowledgeCost",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    monitoring_programs = relationship(
        "MedicationKnowledgeMonitoringProgram",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    administration_guidelines = relationship(
        "MedicationKnowledgeAdminGuideline",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    medicine_classifications = relationship(
        "MedicationKnowledgeMedicineClassification",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    drug_characteristics = relationship(
        "MedicationKnowledgeDrugCharacteristic",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    contraindications = relationship(
        "MedicationKnowledgeContraindication",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    regulatory = relationship(
        "MedicationKnowledgeRegulatory",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    kinetics = relationship(
        "MedicationKnowledgeKinetics",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )

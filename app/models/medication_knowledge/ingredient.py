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
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeIngredientItemReferenceType,
    MedicationKnowledgeQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeIngredient(Base, TenantAuditMixin):
    """MedicationKnowledge.ingredient (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_ingredient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    # item[x] (1..1 choice: CodeableConcept | Reference(Substance | Medication))
    item_codeable_concept_text = Column(String, nullable=True)

    item_reference = Column(String, nullable=True)
    item_type = Column(
        Enum(
            MedicationKnowledgeIngredientItemReferenceType,
            name="medication_knowledge_ingredient_item_ref_type",
        ),
        nullable=True,
    )
    item_id = Column(BigInteger, nullable=True, index=True)
    item_display = Column(String, nullable=True)

    item_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    item_identifier_type_system = Column(String, nullable=True)
    item_identifier_type_version = Column(String, nullable=True)
    item_identifier_type_code = Column(String, nullable=True)
    item_identifier_type_display = Column(String, nullable=True)
    item_identifier_type_user_selected = Column(Boolean, nullable=True)
    item_identifier_type_text = Column(String, nullable=True)
    item_identifier_system = Column(String, nullable=True)
    item_identifier_value = Column(String, nullable=True)
    item_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    item_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # isActive (0..1 boolean)
    is_active = Column(Boolean, nullable=True)

    # strength (0..1 Ratio)
    strength_numerator_value = Column(Numeric, nullable=True)
    strength_numerator_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    strength_numerator_unit = Column(String, nullable=True)
    strength_numerator_system = Column(String, nullable=True)
    strength_numerator_code = Column(String, nullable=True)

    strength_denominator_value = Column(Numeric, nullable=True)
    strength_denominator_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    strength_denominator_unit = Column(String, nullable=True)
    strength_denominator_system = Column(String, nullable=True)
    strength_denominator_code = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="ingredients"
    )
    item_codings = relationship(
        "MedicationKnowledgeIngredientItemCoding",
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeIngredientItemCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.ingredient.itemCodeableConcept.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_ingredient_item_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_ingredient_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_ingredient.id"),
        nullable=False,
        index=True,
    )

    ingredient = relationship(
        "MedicationKnowledgeIngredient", back_populates="item_codings"
    )

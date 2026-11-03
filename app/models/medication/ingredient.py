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
from app.models.medication.enums import (
    MedicationIngredientItemReferenceType,
    MedicationQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationIngredient(Base, TenantAuditMixin):
    """Medication.ingredient (0..* BackboneElement) child table."""

    __tablename__ = "medication_ingredient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_pk = Column(
        BigInteger,
        ForeignKey("medication.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # item[x] (1..1 choice: CodeableConcept | Reference(Substance | Medication))
    item_codeable_concept_text = Column(String, nullable=True)

    item_reference = Column(String, nullable=True)
    item_type = Column(
        Enum(
            MedicationIngredientItemReferenceType,
            name="medication_ingredient_item_reference_type",
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

    # strength (0..1 Ratio: numerator Quantity, denominator Quantity)
    strength_numerator_value = Column(Numeric, nullable=True)
    strength_numerator_comparator = Column(
        Enum(
            MedicationQuantityComparator,
            name="medication_quantity_comparator",
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
            MedicationQuantityComparator,
            name="medication_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    strength_denominator_unit = Column(String, nullable=True)
    strength_denominator_system = Column(String, nullable=True)
    strength_denominator_code = Column(String, nullable=True)

    medication = relationship("MedicationModel", back_populates="ingredients")
    item_codings = relationship(
        "MedicationIngredientItemCoding",
        back_populates="ingredient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MedicationIngredientItemCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """Medication.ingredient.itemCodeableConcept.coding (0..* Coding) grandchild table."""

    __tablename__ = "medication_ingredient_item_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_ingredient_id = Column(
        BigInteger,
        ForeignKey("medication_ingredient.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ingredient = relationship("MedicationIngredient", back_populates="item_codings")

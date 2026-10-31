from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import (
    ActivityDefinitionQuantityComparator,
    ActivityDefinitionUseContextValueReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionUseContext(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.useContext (0..* UsageContext) child table."""

    __tablename__ = "activity_definition_use_context"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # value[x]: CodeableConcept — text flat here, coding[] is a grandchild table
    value_codeable_concept_text = Column(String, nullable=True)

    # value[x]: Quantity
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(
            ActivityDefinitionQuantityComparator,
            name="activity_definition_quantity_comparator",
        ),
        nullable=True,
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    # value[x]: Range
    value_range_low_value = Column(Numeric, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_low_system = Column(String, nullable=True)
    value_range_low_code = Column(String, nullable=True)
    value_range_high_value = Column(Numeric, nullable=True)
    value_range_high_unit = Column(String, nullable=True)
    value_range_high_system = Column(String, nullable=True)
    value_range_high_code = Column(String, nullable=True)

    # value[x]: Reference
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(
        Enum(
            ActivityDefinitionUseContextValueReferenceType,
            name="activity_definition_use_context_value_reference_type",
        ),
        nullable=True,
    )
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="use_contexts")
    value_codings = relationship(
        "ActivityDefinitionUseContextValueCoding",
        back_populates="use_context",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionUseContextValueCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.useContext.valueCodeableConcept.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_use_context_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_use_context_id = Column(
        BigInteger,
        ForeignKey("activity_definition_use_context.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use_context = relationship("ActivityDefinitionUseContext", back_populates="value_codings")

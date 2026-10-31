from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.plan_definition.enums import (
    PlanDefinitionQuantityComparator,
    PlanDefinitionUseContextValueReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionUseContext(TenantAuditMixin, Base):
    """PlanDefinition.useContext (0..* UsageContext) child table."""

    __tablename__ = "plan_definition_use_context"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # UsageContext.code (1..1 Coding)
    system = Column(String, nullable=True)
    version = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display = Column(String, nullable=True)
    user_selected = Column(Boolean, nullable=True)

    # UsageContext.value[x] variants
    value_codeable_concept_text = Column(String, nullable=True)

    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(
            PlanDefinitionQuantityComparator,
            name="plan_definition_quantity_comparator",
        ),
        nullable=True,
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    value_range_low_value = Column(Numeric, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_low_system = Column(String, nullable=True)
    value_range_low_code = Column(String, nullable=True)
    value_range_high_value = Column(Numeric, nullable=True)
    value_range_high_unit = Column(String, nullable=True)
    value_range_high_system = Column(String, nullable=True)
    value_range_high_code = Column(String, nullable=True)

    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(
        Enum(
            PlanDefinitionUseContextValueReferenceType,
            name="plan_definition_use_context_value_reference_type",
        ),
        nullable=True,
    )
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="use_contexts")
    value_codings = relationship(
        "PlanDefinitionUseContextValueCoding",
        back_populates="use_context",
        cascade="all, delete-orphan",
    )


class PlanDefinitionUseContextValueCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.useContext.valueCodeableConcept.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_use_context_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_use_context_id = Column(
        BigInteger,
        ForeignKey("plan_definition_use_context.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use_context = relationship("PlanDefinitionUseContext", back_populates="value_codings")

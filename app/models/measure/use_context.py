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
from app.models.measure.enums import (
    MeasureQuantityComparator,
    MeasureUseContextValueReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureUseContext(TenantAuditMixin, Base):
    """Measure.useContext (0..* UsageContext) child table."""

    __tablename__ = "measure_use_context"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
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
            MeasureQuantityComparator,
            name="measure_quantity_comparator",
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
            MeasureUseContextValueReferenceType,
            name="measure_use_context_value_reference_type",
        ),
        nullable=True,
    )
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)

    # value_reference.identifier fallback (11 columns)
    value_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    value_reference_identifier_type_system = Column(String, nullable=True)
    value_reference_identifier_type_version = Column(String, nullable=True)
    value_reference_identifier_type_code = Column(String, nullable=True)
    value_reference_identifier_type_display = Column(String, nullable=True)
    value_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    value_reference_identifier_type_text = Column(String, nullable=True)
    value_reference_identifier_system = Column(String, nullable=True)
    value_reference_identifier_value = Column(String, nullable=True)
    value_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    value_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    measure = relationship("MeasureModel", back_populates="use_contexts")
    value_codings = relationship(
        "MeasureUseContextValueCoding",
        back_populates="use_context",
        cascade="all, delete-orphan",
    )


class MeasureUseContextValueCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Measure.useContext.valueCodeableConcept.coding (0..* Coding) grandchild table."""

    __tablename__ = "measure_use_context_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_use_context_id = Column(
        BigInteger,
        ForeignKey("measure_use_context.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use_context = relationship("MeasureUseContext", back_populates="value_codings")

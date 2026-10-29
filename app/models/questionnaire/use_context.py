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
from app.models.questionnaire.enums import (
    QuestionnaireQuantityComparator,
    QuestionnaireUseContextValueReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# useContext (0..*) child table
# ---------------------------------------------------------------------------


class QuestionnaireUseContext(FhirCodingMixin, TenantAuditMixin, Base):
    """Questionnaire.useContext (0..* UsageContext) —
    https://www.hl7.org/fhir/R4/metadatatypes.html#UsageContext

    `code` (1..1 Coding) is this table's own FhirCodingMixin columns
    directly (no prefix — the mixin's bare system/version/code/display/
    user_selected ARE UsageContext.code's sub-fields; no collision with
    the value[x] columns below, which are all separately prefixed
    `value_*`).

    `value[x]` (1..1, choice of CodeableConcept | Quantity | Range |
    Reference) gets one column group per variant, all nullable — the
    mapper picks whichever group is populated. CodeableConcept's own
    `coding[]` is promoted to a real grandchild table
    (QuestionnaireUseContextValueCoding) per the CodeableConcept rule;
    Range is {low: Quantity, high: Quantity}, so it gets two Quantity
    column groups (`value_range_low_*`/`value_range_high_*`).
    """

    __tablename__ = "questionnaire_use_context"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )

    # value[x]: CodeableConcept — text flat here, coding[] is a grandchild table
    value_codeable_concept_text = Column(String, nullable=True)

    # value[x]: Quantity
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(
            QuestionnaireQuantityComparator,
            name="questionnaire_quantity_comparator",
            # Shared across 3 tables (here, item_enable_when, item_initial)
            # — every usage sets create_type=False; the migration creates
            # the type explicitly once. See CLAUDE.md's
            # organization_reference_type invariant for the same pattern.
            create_type=False,
        ),
        nullable=True,
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    # value[x]: Range = {low: SimpleQuantity, high: SimpleQuantity} — a
    # SimpleQuantity never carries a comparator (per its own R4 profile),
    # so no comparator column on either side.
    value_range_low_value = Column(Numeric, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_low_system = Column(String, nullable=True)
    value_range_low_code = Column(String, nullable=True)
    value_range_high_value = Column(Numeric, nullable=True)
    value_range_high_unit = Column(String, nullable=True)
    value_range_high_system = Column(String, nullable=True)
    value_range_high_code = Column(String, nullable=True)

    # value[x]: Reference(PlanDefinition|ResearchStudy|InsurancePlan|
    # HealthcareService|Group|Location|Organization) — closed 7-type set,
    # so a real Enum (not the Reference(Any) plain-String convention).
    value_reference_reference = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_type = Column(
        Enum(
            QuestionnaireUseContextValueReferenceType,
            name="questionnaire_use_context_value_reference_type",
        ),
        nullable=True,
    )
    value_reference_display = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="use_contexts")
    value_codeable_concept_codings = relationship(
        "QuestionnaireUseContextValueCoding",
        back_populates="use_context",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# useContext.value(CodeableConcept).coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireUseContextValueCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.useContext.value.coding (0..*), when
    value[x] is a CodeableConcept."""

    __tablename__ = "questionnaire_use_context_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_use_context_id = Column(
        BigInteger,
        ForeignKey("questionnaire_use_context.id"),
        nullable=False,
        index=True,
    )

    use_context = relationship(
        "QuestionnaireUseContext", back_populates="value_codeable_concept_codings"
    )

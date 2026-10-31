from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.plan_definition.enums import (
    PlanDefinitionActionCardinalityBehavior,
    PlanDefinitionActionGroupingBehavior,
    PlanDefinitionActionPrecheckBehavior,
    PlanDefinitionActionPriority,
    PlanDefinitionActionRequiredBehavior,
    PlanDefinitionActionSelectionBehavior,
    PlanDefinitionSubjectReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionAction(TenantAuditMixin, Base):
    """PlanDefinition.action (0..*, recursive BackboneElement) child table."""

    __tablename__ = "plan_definition_action"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_action_id = Column(
        BigInteger,
        ForeignKey("plan_definition_action.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    action_id_str = Column(String, nullable=True)  # Element.id for cross-references
    prefix = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    text_equivalent = Column(Text, nullable=True)
    priority = Column(
        Enum(PlanDefinitionActionPriority, name="plan_definition_action_priority"),
        nullable=True,
    )

    code = Column(JSONB, nullable=True)  # 0..* CodeableConcept
    reason = Column(JSONB, nullable=True)  # 0..* CodeableConcept
    documentation = Column(JSONB, nullable=True)  # 0..* RelatedArtifact
    goal_id = Column(ARRAY(String), nullable=True)  # 0..* id (references Goal.id)

    # subject[x]
    subject_codeable_concept_text = Column(String, nullable=True)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            PlanDefinitionSubjectReferenceType,
            name="plan_definition_action_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # trigger, condition, input, output, relatedAction
    trigger = Column(JSONB, nullable=True)  # 0..* TriggerDefinition
    condition = Column(JSONB, nullable=True)  # 0..* PlanDefinition.action.condition
    input = Column(JSONB, nullable=True)  # 0..* DataRequirement
    output = Column(JSONB, nullable=True)  # 0..* DataRequirement
    related_action = Column(JSONB, nullable=True)  # 0..* PlanDefinition.action.relatedAction

    # timing[x]
    timing_date_time = Column(DateTime(timezone=True), nullable=True)
    timing_age = Column(JSONB, nullable=True)  # Age/Quantity
    timing_period_start = Column(DateTime(timezone=True), nullable=True)
    timing_period_end = Column(DateTime(timezone=True), nullable=True)
    timing_duration = Column(JSONB, nullable=True)  # Duration/Quantity
    timing_range = Column(JSONB, nullable=True)  # Range
    timing_timing = Column(JSONB, nullable=True)  # Timing

    participant = Column(JSONB, nullable=True)  # 0..* PlanDefinition.action.participant
    type_text = Column(String, nullable=True)

    grouping_behavior = Column(
        Enum(
            PlanDefinitionActionGroupingBehavior,
            name="plan_definition_action_grouping_behavior",
        ),
        nullable=True,
    )
    selection_behavior = Column(
        Enum(
            PlanDefinitionActionSelectionBehavior,
            name="plan_definition_action_selection_behavior",
        ),
        nullable=True,
    )
    required_behavior = Column(
        Enum(
            PlanDefinitionActionRequiredBehavior,
            name="plan_definition_action_required_behavior",
        ),
        nullable=True,
    )
    precheck_behavior = Column(
        Enum(
            PlanDefinitionActionPrecheckBehavior,
            name="plan_definition_action_precheck_behavior",
        ),
        nullable=True,
    )
    cardinality_behavior = Column(
        Enum(
            PlanDefinitionActionCardinalityBehavior,
            name="plan_definition_action_cardinality_behavior",
        ),
        nullable=True,
    )

    definition_canonical = Column(String, nullable=True)
    definition_uri = Column(String, nullable=True)
    transform = Column(String, nullable=True)
    dynamic_value = Column(JSONB, nullable=True)  # 0..* PlanDefinition.action.dynamicValue

    plan_definition = relationship("PlanDefinitionModel", back_populates="actions")
    type_codings = relationship(
        "PlanDefinitionActionTypeCoding",
        back_populates="action",
        cascade="all, delete-orphan",
    )


class PlanDefinitionActionTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.action.type.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_action_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    action_id = Column(
        BigInteger,
        ForeignKey("plan_definition_action.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = relationship("PlanDefinitionAction", back_populates="type_codings")

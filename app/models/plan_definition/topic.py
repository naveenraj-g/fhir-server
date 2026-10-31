from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionTopic(TenantAuditMixin, Base):
    """PlanDefinition.topic (0..* CodeableConcept) child table."""

    __tablename__ = "plan_definition_topic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="topics")
    codings = relationship(
        "PlanDefinitionTopicCoding",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class PlanDefinitionTopicCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.topic.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_topic_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_topic_id = Column(
        BigInteger,
        ForeignKey("plan_definition_topic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic = relationship("PlanDefinitionTopic", back_populates="codings")

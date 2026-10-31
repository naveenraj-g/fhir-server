from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionTopic(TenantAuditMixin, Base):
    """ActivityDefinition.topic (0..* CodeableConcept) child table."""

    __tablename__ = "activity_definition_topic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="topics")
    codings = relationship(
        "ActivityDefinitionTopicCoding",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionTopicCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.topic.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_topic_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_topic_id = Column(
        BigInteger,
        ForeignKey("activity_definition_topic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic = relationship("ActivityDefinitionTopic", back_populates="codings")

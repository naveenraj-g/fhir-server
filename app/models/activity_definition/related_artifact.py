from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import ActivityDefinitionRelatedArtifactType
from app.models.shared import TenantAuditMixin


class ActivityDefinitionRelatedArtifact(TenantAuditMixin, Base):
    """ActivityDefinition.relatedArtifact (0..* RelatedArtifact) child table."""

    __tablename__ = "activity_definition_related_artifact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type = Column(
        Enum(
            ActivityDefinitionRelatedArtifactType,
            name="activity_definition_related_artifact_type",
        ),
        nullable=False,
    )
    label = Column(String, nullable=True)
    display = Column(String, nullable=True)
    citation = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    document = Column(JSONB, nullable=True)
    resource = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="related_artifacts")

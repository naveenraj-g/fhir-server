from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.plan_definition.enums import PlanDefinitionRelatedArtifactType
from app.models.shared import TenantAuditMixin


class PlanDefinitionRelatedArtifact(TenantAuditMixin, Base):
    """PlanDefinition.relatedArtifact (0..* RelatedArtifact) child table."""

    __tablename__ = "plan_definition_related_artifact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type = Column(
        Enum(
            PlanDefinitionRelatedArtifactType,
            name="plan_definition_related_artifact_type",
        ),
        nullable=False,
    )
    label = Column(String, nullable=True)
    display = Column(String, nullable=True)
    citation = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    document = Column(JSONB, nullable=True)
    resource = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="related_artifacts")

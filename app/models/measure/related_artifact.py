from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.measure.enums import MeasureRelatedArtifactType
from app.models.shared import TenantAuditMixin


class MeasureRelatedArtifact(TenantAuditMixin, Base):
    """Measure.relatedArtifact (0..* RelatedArtifact) child table."""

    __tablename__ = "measure_related_artifact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type = Column(
        Enum(
            MeasureRelatedArtifactType,
            name="measure_related_artifact_type",
        ),
        nullable=False,
    )
    label = Column(String, nullable=True)
    display = Column(String, nullable=True)
    citation = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    document = Column(JSONB, nullable=True)
    resource = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="related_artifacts")

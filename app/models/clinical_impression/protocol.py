from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin


class ClinicalImpressionProtocolModel(TenantAuditMixin, Base):
    """ClinicalImpression.protocol (0..* uri) child table."""

    __tablename__ = "clinical_impression_protocol"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    uri = Column(String, nullable=False)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="protocols"
    )

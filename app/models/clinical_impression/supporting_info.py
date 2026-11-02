from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class ClinicalImpressionSupportingInfoModel(TenantAuditMixin, Base):
    """ClinicalImpression.supportingInfo (0..* Reference(Any)) child table."""

    __tablename__ = "clinical_impression_supporting_info"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    display = Column(String, nullable=True)

    # fallback (11 columns)
    identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_type_system = Column(String, nullable=True)
    identifier_type_version = Column(String, nullable=True)
    identifier_type_code = Column(String, nullable=True)
    identifier_type_display = Column(String, nullable=True)
    identifier_type_user_selected = Column(Boolean, nullable=True)
    identifier_type_text = Column(String, nullable=True)
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="supporting_info"
    )

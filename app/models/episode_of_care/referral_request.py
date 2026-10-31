from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.episode_of_care.enums import EpisodeOfCareReferralRequestReferenceType
from app.models.shared import TenantAuditMixin


class EpisodeOfCareReferralRequest(TenantAuditMixin, Base):
    """EpisodeOfCare.referralRequest (0..*) Reference(ServiceRequest) child table."""

    __tablename__ = "episode_of_care_referral_request"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            EpisodeOfCareReferralRequestReferenceType,
            name="episode_of_care_referral_request_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="referral_requests")

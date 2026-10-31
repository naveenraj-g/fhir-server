from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.episode_of_care.enums import EpisodeOfCareStatus
from app.models.shared import TenantAuditMixin


class EpisodeOfCareStatusHistory(TenantAuditMixin, Base):
    """EpisodeOfCare.statusHistory (0..*) child table."""

    __tablename__ = "episode_of_care_status_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )

    status = Column(
        Enum(
            EpisodeOfCareStatus,
            name="episode_of_care_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="status_history")

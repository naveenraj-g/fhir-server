from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class EpisodeOfCareType(TenantAuditMixin, Base):
    """EpisodeOfCare.type (0..*) CodeableConcept child table."""

    __tablename__ = "episode_of_care_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="types")
    codings = relationship(
        "EpisodeOfCareTypeCoding",
        back_populates="type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EpisodeOfCareTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """EpisodeOfCare.type.coding (0..*) grandchild table."""

    __tablename__ = "episode_of_care_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_id = Column(
        BigInteger,
        ForeignKey("episode_of_care_type.id"),
        nullable=False,
        index=True,
    )

    type = relationship("EpisodeOfCareType", back_populates="codings")

from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceCategory (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ScheduleServiceCategory(TenantAuditMixin, Base):
    """serviceCategory[] — high-level category of service. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (ScheduleServiceCategoryCoding, below) rather than
    a single flattened coding — same reasoning as
    HealthcareServiceCategory's own coding[] promotion."""

    __tablename__ = "schedule_service_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_pk = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    schedule = relationship("ScheduleModel", back_populates="service_categories")
    codings = relationship(
        "ScheduleServiceCategoryCoding",
        back_populates="service_category",
        cascade="all, delete-orphan",
    )


class ScheduleServiceCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Schedule.serviceCategory.coding (0..*)."""

    __tablename__ = "schedule_service_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_service_category_id = Column(
        BigInteger,
        ForeignKey("schedule_service_category.id"),
        nullable=False,
        index=True,
    )

    service_category = relationship(
        "ScheduleServiceCategory", back_populates="codings"
    )

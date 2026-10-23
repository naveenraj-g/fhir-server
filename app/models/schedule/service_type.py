from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceType (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ScheduleServiceType(TenantAuditMixin, Base):
    """serviceType[] — specific type of service. `text` stays flattened
    (sibling of coding[], not part of it); `coding[]` itself is a real 0..*
    child table (ScheduleServiceTypeCoding, below) rather than a single
    flattened coding — same reasoning as HealthcareServiceType's own
    coding[] promotion."""

    __tablename__ = "schedule_service_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_pk = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    schedule = relationship("ScheduleModel", back_populates="service_types")
    codings = relationship(
        "ScheduleServiceTypeCoding",
        back_populates="service_type",
        cascade="all, delete-orphan",
    )


class ScheduleServiceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Schedule.serviceType.coding (0..*)."""

    __tablename__ = "schedule_service_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_service_type_id = Column(
        BigInteger, ForeignKey("schedule_service_type.id"), nullable=False, index=True
    )

    service_type = relationship("ScheduleServiceType", back_populates="codings")

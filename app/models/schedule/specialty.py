from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ScheduleSpecialty(TenantAuditMixin, Base):
    """specialty[] — the specialty of a practitioner that would be
    required to perform the service requested in this schedule. `text`
    stays flattened (sibling of coding[], not part of it); `coding[]`
    itself is a real 0..* child table (ScheduleSpecialtyCoding, below)
    rather than a single flattened coding — same reasoning as
    PractitionerRoleSpecialty's own coding[] promotion."""

    __tablename__ = "schedule_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_pk = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    schedule = relationship("ScheduleModel", back_populates="specialties")
    codings = relationship(
        "ScheduleSpecialtyCoding",
        back_populates="specialty",
        cascade="all, delete-orphan",
    )


class ScheduleSpecialtyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Schedule.specialty.coding (0..*)."""

    __tablename__ = "schedule_specialty_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_specialty_id = Column(
        BigInteger, ForeignKey("schedule_specialty.id"), nullable=False, index=True
    )

    specialty = relationship("ScheduleSpecialty", back_populates="codings")

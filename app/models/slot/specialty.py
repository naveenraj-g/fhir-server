from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class SlotSpecialty(TenantAuditMixin, Base):
    """specialty[] — the specialty of a practitioner that would be
    required to perform the service requested in this slot. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is
    a real 0..* child table (SlotSpecialtyCoding, below) rather than a
    single flattened coding — same reasoning as ScheduleSpecialty's own
    coding[] promotion."""

    __tablename__ = "slot_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    slot = relationship("SlotModel", back_populates="specialties")
    codings = relationship(
        "SlotSpecialtyCoding",
        back_populates="specialty",
        cascade="all, delete-orphan",
    )


class SlotSpecialtyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Slot.specialty.coding (0..*)."""

    __tablename__ = "slot_specialty_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_specialty_id = Column(
        BigInteger, ForeignKey("slot_specialty.id"), nullable=False, index=True
    )

    specialty = relationship("SlotSpecialty", back_populates="codings")

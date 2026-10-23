from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceType (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class SlotServiceType(TenantAuditMixin, Base):
    """serviceType[] — the type of appointments that can be booked into
    this slot. `text` stays flattened (sibling of coding[], not part of
    it); `coding[]` itself is a real 0..* child table
    (SlotServiceTypeCoding, below) rather than a single flattened coding —
    same reasoning as ScheduleServiceType's own coding[] promotion."""

    __tablename__ = "slot_service_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    slot = relationship("SlotModel", back_populates="service_types")
    codings = relationship(
        "SlotServiceTypeCoding",
        back_populates="service_type",
        cascade="all, delete-orphan",
    )


class SlotServiceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Slot.serviceType.coding (0..*)."""

    __tablename__ = "slot_service_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_service_type_id = Column(
        BigInteger, ForeignKey("slot_service_type.id"), nullable=False, index=True
    )

    service_type = relationship("SlotServiceType", back_populates="codings")

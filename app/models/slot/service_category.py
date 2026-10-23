from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceCategory (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class SlotServiceCategory(TenantAuditMixin, Base):
    """serviceCategory[] — a broad categorization of the service for this
    slot. `text` stays flattened (sibling of coding[], not part of it);
    `coding[]` itself is a real 0..* child table (SlotServiceCategoryCoding,
    below) rather than a single flattened coding — same reasoning as
    ScheduleServiceCategory's own coding[] promotion."""

    __tablename__ = "slot_service_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    slot = relationship("SlotModel", back_populates="service_categories")
    codings = relationship(
        "SlotServiceCategoryCoding",
        back_populates="service_category",
        cascade="all, delete-orphan",
    )


class SlotServiceCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Slot.serviceCategory.coding (0..*)."""

    __tablename__ = "slot_service_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_service_category_id = Column(
        BigInteger, ForeignKey("slot_service_category.id"), nullable=False, index=True
    )

    service_category = relationship("SlotServiceCategory", back_populates="codings")

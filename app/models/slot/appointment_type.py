from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# appointmentType.coding (0..*) child table
# ---------------------------------------------------------------------------


class SlotAppointmentTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Slot.appointmentType.coding (0..*).

    appointmentType itself is a 0..1 CodeableConcept living directly on
    the main `slot` row (there's no wrapping sub-resource table the way
    Identifier.type or HealthcareServiceEligibility.code have one) — its
    `text` sibling field is flattened onto SlotModel
    (`appointment_type_text`), but `coding[]` still gets this dedicated
    child table, FK'd straight to `slot.id`, since a CodeableConcept's
    coding[] is always 0..* regardless of the containing field's own
    cardinality — same reasoning as every other coding[] promotion in
    this codebase.
    """

    __tablename__ = "slot_appointment_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)

    slot = relationship("SlotModel", back_populates="appointment_type_codings")

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# serviceType.coding (0..*) child table
# ---------------------------------------------------------------------------


class EncounterServiceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.serviceType.coding (0..*).

    serviceType itself is a 0..1 CodeableConcept living directly on the
    main `encounter` row — its `text` sibling field is flattened onto
    EncounterModel (`service_type_text`), but `coding[]` still gets this
    dedicated child table, FK'd straight to `encounter.id` — same
    reasoning as SlotAppointmentTypeCoding's promotion."""

    __tablename__ = "encounter_service_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    encounter = relationship("EncounterModel", back_populates="service_type_codings")

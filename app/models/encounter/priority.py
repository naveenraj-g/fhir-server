from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# priority.coding (0..*) child table
# ---------------------------------------------------------------------------


class EncounterPriorityCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.priority.coding (0..*).

    priority itself is a 0..1 CodeableConcept living directly on the main
    `encounter` row — its `text` sibling field is flattened onto
    EncounterModel (`priority_text`), but `coding[]` still gets this
    dedicated child table, FK'd straight to `encounter.id`."""

    __tablename__ = "encounter_priority_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    encounter = relationship("EncounterModel", back_populates="priority_codings")

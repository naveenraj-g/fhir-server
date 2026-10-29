from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# classHistory (0..*) child table
# ---------------------------------------------------------------------------


class EncounterClassHistory(FhirCodingMixin, TenantAuditMixin, Base):
    """classHistory[] — the class history permits the tracking of the
    encounters transitions without needing to go through the resource
    history. `class` (1..1 Coding, not CodeableConcept) is flattened
    directly onto this row via FhirCodingMixin, `class_`-prefixed — same
    treatment as EncounterModel.class itself. `period` (1..1) is
    flattened to period_start/period_end."""

    __tablename__ = "encounter_class_history"

    _coding_prefix = "class_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="class_history")

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import EncounterStatus
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# statusHistory (0..*) child table
# ---------------------------------------------------------------------------


class EncounterStatusHistory(TenantAuditMixin, Base):
    """statusHistory[] — the status history permits the encounter
    resource to contain the status history without needing to read
    through the historical versions of the resource, or even have the
    server store them. `status` and `period` are both 1..1 within this
    BackboneElement (not enforced at the DB layer — see OrganizationModel's
    docstring for why no DB-level CHECK constraints exist in this
    codebase)."""

    __tablename__ = "encounter_status_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    status = Column(
        Enum(EncounterStatus, name="encounter_status", create_type=False), nullable=False
    )
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="status_history")

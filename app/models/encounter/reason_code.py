from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class EncounterReasonCode(TenantAuditMixin, Base):
    """reasonCode[] — reason the encounter takes place, expressed as a
    code. `text` stays flattened (sibling of coding[], not part of it);
    `coding[]` itself is a real 0..* child table
    (EncounterReasonCodeCoding, below)."""

    __tablename__ = "encounter_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_codes")
    codings = relationship(
        "EncounterReasonCodeCoding", back_populates="reason_code", cascade="all, delete-orphan"
    )


class EncounterReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.reasonCode.coding (0..*)."""

    __tablename__ = "encounter_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_reason_code_id = Column(
        BigInteger, ForeignKey("encounter_reason_code.id"), nullable=False, index=True
    )

    reason_code = relationship("EncounterReasonCode", back_populates="codings")

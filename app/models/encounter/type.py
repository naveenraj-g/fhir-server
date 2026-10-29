from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# type (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class EncounterType(TenantAuditMixin, Base):
    """type[] — specific type of encounter (e.g. e-mail consultation,
    surgical day-care, ...). `text` stays flattened (sibling of coding[],
    not part of it); `coding[]` itself is a real 0..* child table
    (EncounterTypeCoding, below) — same reasoning as every other
    CodeableConcept-list promotion in this codebase."""

    __tablename__ = "encounter_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="types")
    codings = relationship(
        "EncounterTypeCoding", back_populates="type", cascade="all, delete-orphan"
    )


class EncounterTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.type.coding (0..*)."""

    __tablename__ = "encounter_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_type_id = Column(
        BigInteger, ForeignKey("encounter_type.id"), nullable=False, index=True
    )

    type = relationship("EncounterType", back_populates="codings")

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import EncounterLocationReferenceType, EncounterLocationStatus
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# location (0..*) BackboneElement child table
# ---------------------------------------------------------------------------
# Named EncounterLocationRow, not EncounterLocation, to keep it visually
# distinct from app.models.location.LocationModel in every import site —
# same reasoning as naming the reference-list table AppointmentSlot
# (mirrors the FHIR field name) rather than something that reads as if it
# were LocationModel itself.


class EncounterLocationRow(TenantAuditMixin, Base):
    """location[] — list of locations where the patient has been during
    this encounter.

    `location` (1..1 Reference(Location)) is required per spec but
    modeled as nullable here, same as every other flattened Reference
    field — Location IS a modeled resource in this system, so this
    reference's existence check is actually enforced.

    `physicalType` (0..1 CodeableConcept) — text flattened, coding[]
    promoted to a dedicated grandchild table
    (EncounterLocationPhysicalTypeCoding, below)."""

    __tablename__ = "encounter_location"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    # ── location (1..1 Reference(Location)) ──────────────────────────────

    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(EncounterLocationReferenceType, name="encounter_location_reference_type"),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    location_identifier_use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    location_identifier_type_system = Column(String, nullable=True)
    location_identifier_type_version = Column(String, nullable=True)
    location_identifier_type_code = Column(String, nullable=True)
    location_identifier_type_display = Column(String, nullable=True)
    location_identifier_type_text = Column(String, nullable=True)
    location_identifier_type_user_selected = Column(Boolean, nullable=True)
    location_identifier_system = Column(String, nullable=True)
    location_identifier_value = Column(String, nullable=True)
    location_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    location_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── status (0..1 code) ────────────────────────────────────────────────

    status = Column(
        Enum(EncounterLocationStatus, name="encounter_location_status"), nullable=True
    )

    # ── physicalType (0..1 CodeableConcept) ───────────────────────────────

    physical_type_text = Column(String, nullable=True)

    # ── period (0..1 Period) ──────────────────────────────────────────────

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="locations")
    physical_type_codings = relationship(
        "EncounterLocationPhysicalTypeCoding",
        back_populates="location_row",
        cascade="all, delete-orphan",
    )


class EncounterLocationPhysicalTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.location.physicalType.coding (0..*)."""

    __tablename__ = "encounter_location_physical_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_location_id = Column(
        BigInteger, ForeignKey("encounter_location.id"), nullable=False, index=True
    )

    location_row = relationship("EncounterLocationRow", back_populates="physical_type_codings")

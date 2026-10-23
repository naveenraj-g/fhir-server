from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# identifier (0..*) child table
# ---------------------------------------------------------------------------


class SlotIdentifier(TenantAuditMixin, Base):
    """identifier[] — external business identifiers for this slot.

    type_text stays flattened (sibling of coding[], not part of it);
    type's coding[] is a real 0..* child table (SlotIdentifierTypeCoding,
    below) rather than a single flattened coding — same reasoning as
    ScheduleIdentifier's own type.coding[] promotion."""

    __tablename__ = "slot_identifier"
    __table_args__ = (
        UniqueConstraint("system", "value", name="uq_slot_identifier_system_value"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named slot_pk, not slot_id, so it can never be
    # confused with SlotModel.slot_id (the public, FHIR-facing sequence
    # ID) — same reasoning as Schedule's schedule_pk.
    slot_pk = Column(BigInteger, ForeignKey("slot.id"), nullable=False, index=True)

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    # assigner.identifier (0..1 Identifier) — logical-reference fallback
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    assigner_identifier_type_system = Column(String, nullable=True)
    assigner_identifier_type_version = Column(String, nullable=True)
    assigner_identifier_type_code = Column(String, nullable=True)
    assigner_identifier_type_display = Column(String, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)
    assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    slot = relationship("SlotModel", back_populates="identifiers")
    type_codings = relationship(
        "SlotIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class SlotIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Slot.identifier.type.coding (0..*)."""

    __tablename__ = "slot_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slot_identifier_id = Column(
        BigInteger, ForeignKey("slot_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("SlotIdentifier", back_populates="type_codings")

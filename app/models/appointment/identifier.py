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


class AppointmentIdentifier(TenantAuditMixin, Base):
    """identifier[] — external business identifiers for this appointment.

    type_text stays flattened (sibling of coding[], not part of it);
    type's coding[] is a real 0..* child table (AppointmentIdentifierTypeCoding,
    below) rather than a single flattened coding — same reasoning as
    SlotIdentifier's own type.coding[] promotion."""

    __tablename__ = "appointment_identifier"
    __table_args__ = (
        UniqueConstraint(
            "system", "value", name="uq_appointment_identifier_system_value"
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named appointment_pk, not appointment_id, so it can
    # never be confused with AppointmentModel.appointment_id (the public,
    # FHIR-facing sequence ID) — same reasoning as Slot's slot_pk.
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    #
    # assigner_reference is the raw literal string exactly as received —
    # see OrganizationIdentifier.assigner_reference for the full reasoning.
    assigner_reference = Column(String, nullable=True)
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

    appointment = relationship("AppointmentModel", back_populates="identifiers")
    type_codings = relationship(
        "AppointmentIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class AppointmentIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Appointment.identifier.type.coding (0..*)."""

    __tablename__ = "appointment_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_identifier_id = Column(
        BigInteger, ForeignKey("appointment_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("AppointmentIdentifier", back_populates="type_codings")

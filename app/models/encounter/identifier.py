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
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# identifier (0..*) child table
# ---------------------------------------------------------------------------


class EncounterIdentifier(TenantAuditMixin, Base):
    """identifier[] — external business identifiers for this encounter.

    type_text stays flattened (sibling of coding[], not part of it);
    type's coding[] is a real 0..* child table
    (EncounterIdentifierTypeCoding, below) rather than a single flattened
    coding — same reasoning as AppointmentIdentifier's own type.coding[]
    promotion.

    No UniqueConstraint on (system, value) and no DB-level CHECK
    constraints — same reasoning as OrganizationIdentifier, see
    app/models/organization/identifier.py's docstring."""

    __tablename__ = "encounter_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named encounter_pk, not encounter_id, so it can
    # never be confused with EncounterModel.encounter_id (the public,
    # FHIR-facing sequence ID) — same reasoning as Appointment's
    # appointment_pk.
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

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

    encounter = relationship("EncounterModel", back_populates="identifiers")
    type_codings = relationship(
        "EncounterIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class EncounterIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.identifier.type.coding (0..*)."""

    __tablename__ = "encounter_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_identifier_id = Column(
        BigInteger, ForeignKey("encounter_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("EncounterIdentifier", back_populates="type_codings")

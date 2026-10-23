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


class PractitionerIdentifier(TenantAuditMixin, Base):
    """No UniqueConstraint on (system, value) and no DB-level CHECK
    constraints — same reasoning as OrganizationIdentifier, see
    app/models/organization/identifier.py's docstring."""

    __tablename__ = "practitioner_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named practitioner_pk, not practitioner_id, so it can
    # never be confused with PractitionerModel.practitioner_id (the public,
    # FHIR-facing sequence ID) — same reasoning as Organization's
    # organization_pk.
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    # Identifier.type (0..1 CodeableConcept) — type_text stays flattened
    # (sibling of coding[], not part of it); type's coding[] is a real 0..*
    # child table (PractitionerIdentifierTypeCoding) — see
    # app/models/organization/identifier.py for the full reasoning.
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization)) — flattened, no FK, stores the
    # PUBLIC organization_id — see app/models/organization/identifier.py's
    # assigner_* columns for the full reasoning.
    assigner_reference = Column(String, nullable=True)
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
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

    practitioner = relationship("PractitionerModel", back_populates="identifiers")
    type_codings = relationship(
        "PractitionerIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class PractitionerIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Practitioner.identifier.type.coding (0..*)."""

    __tablename__ = "practitioner_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_identifier_id = Column(
        BigInteger, ForeignKey("practitioner_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("PractitionerIdentifier", back_populates="type_codings")

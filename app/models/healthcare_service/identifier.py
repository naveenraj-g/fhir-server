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


class HealthcareServiceIdentifier(TenantAuditMixin, Base):
    """identifier[] — external business identifiers for this service.

    type_text stays flattened (sibling of coding[], not part of it);
    type's coding[] is a real 0..* child table
    (HealthcareServiceIdentifierTypeCoding, below) rather than a single
    flattened coding — same reasoning as OrganizationIdentifier's own
    type.coding[] promotion."""

    __tablename__ = "healthcare_service_identifier"
    __table_args__ = (
        UniqueConstraint(
            "system", "value", name="uq_healthcare_service_identifier_system_value"
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named healthcare_service_pk, not healthcare_service_id,
    # so it can never be confused with HealthcareServiceModel.healthcare_service_id
    # (the public, FHIR-facing sequence ID) — same reasoning as Organization's
    # organization_pk.
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    # Identifier.type (0..1 CodeableConcept) — type_text is the
    # CodeableConcept's own field; type's coding[] is the real 0..* list,
    # via the type_codings relationship below.
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization)) — resolved reference (public ID,
    # no FK/relationship — see HealthcareServiceModel.provided_by_*)
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

    # assigner.identifier (0..1 Identifier) — logical-reference fallback for
    # when the assigning organization isn't a resource in this system
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

    # Audit columns come from TenantAuditMixin above.

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="identifiers"
    )
    type_codings = relationship(
        "HealthcareServiceIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class HealthcareServiceIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.identifier.type.coding (0..*)."""

    __tablename__ = "healthcare_service_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_identifier_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_identifier.id"),
        nullable=False,
        index=True,
    )

    identifier = relationship(
        "HealthcareServiceIdentifier", back_populates="type_codings"
    )

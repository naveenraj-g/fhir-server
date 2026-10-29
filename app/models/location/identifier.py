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
# identifier (0..*) Identifier child table
# ---------------------------------------------------------------------------


class LocationIdentifier(TenantAuditMixin, Base):
    """Location.identifier[] — unique codes/numbers identifying the location.

    Same shape as OrganizationIdentifier: type_text stays flattened (sibling
    of coding[], not part of it); type's coding[] is a real 0..* child table
    (LocationIdentifierTypeCoding, below) rather than a single flattened
    coding — same org-custom-code-plus-standard-crosswalk reasoning as
    OrganizationIdentifier's own type.coding[] promotion. Identifier.assigner
    is a resolved Reference(Organization) with an Identifier logical-
    reference fallback for assigners that aren't resources in this system —
    that fallback's own `.type` stays flattened/one-to-one (it's a
    reference's logical-identifier fallback, not a first-class identifier of
    this resource), matching OrganizationIdentifier's assigner_identifier_type_*.

    No UniqueConstraint on (system, value) and no DB-level CHECK
    constraints — same reasoning as OrganizationIdentifier, see
    app/models/organization/identifier.py's docstring.
    """

    __tablename__ = "location_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)

    # Identifier.type (0..1 CodeableConcept) — type_text is the
    # CodeableConcept's own field; type_coding is the real 0..* coding list,
    # via the type_codings relationship below.
    type_text = Column(String, nullable=True)

    # system/value are 0..1 on Identifier — not required even here, same
    # as OrganizationIdentifier/PractitionerIdentifier.
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization)) — resolved reference. Stores the
    # internal organization.id PK; the public ID is read back through the
    # repository, matching OrganizationIdentifier.assigner_*.
    #
    # assigner_reference is the raw literal string exactly as received —
    # relative or an absolute URL to another system entirely — kept
    # regardless of whether it resolves locally. See
    # OrganizationIdentifier.assigner_reference for the full reasoning.
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

    location = relationship("LocationModel", back_populates="identifiers")
    type_codings = relationship(
        "LocationIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class LocationIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Location.identifier.type.coding (0..*)."""

    __tablename__ = "location_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_identifier_id = Column(
        BigInteger, ForeignKey("location_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("LocationIdentifier", back_populates="type_codings")

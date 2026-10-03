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


class OrganizationIdentifier(TenantAuditMixin, Base):
    """No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness at all — it's a local/profile decision, not a
    base-resource rule — and a global constraint here was a real
    cross-tenant bug (two different orgs could never share an identifier
    value under the same system). Enforce uniqueness at the profile level
    if/when a specific deployment needs it.

    No DB-level CHECK constraints either — see OrganizationModel's
    docstring (core.py) for why every R4 rule, including the Reference-shape
    rule that would apply to `assigner` here, is enforced by the FHIR
    validator layer instead."""

    __tablename__ = "organization_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named organization_pk, not organization_id,
    # specifically so it can never be confused with
    # OrganizationModel.organization_id (the public, FHIR-facing sequence
    # ID) — same column name, two unrelated meanings otherwise.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    # Identifier.type (0..1 CodeableConcept) — type_text stays flattened
    # (sibling of coding[], not part of it); type's coding[] is a real 0..*
    # child table (OrganizationIdentifierTypeCoding), not a single flattened
    # coding — an org may need its own custom identifier-type code AND a
    # crosswalk to a standard one at the same time. NOTE: this is distinct
    # from assigner_identifier_type_* below (the *assigner's own* Identifier
    # fallback's .type) — that one stays flattened/one-to-one, since it's a
    # reference's logical-identifier fallback, not a first-class identifier
    # of this resource.
    type_text = Column(String, nullable=True)
    # system/value are 0..1 on Identifier — not required even here.
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization)) — Reference is
    # {reference, type, identifier, display}, all four independently 0..1.
    # assigner_reference is the raw literal string exactly as received
    # (relative "Organization/190004", or an absolute URL to another system
    # entirely) — kept regardless of whether we can resolve it. An external
    # absolute URL to an org we don't have locally has nowhere else to live:
    # it isn't assigner_id (nothing to resolve to) and it isn't
    # assigner_identifier_* (that's a structured business Identifier, not a
    # URL — a sender can populate either, both, or neither, independently).
    assigner_reference = Column(String, nullable=True)
    # Deliberately NOT a ForeignKey — see core.py's partof_id for the full
    # architecture reasoning. Stores the PUBLIC organization_id value, not
    # an internal PK.
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

    organization = relationship("OrganizationModel", back_populates="identifiers")
    type_codings = relationship(
        "OrganizationIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class OrganizationIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Organization.identifier.type.coding (0..*)."""

    __tablename__ = "organization_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_identifier_id = Column(
        BigInteger, ForeignKey("organization_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("OrganizationIdentifier", back_populates="type_codings")

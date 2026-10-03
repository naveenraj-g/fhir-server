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
from app.models.enums import IdentifierUse
from app.models.organization.enums import OrganizationEndpointReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# endpoint (0..*) Reference(Endpoint) child table
# ---------------------------------------------------------------------------


class OrganizationEndpoint(TenantAuditMixin, Base):
    """No UniqueConstraint on (organization_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same endpoint twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint.

    No DB-level CHECK constraints either — the same Reference-shape rules
    that apply to core.py's partOf apply here too, and are enforced by the
    FHIR validator layer instead — see OrganizationModel's docstring
    (core.py) for why."""

    __tablename__ = "organization_endpoint"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )

    # The raw literal string as received — see core.py's partof_reference
    # for the full reasoning (an absolute URL to another system's Endpoint
    # has nowhere else to live).
    reference_reference = Column(String, nullable=True)
    # Endpoint isn't modeled locally — deliberately never a real FK, since
    # there's no local table to reference at all (not a polymorphism
    # judgment call the way partOf/assigner are).
    reference_id = Column(BigInteger, nullable=True, index=True)
    # Always "Endpoint" — independent Reference.type element, same reasoning
    # as partof_type/assigner_type, not a polymorphism discriminator.
    reference_type = Column(
        Enum(OrganizationEndpointReferenceType, name="organization_endpoint_ref_type"),
        nullable=True,
    )
    reference_display = Column(String, nullable=True)

    # endpoint.identifier (0..1 Identifier) — logical-reference fallback for
    # when the endpoint isn't a resource in this system (Endpoint isn't a
    # modeled resource here at all, so this is the only way to record one)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("OrganizationModel", back_populates="endpoints")

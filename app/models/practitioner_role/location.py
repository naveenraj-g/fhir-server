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
from app.models.practitioner_role.enums import PractitionerRoleLocationReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# location (0..*) Reference(Location) child table
# ---------------------------------------------------------------------------


class PractitionerRoleLocation(TenantAuditMixin, Base):
    """location[] — the location(s) at which this practitioner provides
    care.

    reference_id stores Location's PUBLIC location_id — no FK/relationship,
    same flattened-reference convention as PractitionerRoleModel.practitioner_*
    and HealthcareServiceLocation.

    No UniqueConstraint on (practitioner_role_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same reference twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint.
    """

    __tablename__ = "practitioner_role_location"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            PractitionerRoleLocationReferenceType,
            name="practitioner_role_location_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # location.identifier (0..1 Identifier) — logical-reference fallback for
    # a location held in another system
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

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="locations"
    )

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
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# supportingInformation (0..*) Reference(Any) child table
# ---------------------------------------------------------------------------


class AppointmentSupportingInformation(TenantAuditMixin, Base):
    """supportingInformation[] — additional information to support the
    appointment, provided by the requester/referrer.

    Unlike every other Reference field on this resource, FHIR R4 allows
    *any* resource type as the target here (`Reference(Any)`) — there is no
    fixed, enumerable set of allowed types to validate against the way
    reasonReference/basedOn/slot/participant.actor each have. `reference_type`
    is therefore a plain free-text `String`, not a Postgres `Enum`
    (app.core.filters.parse_reference would otherwise 422-reject any target
    type outside a hand-picked list, which is wrong for a genuinely
    polymorphic-to-anything field) — `reference_id`'s existence is never
    checked for the same reason (RESOURCE_REGISTRY is keyed by a known,
    finite set of resource types, not "any string"). The raw
    reference_reference / reference_identifier_* fallback are, in practice,
    the only reliably populated columns for this field."""

    __tablename__ = "appointment_supporting_information"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    # Free-text resource-type name exactly as parsed from the reference
    # string (e.g. "DocumentReference") — never validated against an enum.
    reference_type = Column(String, nullable=True)
    # Best-effort: only populated when the id portion of the reference
    # string parses as an integer AND the type happens to be one of this
    # system's own modeled resources; left null otherwise (e.g. an external
    # absolute URL, or a non-numeric id from another system).
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

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

    appointment = relationship(
        "AppointmentModel", back_populates="supporting_informations"
    )

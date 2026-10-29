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
from app.models.schedule.enums import ScheduleActorReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# actor (1..* per spec, modeled as 0..* — see enums.py) Reference child table
# ---------------------------------------------------------------------------


class ScheduleActor(TenantAuditMixin, Base):
    """actor[] — the resource(s) this schedule resource is for. FHIR R4
    allows Patient|Practitioner|PractitionerRole|RelatedPerson|Device|
    HealthcareService|Location as the target (see ScheduleActorReferenceType).

    reference_id stores the target's PUBLIC sequence ID — no FK/relationship,
    same flattened-reference convention as PractitionerRoleLocation. Cardinality
    (1..*) is enforced by the FHIR validator layer, not the database — see
    OrganizationModel's docstring for why no DB-level CHECK constraints exist
    in this codebase.

    No UniqueConstraint on (schedule_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment
    that wants that as a rule expresses it as a profile-layer invariant,
    not a base constraint.
    """

    __tablename__ = "schedule_actor"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_pk = Column(
        BigInteger, ForeignKey("schedule.id"), nullable=False, index=True
    )

    # The raw literal string as received — see OrganizationEndpoint's
    # reference_reference for the full reasoning.
    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ScheduleActorReferenceType, name="schedule_actor_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # actor.identifier (0..1 Identifier) — logical-reference fallback for a
    # target held in another system, or one of Patient/RelatedPerson/Device
    # (not modeled resources in this system)
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

    schedule = relationship("ScheduleModel", back_populates="actors")

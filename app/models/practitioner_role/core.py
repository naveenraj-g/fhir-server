from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.practitioner_role.enums import PractitionerRolePractitionerReferenceType

practitioner_role_id_seq = Sequence(
    "practitioner_role_pub_seq", start=140000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class PractitionerRoleModel(Base):
    """FHIR R4 PractitionerRole — https://www.hl7.org/fhir/R4/practitionerrole.html

    A specific set of Roles/Locations/specialties/services that a practitioner
    may perform at an organization for a period of time.

    Modeled to the same conventions as Organization/Location/HealthcareService:
    BigInteger internal PK + public sequence ID, full six-column CodeableConcept
    flattening, and flattened references (`{prefix}_type`/`_id`/`_display`,
    storing the target's PUBLIC sequence ID with no ForeignKey/relationship —
    see CLAUDE.md's FHIR DB Model Design section) with an Identifier
    logical-reference fallback where the target may live outside this system.

    Part of the Patient/Practitioner/Organization/Location/HealthcareService
    JWT auth rollout: org_id comes from the verified JWT's activeOrganizationId
    claim (actor.org_id), never a client-suppliable field. There is deliberately
    no user_id: like Organization, Location, and HealthcareService, a
    PractitionerRole row is treated as a shared org-level entity (which
    practitioners may act in which roles at this org) rather than something
    scoped to one end user.
    """

    __tablename__ = "practitioner_role"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    practitioner_role_id = Column(
        BigInteger,
        practitioner_role_id_seq,
        server_default=practitioner_role_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    org_id = Column(String, nullable=False, index=True)

    # ── active (0..1 boolean) ────────────────────────────────────────────────

    active = Column(Boolean, nullable=False, default=False)

    # ── period (0..1 Period) — flattened ────────────────────────────────────

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # ── practitioner (0..1 Reference(Practitioner)) ─────────────────────────
    # practitioner_id stores Practitioner's PUBLIC practitioner_id — no FK, no
    # relationship (existence enforced at write time via ensure_resource_exists(),
    # not the database).

    practitioner_type = Column(
        Enum(
            PractitionerRolePractitionerReferenceType,
            name="practitioner_role_practitioner_reference_type",
        ),
        nullable=True,
    )
    practitioner_id = Column(BigInteger, nullable=True)
    practitioner_display = Column(String, nullable=True)

    # practitioner.identifier (0..1 Identifier) — logical-reference fallback for
    # when the practitioner isn't a resource in this system.
    practitioner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    practitioner_identifier_type_system = Column(String, nullable=True)
    practitioner_identifier_type_version = Column(String, nullable=True)
    practitioner_identifier_type_code = Column(String, nullable=True)
    practitioner_identifier_type_display = Column(String, nullable=True)
    practitioner_identifier_type_text = Column(String, nullable=True)
    practitioner_identifier_type_user_selected = Column(Boolean, nullable=True)
    practitioner_identifier_system = Column(String, nullable=True)
    practitioner_identifier_value = Column(String, nullable=True)
    practitioner_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    practitioner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── organization (0..1 Reference(Organization)) ─────────────────────────
    # Shared PG enum type — never created/dropped by this resource's migration.

    organization_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    organization_id = Column(BigInteger, nullable=True)
    organization_display = Column(String, nullable=True)

    # organization.identifier (0..1 Identifier) — logical-reference fallback for
    # when the organization isn't a resource in this system.
    organization_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    organization_identifier_type_system = Column(String, nullable=True)
    organization_identifier_type_version = Column(String, nullable=True)
    organization_identifier_type_code = Column(String, nullable=True)
    organization_identifier_type_display = Column(String, nullable=True)
    organization_identifier_type_text = Column(String, nullable=True)
    organization_identifier_type_user_selected = Column(Boolean, nullable=True)
    organization_identifier_system = Column(String, nullable=True)
    organization_identifier_value = Column(String, nullable=True)
    organization_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    organization_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── availabilityExceptions (0..1 string) ────────────────────────────────

    availability_exceptions = Column(Text, nullable=True)

    # ── Audit ────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    identifiers = relationship(
        "PractitionerRoleIdentifier",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    codes = relationship(
        "PractitionerRoleCode",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    specialties = relationship(
        "PractitionerRoleSpecialty",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    locations = relationship(
        "PractitionerRoleLocation",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    healthcare_services = relationship(
        "PractitionerRoleHealthcareService",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PractitionerRoleTelecom",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    available_times = relationship(
        "PractitionerRoleAvailableTime",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    not_available = relationship(
        "PractitionerRoleNotAvailable",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )
    endpoints = relationship(
        "PractitionerRoleEndpoint",
        back_populates="practitioner_role",
        cascade="all, delete-orphan",
    )

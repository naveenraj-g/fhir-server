from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Sequence, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType, PractitionerReferenceType
from app.models.shared import TenantAuditMixin

practitioner_role_id_seq = Sequence(
    "practitioner_role_pub_seq", start=140000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class PractitionerRoleModel(TenantAuditMixin, Base):
    """FHIR R4 PractitionerRole — https://www.hl7.org/fhir/R4/practitionerrole.html

    A specific set of Roles/Locations/specialties/services that a
    practitioner may perform at an organization for a period of time.

    Modeled to the same conventions as Organization/Location/HealthcareService/
    Practitioner: BigInteger internal PK + public sequence ID, TenantAuditMixin
    (tenant_id, not a hand-declared org_id), flattened references
    (`{prefix}_type`/`_id`/`_display`, storing the target's PUBLIC sequence ID
    with no ForeignKey/relationship — see CLAUDE.md's FHIR DB Model Design
    section) with an Identifier logical-reference fallback where the target
    may live outside this system, and every CodeableConcept's coding[] as a
    real 0..* child/grandchild table rather than a single flattened coding
    (see code.py/specialty.py/identifier.py).

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like Organization/Location/
    HealthcareService, a PractitionerRole (the role assignment itself) is a
    shared tenant-level entity, not scoped to one end user's own account.
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

    # ── active (0..1 boolean) ─────────────────────────────────────────────────
    # Absent means unknown, not false — nullable with no default, same
    # reasoning as PractitionerModel.active/OrganizationModel.active.

    active = Column(Boolean, nullable=True)

    # ── period (0..1 Period) ──────────────────────────────────────────────────

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # ── practitioner (0..1 Reference(Practitioner)) ───────────────────────────
    # practitioner_id stores Practitioner's PUBLIC practitioner_id — no FK, no
    # relationship (see HealthcareServiceModel.provided_by_* for the same
    # pattern). Shared PG enum type, created by this resource's own migration
    # (Practitioner is the first/only resource this reference type targets so
    # far) — create_type=False here since the migration owns creation.

    practitioner_type = Column(
        Enum(
            PractitionerReferenceType,
            name="practitioner_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    practitioner_id = Column(BigInteger, nullable=True, index=True)
    practitioner_display = Column(String, nullable=True)

    # practitioner.identifier (0..1 Identifier) — logical-reference fallback
    # for when the practitioner isn't a resource in this system.
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
    practitioner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    practitioner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── organization (0..1 Reference(Organization)) ───────────────────────────
    # Shared organization_reference_type PG enum — never created/dropped by
    # this resource's migration.

    organization_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    organization_id = Column(BigInteger, nullable=True, index=True)
    organization_display = Column(String, nullable=True)

    # organization.identifier (0..1 Identifier) — logical-reference fallback
    # for when the organization isn't a resource in this system.
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
    organization_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    organization_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── availabilityExceptions (0..1 string) ─────────────────────────────────

    availability_exceptions = Column(Text, nullable=True)

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/LocationModel/HealthcareServiceModel.

    # ── Relationships ─────────────────────────────────────────────────────────

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

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

healthcare_service_id_seq = Sequence(
    "healthcare_service_pub_seq", start=150000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class HealthcareServiceModel(Base):
    """FHIR R4 HealthcareService — https://www.hl7.org/fhir/R4/healthcareservice.html

    The details of a healthcare service available at a location, or by an
    organization, for a certain type of patient.

    Modeled to the same conventions as Organization/Location/Patient: BigInteger
    internal PK + public sequence ID, full six-column CodeableConcept/Coding
    flattening, and flattened references (`{prefix}_type`/`_id`/`_display`,
    storing the target's PUBLIC sequence ID with no ForeignKey/relationship —
    see CLAUDE.md's FHIR DB Model Design section) with an Identifier
    logical-reference fallback where the target may live outside this system.

    Not part of the Patient/Practitioner/Organization/Location JWT auth
    rollout, so org_id stays a plain, nullable, gateway-forwarded field — same
    as every other non-auth resource (Encounter, PractitionerRole, …).
    There is deliberately no user_id: like Organization and Location, a
    HealthcareService is a shared tenant-level entity (a service the org
    offers) rather than something scoped to one end user.
    """

    __tablename__ = "healthcare_service"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    healthcare_service_id = Column(
        BigInteger,
        healthcare_service_id_seq,
        server_default=healthcare_service_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    org_id = Column(String, nullable=False, index=True)

    # ── active (0..1 boolean) ─────────────────────────────────────────────────

    active = Column(Boolean, nullable=True, default=False)

    # ── providedBy (0..1 Reference(Organization)) ─────────────────────────────
    # provided_by_id stores Organization's PUBLIC organization_id — no FK, no
    # relationship (target table varies conceptually across resources sharing
    # this pattern, and existence is enforced at write time via
    # ensure_resource_exists(), not the database). Shared PG enum type — never
    # created/dropped by this resource's migration.

    provided_by_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    provided_by_id = Column(BigInteger, nullable=True)
    provided_by_display = Column(String, nullable=True)

    # providedBy.identifier (0..1 Identifier) — logical-reference fallback for
    # when the providing organization isn't a resource in this system.
    provided_by_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    provided_by_identifier_type_system = Column(String, nullable=True)
    provided_by_identifier_type_version = Column(String, nullable=True)
    provided_by_identifier_type_code = Column(String, nullable=True)
    provided_by_identifier_type_display = Column(String, nullable=True)
    provided_by_identifier_type_text = Column(String, nullable=True)
    provided_by_identifier_type_user_selected = Column(Boolean, nullable=True)
    provided_by_identifier_system = Column(String, nullable=True)
    provided_by_identifier_value = Column(String, nullable=True)
    provided_by_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    provided_by_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── name (0..1 string) ────────────────────────────────────────────────────

    name = Column(String, nullable=False, index=True)

    # ── comment (0..1 string) ─────────────────────────────────────────────────

    comment = Column(Text, nullable=True)

    # ── extraDetails (0..1 markdown) ──────────────────────────────────────────

    extra_details = Column(Text, nullable=True)

    # ── photo (0..1 Attachment) — flattened ───────────────────────────────────
    # contentType | language | data | url | size | hash | title | creation

    photo_content_type = Column(String, nullable=True)  # MIME type e.g. "image/png"
    photo_language = Column(String, nullable=True)  # BCP-47 e.g. "en"
    photo_data = Column(Text, nullable=True)  # base64-encoded binary
    photo_url = Column(String, nullable=True)  # external URL
    photo_size = Column(BigInteger, nullable=True)  # byte size before base64
    photo_hash = Column(String, nullable=True)  # base64-encoded SHA-1
    photo_title = Column(String, nullable=True)  # human-readable label
    photo_creation = Column(DateTime(timezone=True), nullable=True)

    # ── appointmentRequired (0..1 boolean) ───────────────────────────────────

    appointment_required = Column(Boolean, nullable=True)

    # ── availabilityExceptions (0..1 string) ─────────────────────────────────

    availability_exceptions = Column(Text, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "HealthcareServiceIdentifier",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "HealthcareServiceCategory",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "HealthcareServiceType",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    specialties = relationship(
        "HealthcareServiceSpecialty",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    locations = relationship(
        "HealthcareServiceLocation",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "HealthcareServiceTelecom",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    coverage_areas = relationship(
        "HealthcareServiceCoverageArea",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    service_provision_codes = relationship(
        "HealthcareServiceServiceProvisionCode",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    eligibilities = relationship(
        "HealthcareServiceEligibility",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    programs = relationship(
        "HealthcareServiceProgram",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    characteristics = relationship(
        "HealthcareServiceCharacteristic",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "HealthcareServiceCommunication",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    referral_methods = relationship(
        "HealthcareServiceReferralMethod",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    available_times = relationship(
        "HealthcareServiceAvailableTime",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    not_available = relationship(
        "HealthcareServiceNotAvailable",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    endpoints = relationship(
        "HealthcareServiceEndpoint",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )

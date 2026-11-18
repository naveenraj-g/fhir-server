from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType, PractitionerReferenceType
from app.models.shared import TenantAuditMixin

practitioner_role_id_seq = Sequence(
    "practitioner_role_pub_seq", start=140000, increment=1, metadata=Base.metadata
)


class PractitionerRoleModel(TenantAuditMixin, Base):
    """FHIR R4 PractitionerRole — Medplum-style storage, same as
    Organization, Location, Practitioner, HealthcareService and Endpoint.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.practitioner_role). Nothing else in this table or its
    child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 PractitionerRole search parameter filters on it
    (https://www.hl7.org/fhir/R4/practitionerrole.html#search), and is derived
    from `content` on every write by app.repository.practitioner_role._indexer.

    Search parameter -> storage:
      active            -> active (0..1, column)
      date              -> period_start / period_end (0..1 Period, two columns;
                           matched as a range — see app.fhir.search.sql.period_match)
      practitioner      -> practitioner_reference/_type/_id +
                           practitioner_identifier_system/_value (0..1, columns)
      organization      -> organization_reference/_type/_id +
                           organization_identifier_system/_value (0..1, columns)
      identifier        -> PractitionerRoleIdentifier (0..*)
      telecom, phone,
      email             -> PractitionerRoleTelecom (0..*)
      role, specialty   -> PractitionerRoleToken (0..*, one row per coding,
                           `param` says which search parameter it feeds)
      location, service,
      endpoint          -> PractitionerRoleReference (0..*, `param` says which)
      _id               -> practitioner_role_id;  _lastUpdated -> updated_at/created_at

    Everything else PractitionerRole carries (availableTime, notAvailable,
    availabilityExceptions, extension) has no search parameter and lives only
    in `content`.

    `period_start` is the first instant the period covers and `period_end`
    the first instant *after* it (see app.repository._content_index.period_bounds),
    NULL meaning open.

    No `user_id`: a PractitionerRole is a shared tenant-level entity. No
    DB-level CHECK constraints — every R4 rule is enforced by the FHIR
    validator before anything is written."""

    __tablename__ = "practitioner_role"
    __table_args__ = (
        Index("ix_practitioner_role_period", "period_start", "period_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    practitioner_role_id = Column(
        BigInteger,
        practitioner_role_id_seq,
        server_default=practitioner_role_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    active = Column(Boolean, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # practitioner (0..1 Reference(Practitioner)) and organization (0..1
    # Reference(Organization)). `*_reference` is the raw literal string exactly
    # as received (relative, or an absolute URL to another system, kept whether
    # or not it resolves locally); `*_type`/`*_id` are the resolved type and
    # PUBLIC id for a relative `Type/<id>` (no FK — see CLAUDE.md's
    # flattened-reference convention); `*_identifier_*` is Reference.identifier,
    # for `<param>:identifier`.
    practitioner_reference = Column(String, nullable=True)
    practitioner_type = Column(
        Enum(PractitionerReferenceType, name="practitioner_reference_type", create_type=False),
        nullable=True,
    )
    practitioner_id = Column(BigInteger, nullable=True, index=True)
    practitioner_identifier_system = Column(String, nullable=True)
    practitioner_identifier_value = Column(String, nullable=True)

    organization_reference = Column(String, nullable=True)
    organization_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
        nullable=True,
    )
    organization_id = Column(BigInteger, nullable=True, index=True)
    organization_identifier_system = Column(String, nullable=True)
    organization_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "PractitionerRoleIdentifier", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PractitionerRoleTelecom", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "PractitionerRoleToken", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    references = relationship(
        "PractitionerRoleReference", back_populates="practitioner_role", cascade="all, delete-orphan"
    )

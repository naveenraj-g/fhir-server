from sqlalchemy import BigInteger, Boolean, Column, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.shared import TenantAuditMixin

healthcare_service_id_seq = Sequence(
    "healthcare_service_pub_seq", start=150000, increment=1, metadata=Base.metadata
)


class HealthcareServiceModel(TenantAuditMixin, Base):
    """FHIR R4 HealthcareService — Medplum-style storage, same as
    Organization, Location and Practitioner.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.healthcare_service). Nothing else in this table or
    its child tables is a second copy of the resource: every other column
    exists only because a FHIR R4 HealthcareService search parameter filters
    on it (https://www.hl7.org/fhir/R4/healthcareservice.html#search), and is
    derived from `content` on every write by
    app.repository.healthcare_service._indexer.

    Search parameter -> storage:
      active             -> active (0..1, column)
      name               -> name/name_norm (0..1, columns)
      organization       -> provided_by_reference/_type/_id +
                            provided_by_identifier_system/_value (0..1, columns)
      identifier         -> HealthcareServiceIdentifier (0..*)
      service-category,
      service-type,
      specialty, program,
      characteristic     -> HealthcareServiceToken (0..*, one row per coding,
                            `param` says which search parameter it feeds)
      location,
      coverage-area,
      endpoint           -> HealthcareServiceReference (0..*, `param` says
                            which search parameter it feeds)
      _id                -> healthcare_service_id;  _lastUpdated -> updated_at/created_at

    Everything else HealthcareService carries (comment, extraDetails, photo,
    telecom, eligibility, serviceProvisionCode, communication, referralMethod,
    appointmentRequired, availableTime, notAvailable, availabilityExceptions,
    extension) has no search parameter and lives only in `content`.

    String parameters are stored twice: as written (answers `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) —
    for R4's default case/accent-insensitive starts-with match and
    `:contains`.

    No `user_id`: like Organization and Location, a HealthcareService is a
    shared tenant-level entity, not something scoped to one end user. No
    DB-level CHECK constraints — every R4 rule is enforced by the FHIR
    validator before anything is written."""

    __tablename__ = "healthcare_service"
    __table_args__ = (
        # text_pattern_ops: lets the default `name_norm LIKE 'value%'`
        # (starts-with) use the index regardless of the DB collation.
        Index(
            "ix_healthcare_service_name_norm",
            "name_norm",
            postgresql_ops={"name_norm": "text_pattern_ops"},
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    healthcare_service_id = Column(
        BigInteger,
        healthcare_service_id_seq,
        server_default=healthcare_service_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    active = Column(Boolean, nullable=True)
    name = Column(String, nullable=True)
    name_norm = Column(String, nullable=True)
    # providedBy (0..1 Reference(Organization)) — the `organization` search
    # parameter. `provided_by_reference` is the raw literal string exactly as
    # received (relative, or an absolute URL to another system, kept whether
    # or not it resolves locally); provided_by_type/_id are the resolved type
    # and PUBLIC id for a relative Organization/<id> (no FK — see CLAUDE.md's
    # flattened-reference convention); provided_by_identifier_* is
    # Reference.identifier, for `organization:identifier`.
    provided_by_reference = Column(String, nullable=True)
    provided_by_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    provided_by_id = Column(BigInteger, nullable=True, index=True)
    provided_by_identifier_system = Column(String, nullable=True)
    provided_by_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "HealthcareServiceIdentifier",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "HealthcareServiceToken",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "HealthcareServiceReference",
        back_populates="healthcare_service",
        cascade="all, delete-orphan",
    )

from sqlalchemy import BigInteger, Column, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.shared import TenantAuditMixin

from .enums import EndpointStatus

endpoint_id_seq = Sequence("endpoint_pub_seq", start=620000, increment=1, metadata=Base.metadata)


class EndpointModel(TenantAuditMixin, Base):
    """FHIR R4 Endpoint — Medplum-style storage, same as Organization,
    Location, Practitioner and HealthcareService.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.endpoint). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Endpoint search parameter filters on it
    (https://www.hl7.org/fhir/R4/endpoint.html#search), and is derived from
    `content` on every write by app.repository.endpoint._indexer.

    Search parameter -> storage:
      status          -> status (1..1 code, Enum column)
      connection-type -> connection_type_system/_code/_display_norm
                         (1..1 Coding, columns)
      name            -> name/name_norm (0..1, columns)
      organization    -> managing_organization_reference/_type/_id +
                         managing_organization_identifier_system/_value
                         (0..1, columns)
      identifier      -> EndpointIdentifier (0..*)
      payload-type    -> EndpointPayloadType (1..*, one row per coding)
      _id             -> endpoint_id;  _lastUpdated -> updated_at/created_at

    Everything else Endpoint carries (contact, period, payloadMimeType,
    address, header, extension) has no search parameter and lives only in
    `content`.

    String parameters are stored twice: as written (answers `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) —
    for R4's default case/accent-insensitive starts-with match and
    `:contains`.

    No `user_id`: an Endpoint is a shared tenant-level entity. No DB-level
    CHECK constraints — every R4 rule (required status, connectionType,
    payloadType, address) is enforced by the FHIR validator (the
    `java_validator` backend) before anything is written."""

    __tablename__ = "endpoint"
    __table_args__ = (
        # text_pattern_ops: lets the default `name_norm LIKE 'value%'`
        # (starts-with) use the index regardless of the DB collation.
        Index(
            "ix_endpoint_name_norm",
            "name_norm",
            postgresql_ops={"name_norm": "text_pattern_ops"},
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    endpoint_id = Column(
        BigInteger,
        endpoint_id_seq,
        server_default=endpoint_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    # Nullable like every index column: R4 makes status/connectionType
    # mandatory, but that is the validator's rule, not the database's.
    status = Column(
        Enum(
            EndpointStatus,
            name="endpoint_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    connection_type_system = Column(String, nullable=True)
    connection_type_code = Column(String, nullable=True, index=True)
    connection_type_display_norm = Column(String, nullable=True)
    name = Column(String, nullable=True)
    name_norm = Column(String, nullable=True)
    # managingOrganization (0..1 Reference(Organization)) — the `organization`
    # search parameter. `_reference` is the raw literal string exactly as
    # received (kept whether or not it resolves locally); `_type`/`_id` are
    # the resolved type and PUBLIC id for a relative Organization/<id> (no FK
    # — see CLAUDE.md's flattened-reference convention); `_identifier_*` is
    # Reference.identifier, for `organization:identifier`.
    managing_organization_reference = Column(String, nullable=True)
    managing_organization_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    managing_organization_id = Column(BigInteger, nullable=True, index=True)
    managing_organization_identifier_system = Column(String, nullable=True)
    managing_organization_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "EndpointIdentifier", back_populates="endpoint", cascade="all, delete-orphan"
    )
    payload_types = relationship(
        "EndpointPayloadType", back_populates="endpoint", cascade="all, delete-orphan"
    )

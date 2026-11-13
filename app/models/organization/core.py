from sqlalchemy import BigInteger, Boolean, Column, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.shared import TenantAuditMixin

organization_id_seq = Sequence(
    "organization_pub_seq", start=190000, increment=1, metadata=Base.metadata
)


class OrganizationModel(TenantAuditMixin, Base):
    """FHIR R4 Organization — Medplum-style storage.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.organization). Nothing else in this table or its
    child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 Organization search parameter filters on it
    (https://www.hl7.org/fhir/R4/organization.html#search), and is derived
    from `content` on every write by app.repository.organization._indexer.

    Search parameter -> storage:
      active             -> active (0..1, column)
      name               -> name/name_norm (0..1, columns) + alias/alias_norm (0..*, arrays)
      phonetic           -> name_phonetic (column)
      partof             -> partof_type/partof_id/partof_reference +
                            partof_identifier_system/_value (0..1, columns)
      identifier         -> OrganizationIdentifier (0..*)
      type               -> OrganizationType (0..*, one row per type.coding)
      address, address-* -> OrganizationAddress (0..*)
      endpoint           -> OrganizationEndpoint (0..*)
      _id                -> organization_id;  _lastUpdated -> updated_at/created_at

    String parameters are stored twice: as written (for `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) —
    for R4's default case/accent-insensitive starts-with match and
    `:contains`. `alias` is a plain list of strings, so it's an array
    column rather than a child table: no join to search it and nothing to
    delete/re-insert on write.

    No DB-level CHECK constraints — every R4 rule (org-1 etc.) is enforced
    by the FHIR validator before anything is written."""

    __tablename__ = "organization"
    __table_args__ = (
        # text_pattern_ops: lets the default `name_norm LIKE 'value%'`
        # (starts-with) use the index regardless of the DB collation.
        Index(
            "ix_organization_name_norm",
            "name_norm",
            postgresql_ops={"name_norm": "text_pattern_ops"},
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(
        BigInteger,
        organization_id_seq,
        server_default=organization_id_seq.next_value(),
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
    # NULL (not an empty array) when there are no aliases, so `:missing`
    # is a plain IS NULL test.
    alias = Column(ARRAY(String), nullable=True)
    alias_norm = Column(ARRAY(String), nullable=True)
    # Soundex code of every word in `name`, space-padded (" G564 H213 ") so a
    # code can be matched as a whole token — see app.core.phonetic.
    name_phonetic = Column(String, nullable=True)
    # partOf. `partof_reference` is the raw literal `reference` string
    # exactly as received — relative ("Organization/190004") or an absolute
    # URL to another system's server entirely — kept whether or not it
    # resolves to a local row: an external absolute URL has nowhere else to
    # live (partof_id can never resolve it), and it's what an absolute-URL
    # `partof=` search matches. partof_type/partof_id are the resolved type
    # and PUBLIC id when it's a relative Organization/<id> (no FK — see
    # CLAUDE.md's flattened-reference convention); partof_identifier_* is
    # Reference.identifier, for `partof:identifier`.
    partof_reference = Column(String, nullable=True)
    partof_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    partof_id = Column(BigInteger, nullable=True, index=True)
    partof_identifier_system = Column(String, nullable=True)
    partof_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "OrganizationIdentifier",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "OrganizationType", back_populates="organization", cascade="all, delete-orphan"
    )
    addresses = relationship(
        "OrganizationAddress",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    endpoints = relationship(
        "OrganizationEndpoint",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

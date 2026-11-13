from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Enum,
    Index,
    Numeric,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.location.enums import LocationPartOfReferenceType, LocationStatus
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AddressUse

location_id_seq = Sequence(
    "location_pub_seq", start=230000, increment=1, metadata=Base.metadata
)


class LocationModel(TenantAuditMixin, Base):
    """FHIR R4 Location — Medplum-style storage, same as OrganizationModel.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.location). Every other column, here and in the
    child tables, exists only because a FHIR R4 Location search parameter
    filters on it (https://www.hl7.org/fhir/R4/location.html#search), and is
    derived from `content` on every write by
    app.repository.location._indexer.

    Search parameter -> storage:
      name                -> name/name_norm (column) + alias/alias_norm (arrays)
      status              -> status
      operational-status  -> operational_status_system/_code/_display_norm
      address, address-*  -> address_* (Location.address is 0..1, so its
                             searched parts are columns here, not a child table)
      organization        -> managing_organization_reference/_type/_id/_identifier_*
      partof              -> part_of_reference/_type/_id/_identifier_*
      near                -> position_latitude / position_longitude
      identifier          -> LocationIdentifier (0..*)
      type                -> LocationType (0..*, one row per type.coding)
      endpoint            -> LocationEndpoint (0..*)
      _id                 -> location_id;  _lastUpdated -> updated_at/created_at

    Searched strings are stored as written (answers `:exact`) and normalized
    (`*_norm`: accents stripped, case-folded — app.fhir.search.normalize —
    for the default starts-with and `:contains`).

    The `*_reference` columns keep a Reference's raw `reference` string
    exactly as received (relative, or an absolute URL to another server)
    whether or not it resolves locally — see
    OrganizationModel.partof_reference for the full reasoning. `*_type` /
    `*_id` are the resolved type and PUBLIC id of a relative reference (no
    FK — CLAUDE.md's flattened-reference convention).

    There is deliberately no user_id: like Organization, a Location is a
    shared tenant-level entity scoped by org_id."""

    __tablename__ = "location"
    __table_args__ = (
        # position.latitude/longitude are jointly 1..1 within the 0..1
        # position BackboneElement — the one CheckConstraint shape CLAUDE.md
        # allows (base R4 validation enforces it first; this guards the
        # index columns derived from it).
        CheckConstraint(
            "(position_longitude IS NULL) = (position_latitude IS NULL)",
            name="ck_location_position_lat_long_together",
        ),
        # text_pattern_ops: lets the default `name_norm LIKE 'value%'`
        # (starts-with) use the index regardless of the DB collation.
        Index(
            "ix_location_name_norm",
            "name_norm",
            postgresql_ops={"name_norm": "text_pattern_ops"},
        ),
    )

    # Internal PK — never exposed.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    # Public ID — used in all API responses and FHIR references.
    location_id = Column(
        BigInteger,
        location_id_seq,
        server_default=location_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(Enum(LocationStatus, name="location_status"), nullable=True)
    operational_status_system = Column(String, nullable=True)
    operational_status_code = Column(String, nullable=True)
    operational_status_display_norm = Column(String, nullable=True)
    name = Column(String, nullable=True, index=True)
    name_norm = Column(String, nullable=True)
    # NULL (not an empty array) when there are no aliases, so `:missing`
    # is a plain IS NULL test.
    alias = Column(ARRAY(String), nullable=True)
    alias_norm = Column(ARRAY(String), nullable=True)

    # Location.address (0..1) — only the parts the address* parameters match.
    address_use = Column(
        Enum(AddressUse, name="address_use", create_type=False), nullable=True
    )
    address_text = Column(String, nullable=True)
    address_text_norm = Column(String, nullable=True)
    address_line = Column(ARRAY(String), nullable=True)
    address_line_norm = Column(ARRAY(String), nullable=True)
    address_city = Column(String, nullable=True)
    address_city_norm = Column(String, nullable=True)
    address_district = Column(String, nullable=True)
    address_district_norm = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_state_norm = Column(String, nullable=True)
    address_postal_code = Column(String, nullable=True)
    address_postal_code_norm = Column(String, nullable=True)
    address_country = Column(String, nullable=True)
    address_country_norm = Column(String, nullable=True)

    # managingOrganization (`organization` search parameter).
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

    # partOf (`partof` search parameter) — self-referential hierarchy.
    part_of_reference = Column(String, nullable=True)
    part_of_type = Column(
        Enum(LocationPartOfReferenceType, name="location_part_of_reference_type"),
        nullable=True,
    )
    part_of_id = Column(BigInteger, nullable=True, index=True)
    part_of_identifier_system = Column(String, nullable=True)
    part_of_identifier_value = Column(String, nullable=True)

    # position (`near`) — WGS84 decimal degrees.
    position_longitude = Column(Numeric(18, 8), nullable=True)
    position_latitude = Column(Numeric(18, 8), nullable=True)

    identifiers = relationship(
        "LocationIdentifier", back_populates="location", cascade="all, delete-orphan"
    )
    types = relationship(
        "LocationType", back_populates="location", cascade="all, delete-orphan"
    )
    endpoints = relationship(
        "LocationEndpoint", back_populates="location", cascade="all, delete-orphan"
    )

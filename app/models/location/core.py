from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.location.enums import (
    LocationMode,
    LocationPartOfReferenceType,
    LocationStatus,
)
from app.models.shared import FhirAddressMixin, FhirCodingMixin, TenantAuditMixin

location_id_seq = Sequence(
    "location_pub_seq", start=230000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class LocationModel(FhirAddressMixin, TenantAuditMixin, Base):
    """FHIR R4 Location — https://www.hl7.org/fhir/R4/location.html

    Physical place where services are provided, resources and participants
    may be stored, found, contained or accommodated.

    Modeled to the same conventions as Organization: BigInteger internal PK
    + public sequence ID, TenantAuditMixin (tenant_id, not a hand-declared
    org_id — see that mixin's docstring), resolved references with an
    Identifier logical-reference fallback, and every CodeableConcept's
    coding[] as a real 0..* child/grandchild table rather than a single
    flattened coding (see LocationPhysicalTypeCoding below, and type.py/
    identifier.py) — a CodeableConcept's coding is 0..* per spec even where
    this resource only ever carries one CodeableConcept at that position
    (e.g. physicalType, which is 0..1 at the Location level but whose
    *coding* array within it is still 0..*).

    Address (0..1) is the shared FhirAddressMixin with `_address_prefix =
    "address_"` — same pattern as OrganizationContact — not hand-declared
    columns, so `line` stays a real Postgres array (never comma-separated
    text) and every Address sub-field stays nullable, since none are
    required by the base Address datatype. `status` and `mode` are also
    nullable, matching their real 0..1 cardinality (both were previously
    mis-modeled here as NOT NULL, stricter than R4 actually requires).
    `position.longitude`/`position.latitude` are 1..1 *within* position
    even though position itself is 0..1 — enforced by the
    ck_location_position_lat_long_together CHECK below rather than a plain
    NOT NULL, since neither column can be unconditionally required.

    Every Reference field (managingOrganization, partOf, identifier.assigner,
    endpoint) also carries its own `*_reference` raw-string column — the
    literal value exactly as received, kept regardless of whether it
    resolves locally — matching OrganizationModel's partof_reference/
    assigner_reference/reference_reference exactly; these were missing here
    before this pass.

    There is deliberately no user_id: like Organization, a Location is a
    shared tenant-level entity (a physical place belongs to an org, not to
    one end user).
    """

    __tablename__ = "location"
    _address_prefix = "address_"
    __table_args__ = (
        CheckConstraint(
            "(position_longitude IS NULL) = (position_latitude IS NULL)",
            name="ck_location_position_lat_long_together",
        ),
    )

    # Internal PK — never exposed. BigInteger to match Organization and
    # Practitioner, and because every child table's FK must share the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    location_id = Column(
        BigInteger,
        location_id_seq,
        server_default=location_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── status (0..1 code) ────────────────────────────────────────────────────

    status = Column(Enum(LocationStatus, name="location_status"), nullable=True)

    # ── operationalStatus (0..1 Coding) ──────────────────────────────────────
    # Coding, not CodeableConcept — so it has no `text` sibling, but it does
    # carry version/userSelected like any other Coding.
    # https://www.hl7.org/fhir/R4/datatypes.html#Coding

    operational_status_system = Column(String, nullable=True)
    operational_status_version = Column(String, nullable=True)
    operational_status_code = Column(String, nullable=True)
    operational_status_display = Column(String, nullable=True)
    operational_status_user_selected = Column(Boolean, nullable=True)

    # ── name (0..1 string) ────────────────────────────────────────────────────

    name = Column(String, nullable=True, index=True)

    # ── description (0..1 string) ─────────────────────────────────────────────

    description = Column(Text, nullable=True)

    # ── mode (0..1 code) ─────────────────────────────────────────────────────

    mode = Column(Enum(LocationMode, name="location_mode"), nullable=True)

    # ── address (0..1 Address) — via FhirAddressMixin, _address_prefix =
    # "address_" (set above), same pattern as OrganizationContact's
    # address_* group. Every Address sub-field is 0..1 per the base
    # datatype (none required by spec), so none are NOT NULL; `line` is a
    # real Postgres array (mixin-provided), never comma-separated text.
    # Columns are: address_use, address_type, address_text, address_line,
    # address_city, address_district, address_state, address_postal_code,
    # address_country, address_period_start, address_period_end — accessed
    # in Python as self.use/self.type/self.city/etc.

    # ── physicalType (0..1 CodeableConcept) ──────────────────────────────────
    # text stays flattened (sibling of coding[], not part of it); coding[]
    # is a real 0..* child table (LocationPhysicalTypeCoding, below) rather
    # than a single flattened coding — same reasoning as Organization.type's
    # own coding[] promotion (see app.models.organization.type), just here
    # the parent CodeableConcept sits directly on this row instead of its
    # own child table, since physicalType itself is 0..1, not 0..*.

    physical_type_text = Column(String, nullable=True)

    # ── managingOrganization (0..1 Reference(Organization)) ──────────────────
    # Shared PG enum type — never created/dropped by this resource's migration.

    # managing_organization_reference is the raw literal string exactly as
    # received — relative ("Organization/190004") or an absolute URL to
    # another system's server entirely. Kept regardless of whether it
    # resolves to a local row — see OrganizationModel's partof_reference
    # (core.py) for the full reasoning. An external absolute URL has
    # nowhere else to live: it isn't managing_organization_id (nothing to
    # resolve to) and it isn't managing_organization_identifier_* (that's a
    # structured business Identifier, not a URL).
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
    managing_organization_display = Column(String, nullable=True)

    # managingOrganization.identifier (0..1 Identifier) — logical-reference
    # fallback for when the managing organization isn't a resource in this
    # system. Mirrors Patient.managing_organization_identifier_*.
    managing_organization_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    managing_organization_identifier_type_system = Column(String, nullable=True)
    managing_organization_identifier_type_version = Column(String, nullable=True)
    managing_organization_identifier_type_code = Column(String, nullable=True)
    managing_organization_identifier_type_display = Column(String, nullable=True)
    managing_organization_identifier_type_text = Column(String, nullable=True)
    managing_organization_identifier_type_user_selected = Column(Boolean, nullable=True)
    managing_organization_identifier_system = Column(String, nullable=True)
    managing_organization_identifier_value = Column(String, nullable=True)
    managing_organization_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    managing_organization_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    # ── partOf (0..1 Reference(Location)) — self-referential hierarchy ───────

    # part_of_reference is the raw literal string exactly as received —
    # same reasoning as managing_organization_reference above and
    # OrganizationModel's partof_reference.
    part_of_reference = Column(String, nullable=True)
    part_of_type = Column(
        Enum(LocationPartOfReferenceType, name="location_part_of_reference_type"),
        nullable=True,
    )
    part_of_id = Column(BigInteger, nullable=True, index=True)
    part_of_display = Column(String, nullable=True)

    # partOf.identifier (0..1 Identifier) — logical-reference fallback for a
    # containing location held in another system. Same shape as Organization's
    # partof_identifier_*.
    part_of_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    part_of_identifier_type_system = Column(String, nullable=True)
    part_of_identifier_type_version = Column(String, nullable=True)
    part_of_identifier_type_code = Column(String, nullable=True)
    part_of_identifier_type_display = Column(String, nullable=True)
    part_of_identifier_type_text = Column(String, nullable=True)
    part_of_identifier_type_user_selected = Column(Boolean, nullable=True)
    part_of_identifier_system = Column(String, nullable=True)
    part_of_identifier_value = Column(String, nullable=True)
    part_of_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    part_of_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── availabilityExceptions (0..1 string) ─────────────────────────────────

    availability_exceptions = Column(Text, nullable=True)

    # ── position (0..1 BackboneElement) — flattened ──────────────────────────
    # longitude/latitude are 1..1 *within* position, but position itself is
    # 0..1, so neither column can be a plain NOT NULL. Enforced instead by
    # the ck_location_position_lat_long_together CHECK (__table_args__
    # above): both null (no position) or both set together, never just one.

    position_longitude = Column(Numeric(18, 8), nullable=True)
    position_latitude = Column(Numeric(18, 8), nullable=True)
    position_altitude = Column(Numeric(18, 8), nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not Location-specific). Raw
    # [{url, valueType, value}, ...]; validated against registered
    # extension definitions by the (not-yet-built) profile pipeline, not by
    # the database. No explicit ::jsonb cast — Postgres infers it from the
    # column's own type in a DEFAULT clause, and the explicit cast is
    # invalid SQL on SQLite (the test suite's engine), which has no cast
    # syntax at all. Same shape as OrganizationModel.extension/
    # PractitionerModel.extension.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "LocationIdentifier",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    aliases = relationship(
        "LocationAlias",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "LocationType",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "LocationTelecom",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    hours_of_operation = relationship(
        "LocationHoursOfOperation",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    endpoints = relationship(
        "LocationEndpoint",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    physical_type_codings = relationship(
        "LocationPhysicalTypeCoding",
        back_populates="location",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# physicalType.coding (0..*) child table
# ---------------------------------------------------------------------------


class LocationPhysicalTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Location.physicalType.coding (0..*). physicalType itself
    is 0..1 at the Location level, so this points straight at `location.id`
    rather than at an intermediate CodeableConcept child row — unlike
    LocationTypeCoding/LocationIdentifierTypeCoding (type.py/identifier.py),
    which hang off their own 0..* parent row instead."""

    __tablename__ = "location_physical_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — named location_pk, not location_id, so it can never
    # be confused with LocationModel.location_id (the public, FHIR-facing
    # sequence ID) — same reasoning as Organization's organization_pk.
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )

    location = relationship("LocationModel", back_populates="physical_type_codings")

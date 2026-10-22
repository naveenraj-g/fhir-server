from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.location.enums import (
    LocationMode,
    LocationPartOfReferenceType,
    LocationStatus,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin
from app.schemas.enums import AddressType, AddressUse

location_id_seq = Sequence(
    "location_pub_seq", start=230000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class LocationModel(TenantAuditMixin, Base):
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

    There is deliberately no user_id: like Organization, a Location is a
    shared tenant-level entity (a physical place belongs to an org, not to
    one end user).
    """

    __tablename__ = "location"

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

    status = Column(Enum(LocationStatus, name="location_status"), nullable=False)

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

    name = Column(String, nullable=False, index=True)

    # ── description (0..1 string) ─────────────────────────────────────────────

    description = Column(Text, nullable=True)

    # ── mode (0..1 code) ─────────────────────────────────────────────────────

    mode = Column(Enum(LocationMode, name="location_mode"), nullable=False)

    # ── address (0..1 Address) — flattened, unlike Organization's 0..* ───────
    # Location.address is 0..1 (Organization.address is 0..*), so it lives in
    # flat columns rather than a child table. The required sub-fields are the
    # same either way — type/city/state/postalCode/country are NOT NULL on
    # every Address in this project, including the ones flattened into a
    # parent row (see OrganizationContact / PatientContact).

    address_use = Column(Enum(AddressUse, name="address_use"), nullable=True)
    address_type = Column(Enum(AddressType, name="address_type"), nullable=False)
    address_text = Column(Text, nullable=True)
    address_line = Column(
        Text, nullable=True
    )  # comma-separated (Address.line[] exception)
    address_city = Column(String, nullable=False)
    address_district = Column(String, nullable=True)
    address_state = Column(String, nullable=False)
    address_postal_code = Column(String, nullable=False)
    address_country = Column(String, nullable=False)
    address_period_start = Column(DateTime(timezone=True), nullable=True)
    address_period_end = Column(DateTime(timezone=True), nullable=True)

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
    # 0..1, so all three columns are nullable; the schema layer enforces that
    # longitude+latitude are supplied together.

    position_longitude = Column(Numeric(18, 8), nullable=True)
    position_latitude = Column(Numeric(18, 8), nullable=True)
    position_altitude = Column(Numeric(18, 8), nullable=True)

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

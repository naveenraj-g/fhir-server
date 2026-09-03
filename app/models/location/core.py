from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.location.enums import (
    LocationMode,
    LocationPartOfReferenceType,
    LocationStatus,
)
from app.schemas.enums import AddressType, AddressUse

location_id_seq = Sequence(
    "location_pub_seq", start=230000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class LocationModel(Base):
    """FHIR R4 Location — https://www.hl7.org/fhir/R4/location.html

    Physical place where services are provided, resources and participants
    may be stored, found, contained or accommodated.

    Modeled to the same conventions as Patient/Practitioner/Organization:
    BigInteger internal PK + public sequence ID, full six-column
    CodeableConcept/Coding flattening, resolved references with an
    Identifier logical-reference fallback, and audit columns on every table.
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

    # Tenant field forwarded by the gateway — NOT FHIR data, and unrelated to
    # managing_organization below. There is deliberately no user_id: like
    # Organization, a Location is a shared tenant-level entity (a physical
    # place belongs to an org, not to one end user).
    org_id = Column(String, nullable=False, index=True)

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
    address_line = Column(Text, nullable=True)  # comma-separated (Address.line[] exception)
    address_city = Column(String, nullable=False)
    address_district = Column(String, nullable=True)
    address_state = Column(String, nullable=False)
    address_postal_code = Column(String, nullable=False)
    address_country = Column(String, nullable=False)
    address_period_start = Column(DateTime(timezone=True), nullable=True)
    address_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── physicalType (0..1 CodeableConcept) ──────────────────────────────────

    physical_type_system = Column(String, nullable=True)
    physical_type_version = Column(String, nullable=True)
    physical_type_code = Column(String, nullable=True)
    physical_type_display = Column(String, nullable=True)
    physical_type_text = Column(String, nullable=True)
    physical_type_user_selected = Column(Boolean, nullable=True)

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
    managing_organization_identifier_type_user_selected = Column(
        Boolean, nullable=True
    )
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

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

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

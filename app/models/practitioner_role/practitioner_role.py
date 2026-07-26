from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.practitioner_role.enums import (
    DayOfWeek,
    PractitionerRoleEndpointReferenceType,
    PractitionerRoleHealthcareServiceReferenceType,
    PractitionerRoleLocationReferenceType,
)
from app.schemas.enums import (
    ContactPointSystem,
    ContactPointUse,
    IdentifierUse,
)

practitioner_role_id_seq = Sequence("practitioner_role_pub_seq", start=140000, increment=1, metadata=Base.metadata)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------

class PractitionerRoleModel(Base):
    __tablename__ = "practitioner_role"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    practitioner_role_id = Column(
        Integer,
        practitioner_role_id_seq,
        server_default=practitioner_role_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    active = Column(Boolean, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # practitioner (0..1 Reference(Practitioner)) — internal PK, matches repo convention
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=True, index=True)
    practitioner_display = Column(String, nullable=True)

    # organization (0..1 Reference(Organization))
    organization_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
        nullable=True,
    )
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=True, index=True)
    organization_display = Column(String, nullable=True)

    # availabilityExceptions (0..1 string) — narrative exceptions to availability
    availability_exceptions = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # parent relationship
    practitioner = relationship(
        "PractitionerModel", foreign_keys=[practitioner_id], lazy="selectin"
    )
    organization = relationship(
        "OrganizationModel", foreign_keys=[organization_id], lazy="selectin"
    )

    # child relationships
    identifiers = relationship(
        "PractitionerRoleIdentifier", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    codes = relationship(
        "PractitionerRoleCode", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "PractitionerRoleSpecialty", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    locations = relationship(
        "PractitionerRoleLocation", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    healthcare_services = relationship(
        "PractitionerRoleHealthcareService", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PractitionerRoleTelecom", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    available_times = relationship(
        "PractitionerRoleAvailabilityTime", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    not_available_times = relationship(
        "PractitionerRoleNotAvailableTime", back_populates="practitioner_role", cascade="all, delete-orphan"
    )
    endpoints = relationship(
        "PractitionerRoleEndpoint", back_populates="practitioner_role", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# identifier[] — 0..*  (Identifier)
# ---------------------------------------------------------------------------

class PractitionerRoleIdentifier(Base):
    __tablename__ = "practitioner_role_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="identifiers")


# ---------------------------------------------------------------------------
# code[] — 0..*  (CodeableConcept)
# ---------------------------------------------------------------------------

class PractitionerRoleCode(Base):
    __tablename__ = "practitioner_role_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="codes")


# ---------------------------------------------------------------------------
# specialty[] — 0..*  (CodeableConcept)
# ---------------------------------------------------------------------------

class PractitionerRoleSpecialty(Base):
    __tablename__ = "practitioner_role_specialty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="specialties")


# ---------------------------------------------------------------------------
# location[] — 0..*  (Reference(Location))
# ---------------------------------------------------------------------------

class PractitionerRoleLocation(Base):
    __tablename__ = "practitioner_role_location"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(PractitionerRoleLocationReferenceType, name="pr_location_ref_type"),
        nullable=True,
    )
    reference_id = Column(Integer, ForeignKey("location.id"), nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference = relationship("LocationModel", foreign_keys=[reference_id], lazy="selectin")

    practitioner_role = relationship("PractitionerRoleModel", back_populates="locations")


# ---------------------------------------------------------------------------
# healthcareService[] — 0..*  (Reference(HealthcareService))
# ---------------------------------------------------------------------------

class PractitionerRoleHealthcareService(Base):
    __tablename__ = "practitioner_role_healthcare_service"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(PractitionerRoleHealthcareServiceReferenceType, name="pr_healthcare_service_ref_type"),
        nullable=True,
    )
    reference_id = Column(Integer, ForeignKey("healthcare_service.id"), nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference = relationship("HealthcareServiceModel", foreign_keys=[reference_id], lazy="selectin")

    practitioner_role = relationship("PractitionerRoleModel", back_populates="healthcare_services")


# ---------------------------------------------------------------------------
# telecom[] — 0..*  (ContactPoint)  — required R4 element
# ---------------------------------------------------------------------------

class PractitionerRoleTelecom(Base):
    __tablename__ = "practitioner_role_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(Enum(ContactPointSystem, name="contact_point_system", create_type=False), nullable=True)
    value = Column(String, nullable=True)
    use = Column(Enum(ContactPointUse, name="contact_point_use", create_type=False), nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="telecoms")


# ---------------------------------------------------------------------------
# availableTime[] / notAvailable[] — 0..* each, flat top-level per R4
# (R5 wraps these in a single `availability` object — not used here)
# ---------------------------------------------------------------------------

class PractitionerRoleAvailabilityTime(Base):
    """availableTime BackboneElement — times the role is available."""
    __tablename__ = "practitioner_role_availability_time"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # daysOfWeek (0..* code)
    days_of_week = Column(ARRAY(Enum(DayOfWeek, name="day_of_week")), nullable=True)
    all_day = Column(Boolean, nullable=True)
    # FHIR time type is HH:mm:ss — stored as String
    available_start_time = Column(String, nullable=True)
    available_end_time = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="available_times")


class PractitionerRoleNotAvailableTime(Base):
    """notAvailable BackboneElement — times the role is not available."""
    __tablename__ = "practitioner_role_not_available_time"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    description = Column(String, nullable=True)
    during_start = Column(DateTime(timezone=True), nullable=True)
    during_end = Column(DateTime(timezone=True), nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="not_available_times")


# ---------------------------------------------------------------------------
# endpoint[] — 0..*  (Reference(Endpoint))
# ---------------------------------------------------------------------------

class PractitionerRoleEndpoint(Base):
    __tablename__ = "practitioner_role_endpoint"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(PractitionerRoleEndpointReferenceType, name="pr_endpoint_ref_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="endpoints")

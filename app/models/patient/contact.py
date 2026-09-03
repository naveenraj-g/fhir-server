from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.patient.enums import (
    AddressType,
    AddressUse,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
    PatientGender,
)


class PatientContact(Base):
    """contact[] BackboneElement — guardian, next-of-kin, or emergency contact.

    R4 fields: relationship (0..*), name (0..1), telecom (0..*), address (0..1),
               gender (0..1), organization (0..1 Reference), period (0..1).
    name and address are 0..1 so they are flattened onto this table.
    relationship and telecom are 0..* so they become grandchild tables
    (PatientContactRelationship, PatientContactTelecom — defined below in
    this same file since they only exist to support PatientContact).
    """

    __tablename__ = "patient_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    # name (0..1 HumanName) — flattened
    name_use = Column(Enum(HumanNameUse, name="human_name_use"), nullable=True)
    name_text = Column(String, nullable=True)
    name_family = Column(String, nullable=True)
    name_given = Column(Text, nullable=True)  # comma-separated
    name_prefix = Column(Text, nullable=True)  # comma-separated
    name_suffix = Column(Text, nullable=True)  # comma-separated
    name_period_start = Column(DateTime(timezone=True), nullable=True)
    name_period_end = Column(DateTime(timezone=True), nullable=True)

    # address (0..1 Address) — flattened
    address_use = Column(Enum(AddressUse, name="address_use"), nullable=True)
    address_type = Column(Enum(AddressType, name="address_type"), nullable=False)
    address_text = Column(String, nullable=True)
    address_line = Column(Text, nullable=True)  # comma-separated
    address_city = Column(String, nullable=False)
    address_district = Column(String, nullable=True)
    address_state = Column(String, nullable=False)
    address_postal_code = Column(String, nullable=False)
    address_country = Column(String, nullable=False)
    address_period_start = Column(DateTime(timezone=True), nullable=True)
    address_period_end = Column(DateTime(timezone=True), nullable=True)

    gender = Column(Enum(PatientGender, name="patient_gender"), nullable=True)

    # organization (0..1 Reference(Organization)) — flattened
    organization_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    organization_id = Column(BigInteger, nullable=True, index=True)
    organization_display = Column(String, nullable=True)

    # organization.identifier (0..1 Identifier) — logical-reference fallback,
    # same shape/purpose as managing_organization_identifier_* on PatientModel
    organization_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    organization_identifier_type_system = Column(String, nullable=True)
    organization_identifier_type_version = Column(String, nullable=True)
    organization_identifier_type_code = Column(String, nullable=True)
    organization_identifier_type_display = Column(String, nullable=True)
    organization_identifier_type_text = Column(String, nullable=True)
    organization_identifier_type_user_selected = Column(Boolean, nullable=True)
    organization_identifier_system = Column(String, nullable=True)
    organization_identifier_value = Column(String, nullable=True)
    organization_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    organization_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # period (0..1 Period) — flattened
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="contacts")
    relationships = relationship(
        "PatientContactRelationship",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PatientContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class PatientContactRelationship(Base):
    """contact[].relationship[] — CodeableConcept — nature of relationship to patient."""

    __tablename__ = "patient_contact_relationship"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("patient_contact.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    coding_system = Column(String, nullable=True)
    coding_version = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)
    coding_user_selected = Column(Boolean, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    contact = relationship("PatientContact", back_populates="relationships")


class PatientContactTelecom(Base):
    """contact[].telecom[] — ContactPoint — contact details for the contact person."""

    __tablename__ = "patient_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("patient_contact.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    system = Column(
        Enum(ContactPointSystem, name="contact_point_system"), nullable=False
    )
    value = Column(String, nullable=False)
    use = Column(Enum(ContactPointUse, name="contact_point_use"), nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    contact = relationship("PatientContact", back_populates="telecoms")

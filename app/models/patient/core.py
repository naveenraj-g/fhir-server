from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.patient.enums import PatientGender

patient_id_seq = Sequence(
    "patient_pub_seq", start=10000, increment=1, metadata=Base.metadata
)


class PatientModel(Base):
    """FHIR R4 Patient — demographics and administrative information about an
    individual receiving care. Owns the scalar fields (gender, birthDate,
    deceased[x], maritalStatus, multipleBirth[x], managingOrganization) plus
    the 9 sub-resource relationships defined in this package's sibling
    modules (identifiers, names, telecoms, addresses, photos, contacts,
    communications, general_practitioners, links)."""

    __tablename__ = "patient"
    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_patient_user_id_org_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    patient_id = Column(
        BigInteger,
        patient_id_seq,
        server_default=patient_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=False, index=True)

    active = Column(Boolean, nullable=False, default=False)
    gender = Column(Enum(PatientGender, name="patient_gender"), nullable=False)
    birth_date = Column(Date, nullable=False)

    # deceased[x] — boolean | dateTime choice type
    deceased_boolean = Column(Boolean, nullable=False, default=False)

    # need to have timezone in UTC
    deceased_datetime = Column(DateTime(timezone=True), nullable=True)

    # maritalStatus (0..1 CodeableConcept) — flattened
    marital_status_system = Column(String, nullable=True)
    marital_status_version = Column(String, nullable=True)
    marital_status_code = Column(String, nullable=True)
    marital_status_display = Column(String, nullable=True)
    marital_status_text = Column(String, nullable=True)
    marital_status_user_selected = Column(Boolean, nullable=True)

    # multipleBirth[x] — boolean | integer choice type
    multiple_birth_boolean = Column(Boolean, nullable=True)
    multiple_birth_integer = Column(Integer, nullable=True)

    # managingOrganization (0..1 Reference(Organization)) — flattened
    managing_organization_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    managing_organization_id = Column(BigInteger, nullable=True)
    managing_organization_display = Column(String, nullable=True)

    # managingOrganization.identifier (0..1 Identifier) — logical-reference
    # fallback, flattened the same way PatientIdentifier.* is, used when the
    # managing organization isn't a resource in this system at all
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    identifiers = relationship(
        "PatientIdentifier",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "PatientName",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PatientTelecom",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "PatientAddress",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    photos = relationship(
        "PatientPhoto",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "PatientContact",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "PatientCommunication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    general_practitioners = relationship(
        "PatientGeneralPractitioner",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    links = relationship(
        "PatientLink",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender

patient_id_seq = Sequence(
    "patient_pub_seq", start=10000, increment=1, metadata=Base.metadata
)


class PatientModel(TenantAuditMixin, Base):
    """FHIR R4 Patient. Demographics and other administrative information about an
    individual receiving care or other health-related services.
    https://www.hl7.org/fhir/R4/patient.html

    Patient keeps a plain `user_id` column alongside the JWT-derived `tenant_id`/
    `created_by`/`updated_by` (TenantAuditMixin) — a Patient record belongs to an
    individual end-user, so `/me` scopes to `actor.sub` + `actor.org_id`.
    """

    __tablename__ = "patient"

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

    # active (0..1 boolean)
    active = Column(Boolean, nullable=True)

    # gender (0..1 code, AdministrativeGender)
    gender = Column(Enum(AdministrativeGender, name="administrative_gender"), nullable=True)

    # birthDate (0..1 date)
    birth_date = Column(Date, nullable=True)

    # deceased[x] (0..1 boolean | dateTime)
    deceased_boolean = Column(Boolean, nullable=True)
    deceased_date_time = Column(DateTime(timezone=True), nullable=True)

    # maritalStatus (0..1 CodeableConcept) — text flat here, coding[] in child table
    marital_status_text = Column(String, nullable=True)

    # multipleBirth[x] (0..1 boolean | integer)
    multiple_birth_boolean = Column(Boolean, nullable=True)
    multiple_birth_integer = Column(Integer, nullable=True)

    # managingOrganization (0..1 Reference(Organization))
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
    managing_organization_identifier_system = Column(String, nullable=True)
    managing_organization_identifier_value = Column(String, nullable=True)
    managing_organization_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    managing_organization_identifier_type_text = Column(String, nullable=True)

    # Mandatory resource-level extension column
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
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
    marital_status_codings = relationship(
        "PatientMaritalStatusCoding",
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

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import (
    FhirAddressMixin,
    FhirCodingMixin,
    FhirContactPointMixin,
    TenantAuditMixin,
)
from app.schemas.enums import AdministrativeGender, HumanNameUse


class PatientContact(FhirAddressMixin, TenantAuditMixin, Base):
    """Patient.contact (0..* BackboneElement) child table.
    contact.address uses FhirAddressMixin with `_address_prefix = "address_"`."""

    __tablename__ = "patient_contact"
    _address_prefix = "address_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    # gender (0..1 code, AdministrativeGender)
    gender = Column(Enum(AdministrativeGender, name="administrative_gender"), nullable=True)

    # name (0..1 HumanName) flattened
    name_use = Column(Enum(HumanNameUse, name="human_name_use"), nullable=True)
    name_text = Column(String, nullable=True)
    name_family = Column(String, nullable=True)
    name_given = Column(ARRAY(String), nullable=True)
    name_prefix = Column(ARRAY(String), nullable=True)
    name_suffix = Column(ARRAY(String), nullable=True)
    name_period_start = Column(DateTime(timezone=True), nullable=True)
    name_period_end = Column(DateTime(timezone=True), nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # organization (0..1 Reference(Organization))
    organization_reference = Column(String, nullable=True)
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
    organization_identifier_system = Column(String, nullable=True)
    organization_identifier_value = Column(String, nullable=True)
    organization_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    organization_identifier_type_text = Column(String, nullable=True)

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


class PatientContactRelationship(TenantAuditMixin, Base):
    """Patient.contact.relationship (0..* CodeableConcept) child table."""

    __tablename__ = "patient_contact_relationship"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("patient_contact.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    contact = relationship("PatientContact", back_populates="relationships")
    codings = relationship(
        "PatientContactRelationshipCoding",
        back_populates="relationship",
        cascade="all, delete-orphan",
    )


class PatientContactRelationshipCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Patient.contact.relationship.coding (0..*)."""

    __tablename__ = "patient_contact_relationship_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    relationship_id = Column(
        BigInteger, ForeignKey("patient_contact_relationship.id"), nullable=False, index=True
    )

    relationship = relationship("PatientContactRelationship", back_populates="codings")


class PatientContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """Patient.contact.telecom (0..* ContactPoint) child table."""

    __tablename__ = "patient_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("patient_contact.id"), nullable=False, index=True
    )

    contact = relationship("PatientContact", back_populates="telecoms")

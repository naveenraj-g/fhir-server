from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.related_person.enums import RelatedPersonPatientReferenceType
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender


class RelatedPersonModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 RelatedPerson resource.

    A person that is related to a patient, but who is not a direct target of care.
    Sequenced public ID block starts at 300000 (related_person_pub_seq).
    There is deliberately no user_id: RelatedPerson is an org-scoped entity
    associated with a patient, not scoped to an individual system user.
    """

    __tablename__ = "related_person"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_id = Column(
        BigInteger,
        Sequence(
            "related_person_pub_seq",
            start=300000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    active = Column(Boolean, nullable=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            RelatedPersonPatientReferenceType,
            name="related_person_patient_reference_type",
        ),
        nullable=False,
        default=RelatedPersonPatientReferenceType.Patient,
    )
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_display = Column(String, nullable=True)

    # gender (0..1 code, AdministrativeGender)
    gender = Column(
        Enum(AdministrativeGender, name="administrative_gender", create_type=False),
        nullable=True,
    )

    # birthDate (0..1 date)
    birth_date = Column(Date, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "RelatedPersonIdentifier",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    relationships = relationship(
        "RelatedPersonRelationship",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "RelatedPersonName",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "RelatedPersonTelecom",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "RelatedPersonAddress",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    photos = relationship(
        "RelatedPersonPhoto",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "RelatedPersonCommunication",
        back_populates="related_person",
        cascade="all, delete-orphan",
    )

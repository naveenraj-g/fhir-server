from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.document_reference.enums import (
    DocumentReferenceAuthenticatorReferenceType,
    DocumentReferenceAuthorReferenceType,
    DocumentReferenceDocStatus,
    DocumentReferencePatientReferenceType,
    DocumentReferenceStatus,
    DocumentReferenceSubjectReferenceType,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin

document_reference_id_seq = Sequence(
    "document_reference_pub_seq", start=320000, metadata=Base.metadata
)


class DocumentReferenceModel(TenantAuditMixin, Base):
    """FHIR R4 DocumentReference model — https://www.hl7.org/fhir/R4/documentreference.html

    A reference to a document of any kind for any purpose.
    Provides metadata about the document so that the document can be discovered and managed.
    """

    __tablename__ = "document_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_id = Column(
        BigInteger,
        document_reference_id_seq,
        server_default=document_reference_id_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )

    # masterIdentifier (0..1 Identifier) flattened
    master_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    master_identifier_type_text = Column(String, nullable=True)
    master_identifier_system = Column(String, nullable=True)
    master_identifier_value = Column(String, nullable=True)
    master_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    master_identifier_period_end = Column(DateTime(timezone=True), nullable=True)
    master_identifier_assigner_reference = Column(String, nullable=True)
    master_identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    master_identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    master_identifier_assigner_display = Column(String, nullable=True)
    master_identifier_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    master_identifier_assigner_identifier_system = Column(String, nullable=True)
    master_identifier_assigner_identifier_value = Column(String, nullable=True)
    master_identifier_assigner_identifier_type_text = Column(String, nullable=True)

    # status (1..1 code)
    status = Column(
        Enum(
            DocumentReferenceStatus,
            name="document_reference_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    # docStatus (0..1 code)
    doc_status = Column(
        Enum(
            DocumentReferenceDocStatus,
            name="document_reference_doc_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )

    # type (0..1 CodeableConcept) - codings in document_reference_type_coding
    type_text = Column(String, nullable=True)

    # subject (0..1 Reference(Patient | Practitioner | Group | Device))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            DocumentReferenceSubjectReferenceType,
            name="document_reference_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # date (0..1 instant)
    date = Column(DateTime(timezone=True), nullable=True)

    # authenticator (0..1 Reference(Practitioner | PractitionerRole | Organization))
    authenticator_reference = Column(String, nullable=True)
    authenticator_type = Column(
        Enum(
            DocumentReferenceAuthenticatorReferenceType,
            name="document_reference_authenticator_reference_type",
        ),
        nullable=True,
    )
    authenticator_id = Column(BigInteger, nullable=True, index=True)
    authenticator_display = Column(String, nullable=True)

    # custodian (0..1 Reference(Organization))
    custodian_reference = Column(String, nullable=True)
    custodian_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    custodian_id = Column(BigInteger, nullable=True, index=True)
    custodian_display = Column(String, nullable=True)

    # description (0..1 string)
    description = Column(String, nullable=True)

    # context (0..1 BackboneElement) flattened 0..1 fields
    context_period_start = Column(DateTime(timezone=True), nullable=True)
    context_period_end = Column(DateTime(timezone=True), nullable=True)
    context_facility_type_text = Column(String, nullable=True)
    context_practice_setting_text = Column(String, nullable=True)
    context_source_patient_info_reference = Column(String, nullable=True)
    context_source_patient_info_type = Column(
        Enum(
            DocumentReferencePatientReferenceType,
            name="document_reference_patient_reference_type",
        ),
        nullable=True,
    )
    context_source_patient_info_id = Column(BigInteger, nullable=True, index=True)
    context_source_patient_info_display = Column(String, nullable=True)

    # extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    master_identifier_type_codings = relationship(
        "DocumentReferenceMasterIdentifierTypeCoding",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    identifiers = relationship(
        "DocumentReferenceIdentifier",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "DocumentReferenceTypeCoding",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "DocumentReferenceCategory",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    authors = relationship(
        "DocumentReferenceAuthor",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    relates_to = relationship(
        "DocumentReferenceRelatesTo",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    security_labels = relationship(
        "DocumentReferenceSecurityLabel",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    contents = relationship(
        "DocumentReferenceContent",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    context_encounters = relationship(
        "DocumentReferenceContextEncounter",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    context_events = relationship(
        "DocumentReferenceContextEvent",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    context_facility_type_codings = relationship(
        "DocumentReferenceContextFacilityTypeCoding",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    context_practice_setting_codings = relationship(
        "DocumentReferenceContextPracticeSettingCoding",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    context_related = relationship(
        "DocumentReferenceContextRelated",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )


class DocumentReferenceMasterIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.masterIdentifier.type.coding (0..*)."""

    __tablename__ = "document_reference_master_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger,
        ForeignKey("document_reference.id"),
        nullable=False,
        index=True,
    )

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="master_identifier_type_codings"
    )


class DocumentReferenceTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.type.coding (0..*)."""

    __tablename__ = "document_reference_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    document_reference = relationship("DocumentReferenceModel", back_populates="type_codings")


class DocumentReferenceContextFacilityTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.context.facilityType.coding (0..*)."""

    __tablename__ = "document_reference_context_facility_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="context_facility_type_codings"
    )


class DocumentReferenceContextPracticeSettingCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.context.practiceSetting.coding (0..*)."""

    __tablename__ = "document_reference_context_practice_setting_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="context_practice_setting_codings"
    )

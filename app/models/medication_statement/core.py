from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_statement.enums import (
    MedicationStatementContextReferenceType,
    MedicationStatementInformationSourceReferenceType,
    MedicationStatementMedicationReferenceType,
    MedicationStatementStatus,
    MedicationStatementSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

_seq = Sequence(
    "medication_statement_pub_seq",
    start=500000,
    increment=1,
    metadata=Base.metadata,
)


class MedicationStatementModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationStatement resource.

    A record of a medication that is being consumed, has been consumed,
    or may be taken by a patient.
    """

    __tablename__ = "medication_statement"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_statement_id = Column(
        BigInteger,
        _seq,
        server_default=_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    status = Column(
        Enum(
            MedicationStatementStatus,
            name="medication_statement_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # category (0..1 CodeableConcept) — text flattened
    category_text = Column(String, nullable=True)

    # medication[x] (1..1 choice: CodeableConcept | Reference(Medication))
    medication_codeable_concept_text = Column(String, nullable=True)

    medication_reference = Column(String, nullable=True)
    medication_type = Column(
        Enum(
            MedicationStatementMedicationReferenceType,
            name="medication_statement_medication_reference_type",
        ),
        nullable=True,
    )
    medication_id = Column(BigInteger, nullable=True, index=True)
    medication_display = Column(String, nullable=True)

    # medication.identifier fallback (11 columns)
    medication_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    medication_identifier_type_system = Column(String, nullable=True)
    medication_identifier_type_version = Column(String, nullable=True)
    medication_identifier_type_code = Column(String, nullable=True)
    medication_identifier_type_display = Column(String, nullable=True)
    medication_identifier_type_user_selected = Column(Boolean, nullable=True)
    medication_identifier_type_text = Column(String, nullable=True)
    medication_identifier_system = Column(String, nullable=True)
    medication_identifier_value = Column(String, nullable=True)
    medication_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    medication_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(
            MedicationStatementSubjectReferenceType,
            name="medication_statement_subject_reference_type",
        ),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # subject.identifier fallback (11 columns)
    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # context (0..1 Reference(Encounter | EpisodeOfCare))
    context_reference = Column(String, nullable=True)
    context_type = Column(
        Enum(
            MedicationStatementContextReferenceType,
            name="medication_statement_context_reference_type",
        ),
        nullable=True,
    )
    context_id = Column(BigInteger, nullable=True, index=True)
    context_display = Column(String, nullable=True)

    # context.identifier fallback (11 columns)
    context_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    context_identifier_type_system = Column(String, nullable=True)
    context_identifier_type_version = Column(String, nullable=True)
    context_identifier_type_code = Column(String, nullable=True)
    context_identifier_type_display = Column(String, nullable=True)
    context_identifier_type_user_selected = Column(Boolean, nullable=True)
    context_identifier_type_text = Column(String, nullable=True)
    context_identifier_system = Column(String, nullable=True)
    context_identifier_value = Column(String, nullable=True)
    context_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    context_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # effective[x] (0..1 choice: dateTime | Period)
    effective_date_time = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # dateAsserted (0..1 dateTime)
    date_asserted = Column(DateTime(timezone=True), nullable=True)

    # informationSource (0..1 Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization))
    information_source_reference = Column(String, nullable=True)
    information_source_type = Column(
        Enum(
            MedicationStatementInformationSourceReferenceType,
            name="medication_statement_information_source_reference_type",
        ),
        nullable=True,
    )
    information_source_id = Column(BigInteger, nullable=True, index=True)
    information_source_display = Column(String, nullable=True)

    # informationSource.identifier fallback (11 columns)
    information_source_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    information_source_identifier_type_system = Column(String, nullable=True)
    information_source_identifier_type_version = Column(String, nullable=True)
    information_source_identifier_type_code = Column(String, nullable=True)
    information_source_identifier_type_display = Column(String, nullable=True)
    information_source_identifier_type_user_selected = Column(Boolean, nullable=True)
    information_source_identifier_type_text = Column(String, nullable=True)
    information_source_identifier_system = Column(String, nullable=True)
    information_source_identifier_value = Column(String, nullable=True)
    information_source_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    information_source_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    identifiers = relationship(
        "MedicationStatementIdentifier",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    based_on = relationship(
        "MedicationStatementBasedOn",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    part_of = relationship(
        "MedicationStatementPartOf",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    status_reasons = relationship(
        "MedicationStatementStatusReason",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    category_codings = relationship(
        "MedicationStatementCategoryCoding",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    medication_codings = relationship(
        "MedicationStatementMedicationCoding",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    derived_from = relationship(
        "MedicationStatementDerivedFrom",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "MedicationStatementReasonCode",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "MedicationStatementReasonReference",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "MedicationStatementNote",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    dosages = relationship(
        "MedicationStatementDosage",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )

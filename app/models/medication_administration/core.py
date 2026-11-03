from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_administration.enums import (
    MedicationAdministrationContextReferenceType,
    MedicationAdministrationMedicationReferenceType,
    MedicationAdministrationRequestReferenceType,
    MedicationAdministrationStatus,
    MedicationAdministrationSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

_seq = Sequence(
    "medication_administration_pub_seq",
    start=580000,
    increment=1,
    metadata=Base.metadata,
)


class MedicationAdministrationModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationAdministration resource.

    Describes the event of a patient consuming or being administered a medication.
    """

    __tablename__ = "medication_administration"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_administration_id = Column(
        BigInteger,
        _seq,
        server_default=_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # instantiates (0..* uri)
    instantiates = Column(ARRAY(String), nullable=True)

    # status (1..1 code)
    status = Column(
        Enum(
            MedicationAdministrationStatus,
            name="medication_administration_status",
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
            MedicationAdministrationMedicationReferenceType,
            name="medication_administration_medication_reference_type",
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
            MedicationAdministrationSubjectReferenceType,
            name="medication_administration_subject_reference_type",
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
            MedicationAdministrationContextReferenceType,
            name="medication_administration_context_reference_type",
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

    # effective[x] (1..1 choice: dateTime | Period)
    effective_date_time = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # request (0..1 Reference(MedicationRequest))
    request_reference = Column(String, nullable=True)
    request_type = Column(
        Enum(
            MedicationAdministrationRequestReferenceType,
            name="medication_administration_request_reference_type",
        ),
        nullable=True,
    )
    request_id = Column(BigInteger, nullable=True, index=True)
    request_display = Column(String, nullable=True)

    # request.identifier fallback (11 columns)
    request_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    request_identifier_type_system = Column(String, nullable=True)
    request_identifier_type_version = Column(String, nullable=True)
    request_identifier_type_code = Column(String, nullable=True)
    request_identifier_type_display = Column(String, nullable=True)
    request_identifier_type_user_selected = Column(Boolean, nullable=True)
    request_identifier_type_text = Column(String, nullable=True)
    request_identifier_system = Column(String, nullable=True)
    request_identifier_value = Column(String, nullable=True)
    request_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    request_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # dosage (0..1 BackboneElement)
    dosage_text = Column(String, nullable=True)
    dosage_site_text = Column(String, nullable=True)
    dosage_route_text = Column(String, nullable=True)
    dosage_method_text = Column(String, nullable=True)

    # dosage.dose (0..1 SimpleQuantity)
    dosage_dose_value = Column(Numeric, nullable=True)
    dosage_dose_unit = Column(String, nullable=True)
    dosage_dose_system = Column(String, nullable=True)
    dosage_dose_code = Column(String, nullable=True)

    # dosage.rate[x] (0..1 choice: Ratio | SimpleQuantity)
    dosage_rate_ratio_numerator_value = Column(Numeric, nullable=True)
    dosage_rate_ratio_numerator_unit = Column(String, nullable=True)
    dosage_rate_ratio_numerator_system = Column(String, nullable=True)
    dosage_rate_ratio_numerator_code = Column(String, nullable=True)
    dosage_rate_ratio_denominator_value = Column(Numeric, nullable=True)
    dosage_rate_ratio_denominator_unit = Column(String, nullable=True)
    dosage_rate_ratio_denominator_system = Column(String, nullable=True)
    dosage_rate_ratio_denominator_code = Column(String, nullable=True)

    dosage_rate_quantity_value = Column(Numeric, nullable=True)
    dosage_rate_quantity_unit = Column(String, nullable=True)
    dosage_rate_quantity_system = Column(String, nullable=True)
    dosage_rate_quantity_code = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "MedicationAdministrationIdentifier",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    part_of = relationship(
        "MedicationAdministrationPartOf",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    status_reasons = relationship(
        "MedicationAdministrationStatusReason",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    category_codings = relationship(
        "MedicationAdministrationCategoryCoding",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    medication_codings = relationship(
        "MedicationAdministrationMedicationCoding",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    supporting_informations = relationship(
        "MedicationAdministrationSupportingInformation",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "MedicationAdministrationPerformer",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "MedicationAdministrationReasonCode",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "MedicationAdministrationReasonReference",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    devices = relationship(
        "MedicationAdministrationDevice",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "MedicationAdministrationNote",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    dosage_site_codings = relationship(
        "MedicationAdministrationDosageSiteCoding",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    dosage_route_codings = relationship(
        "MedicationAdministrationDosageRouteCoding",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    dosage_method_codings = relationship(
        "MedicationAdministrationDosageMethodCoding",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    event_history = relationship(
        "MedicationAdministrationEventHistory",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )

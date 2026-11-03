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
from app.models.medication_dispense.enums import (
    MedicationDispenseContextReferenceType,
    MedicationDispenseDestinationReferenceType,
    MedicationDispenseLocationReferenceType,
    MedicationDispenseMedicationReferenceType,
    MedicationDispenseStatus,
    MedicationDispenseStatusReasonReferenceType,
    MedicationDispenseSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin


class MedicationDispenseModel(TenantAuditMixin, Base):
    """MedicationDispense FHIR R4 resource table.

    https://www.hl7.org/fhir/R4/medicationdispense.html
    Public sequence block: 590000.
    """

    __tablename__ = "medication_dispense"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_id = Column(
        BigInteger,
        Sequence(
            "medication_dispense_pub_seq",
            start=590000,
            increment=1,
            metadata=Base.metadata,
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # status (1..1 code)
    status = Column(
        Enum(
            MedicationDispenseStatus,
            name="medication_dispense_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # statusReason[x] (0..1 choice: CodeableConcept | Reference(DetectedIssue))
    status_reason_codeable_concept_text = Column(String, nullable=True)

    status_reason_reference = Column(String, nullable=True)
    status_reason_reference_type = Column(
        Enum(
            MedicationDispenseStatusReasonReferenceType,
            name="medication_dispense_status_reason_reference_type",
        ),
        nullable=True,
    )
    status_reason_reference_id = Column(BigInteger, nullable=True, index=True)
    status_reason_reference_display = Column(String, nullable=True)

    status_reason_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    status_reason_reference_identifier_type_system = Column(String, nullable=True)
    status_reason_reference_identifier_type_version = Column(String, nullable=True)
    status_reason_reference_identifier_type_code = Column(String, nullable=True)
    status_reason_reference_identifier_type_display = Column(String, nullable=True)
    status_reason_reference_identifier_type_user_selected = Column(
        Boolean, nullable=True
    )
    status_reason_reference_identifier_type_text = Column(String, nullable=True)
    status_reason_reference_identifier_system = Column(String, nullable=True)
    status_reason_reference_identifier_value = Column(String, nullable=True)
    status_reason_reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    status_reason_reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    # category (0..1 CodeableConcept) — text flattened
    category_text = Column(String, nullable=True)

    # medication[x] (1..1 choice: CodeableConcept | Reference(Medication))
    medication_codeable_concept_text = Column(String, nullable=True)

    medication_reference = Column(String, nullable=True)
    medication_type = Column(
        Enum(
            MedicationDispenseMedicationReferenceType,
            name="medication_dispense_medication_reference_type",
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

    # subject (0..1 Reference(Patient | Group)) — 15 flattened columns
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            MedicationDispenseSubjectReferenceType,
            name="medication_dispense_subject_reference_type",
        ),
        nullable=True,
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

    # context (0..1 Reference(Encounter | EpisodeOfCare)) — 15 flattened columns
    context_reference = Column(String, nullable=True)
    context_type = Column(
        Enum(
            MedicationDispenseContextReferenceType,
            name="medication_dispense_context_reference_type",
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

    # location (0..1 Reference(Location)) — 15 flattened columns
    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(
            MedicationDispenseLocationReferenceType,
            name="medication_dispense_location_reference_type",
        ),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    location_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    location_identifier_type_system = Column(String, nullable=True)
    location_identifier_type_version = Column(String, nullable=True)
    location_identifier_type_code = Column(String, nullable=True)
    location_identifier_type_display = Column(String, nullable=True)
    location_identifier_type_user_selected = Column(Boolean, nullable=True)
    location_identifier_type_text = Column(String, nullable=True)
    location_identifier_system = Column(String, nullable=True)
    location_identifier_value = Column(String, nullable=True)
    location_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    location_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # type (0..1 CodeableConcept) — text flattened
    type_text = Column(String, nullable=True)

    # quantity (0..1 SimpleQuantity)
    quantity_value = Column(Numeric, nullable=True)
    quantity_unit = Column(String, nullable=True)
    quantity_system = Column(String, nullable=True)
    quantity_code = Column(String, nullable=True)

    # daysSupply (0..1 SimpleQuantity)
    days_supply_value = Column(Numeric, nullable=True)
    days_supply_unit = Column(String, nullable=True)
    days_supply_system = Column(String, nullable=True)
    days_supply_code = Column(String, nullable=True)

    # whenPrepared (0..1 dateTime)
    when_prepared = Column(DateTime(timezone=True), nullable=True)

    # whenHandedOver (0..1 dateTime)
    when_handed_over = Column(DateTime(timezone=True), nullable=True)

    # destination (0..1 Reference(Location)) — 15 flattened columns
    destination_reference = Column(String, nullable=True)
    destination_type = Column(
        Enum(
            MedicationDispenseDestinationReferenceType,
            name="medication_dispense_destination_reference_type",
        ),
        nullable=True,
    )
    destination_id = Column(BigInteger, nullable=True, index=True)
    destination_display = Column(String, nullable=True)

    destination_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    destination_identifier_type_system = Column(String, nullable=True)
    destination_identifier_type_version = Column(String, nullable=True)
    destination_identifier_type_code = Column(String, nullable=True)
    destination_identifier_type_display = Column(String, nullable=True)
    destination_identifier_type_user_selected = Column(Boolean, nullable=True)
    destination_identifier_type_text = Column(String, nullable=True)
    destination_identifier_system = Column(String, nullable=True)
    destination_identifier_value = Column(String, nullable=True)
    destination_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    destination_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # substitution (0..1 BackboneElement) — flattened fields for 0..1 sub-elements
    substitution_was_substituted = Column(Boolean, nullable=True)
    substitution_type_text = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "MedicationDispenseIdentifier",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    part_of = relationship(
        "MedicationDispensePartOf",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    status_reason_codings = relationship(
        "MedicationDispenseStatusReasonCoding",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    category_codings = relationship(
        "MedicationDispenseCategoryCoding",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    medication_codings = relationship(
        "MedicationDispenseMedicationCoding",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    supporting_informations = relationship(
        "MedicationDispenseSupportingInfo",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "MedicationDispensePerformer",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    authorizing_prescriptions = relationship(
        "MedicationDispenseAuthorizingPrescription",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "MedicationDispenseTypeCoding",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    receivers = relationship(
        "MedicationDispenseReceiver",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "MedicationDispenseNote",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    dosage_instructions = relationship(
        "MedicationDispenseDosageInstruction",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    substitution_type_codings = relationship(
        "MedicationDispenseSubstitutionTypeCoding",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    substitution_reasons = relationship(
        "MedicationDispenseSubstitutionReason",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    substitution_responsible_parties = relationship(
        "MedicationDispenseSubstitutionResponsibleParty",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    detected_issues = relationship(
        "MedicationDispenseDetectedIssue",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    event_history = relationship(
        "MedicationDispenseEventHistory",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )

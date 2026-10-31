from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.condition.enums import (
    ConditionAsserterReferenceType,
    ConditionQuantityComparator,
    ConditionRecorderReferenceType,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    SubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

condition_id_seq = Sequence(
    "condition_pub_seq", start=120000, metadata=Base.metadata
)


class ConditionModel(TenantAuditMixin, Base):
    """FHIR R4 Condition model.

    Represents clinical condition, problem, diagnosis, or other event, situation,
    issue, or clinical concept that has risen to a level of concern.
    """

    __tablename__ = "condition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_id = Column(
        BigInteger,
        condition_id_seq,
        server_default=condition_id_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )

    # clinicalStatus (0..1 CodeableConcept) — codings in condition_clinical_status_coding
    clinical_status_text = Column(String, nullable=True)

    # verificationStatus (0..1 CodeableConcept) — codings in condition_verification_status_coding
    verification_status_text = Column(String, nullable=True)

    # severity (0..1 CodeableConcept) — codings in condition_severity_coding
    severity_text = Column(String, nullable=True)

    # code (0..1 CodeableConcept) — codings in condition_code_coding
    code_text = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type", create_type=False),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # subject.identifier fallback
    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # encounter.identifier fallback
    encounter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)
    encounter_identifier_type_text = Column(String, nullable=True)

    # onset[x] (0..1 choice: dateTime | Age | Period | Range | string)
    onset_date_time = Column(DateTime(timezone=True), nullable=True)
    onset_age_value = Column(Numeric, nullable=True)
    onset_age_comparator = Column(
        Enum(ConditionQuantityComparator, name="condition_quantity_comparator"),
        nullable=True,
    )
    onset_age_unit = Column(String, nullable=True)
    onset_age_system = Column(String, nullable=True)
    onset_age_code = Column(String, nullable=True)
    onset_period_start = Column(DateTime(timezone=True), nullable=True)
    onset_period_end = Column(DateTime(timezone=True), nullable=True)
    onset_range_low_value = Column(Numeric, nullable=True)
    onset_range_low_unit = Column(String, nullable=True)
    onset_range_low_system = Column(String, nullable=True)
    onset_range_low_code = Column(String, nullable=True)
    onset_range_high_value = Column(Numeric, nullable=True)
    onset_range_high_unit = Column(String, nullable=True)
    onset_range_high_system = Column(String, nullable=True)
    onset_range_high_code = Column(String, nullable=True)
    onset_string = Column(String, nullable=True)

    # abatement[x] (0..1 choice: dateTime | Age | Period | Range | string)
    abatement_date_time = Column(DateTime(timezone=True), nullable=True)
    abatement_age_value = Column(Numeric, nullable=True)
    abatement_age_comparator = Column(
        Enum(ConditionQuantityComparator, name="condition_quantity_comparator"),
        nullable=True,
    )
    abatement_age_unit = Column(String, nullable=True)
    abatement_age_system = Column(String, nullable=True)
    abatement_age_code = Column(String, nullable=True)
    abatement_period_start = Column(DateTime(timezone=True), nullable=True)
    abatement_period_end = Column(DateTime(timezone=True), nullable=True)
    abatement_range_low_value = Column(Numeric, nullable=True)
    abatement_range_low_unit = Column(String, nullable=True)
    abatement_range_low_system = Column(String, nullable=True)
    abatement_range_low_code = Column(String, nullable=True)
    abatement_range_high_value = Column(Numeric, nullable=True)
    abatement_range_high_unit = Column(String, nullable=True)
    abatement_range_high_system = Column(String, nullable=True)
    abatement_range_high_code = Column(String, nullable=True)
    abatement_string = Column(String, nullable=True)

    # recordedDate (0..1 dateTime)
    recorded_date = Column(DateTime(timezone=True), nullable=True)

    # recorder (0..1 Reference(Practitioner | PractitionerRole | Patient | RelatedPerson))
    recorder_reference = Column(String, nullable=True)
    recorder_type = Column(
        Enum(ConditionRecorderReferenceType, name="condition_recorder_reference_type"),
        nullable=True,
    )
    recorder_id = Column(BigInteger, nullable=True, index=True)
    recorder_display = Column(String, nullable=True)

    # recorder.identifier fallback
    recorder_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    recorder_identifier_system = Column(String, nullable=True)
    recorder_identifier_value = Column(String, nullable=True)
    recorder_identifier_type_text = Column(String, nullable=True)

    # asserter (0..1 Reference(Practitioner | PractitionerRole | Patient | RelatedPerson))
    asserter_reference = Column(String, nullable=True)
    asserter_type = Column(
        Enum(ConditionAsserterReferenceType, name="condition_asserter_reference_type"),
        nullable=True,
    )
    asserter_id = Column(BigInteger, nullable=True, index=True)
    asserter_display = Column(String, nullable=True)

    # asserter.identifier fallback
    asserter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    asserter_identifier_system = Column(String, nullable=True)
    asserter_identifier_value = Column(String, nullable=True)
    asserter_identifier_type_text = Column(String, nullable=True)

    # Identifier fallback columns on Condition
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_type_text = Column(String, nullable=True)

    # DomainResource extension
    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "ConditionIdentifier",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    clinical_status_codings = relationship(
        "ConditionClinicalStatusCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    verification_status_codings = relationship(
        "ConditionVerificationStatusCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "ConditionCategory",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    severity_codings = relationship(
        "ConditionSeverityCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "ConditionCodeCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    body_sites = relationship(
        "ConditionBodySite",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    stages = relationship(
        "ConditionStage",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    evidence = relationship(
        "ConditionEvidence",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "ConditionNote",
        back_populates="condition",
        cascade="all, delete-orphan",
    )

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    MedicationRequestReferenceType,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.medication_request.enums import (
    MedicationRequestIntent,
    MedicationRequestMedicationReferenceType,
    MedicationRequestPerformerReferenceType,
    MedicationRequestPriority,
    MedicationRequestQuantityComparator,
    MedicationRequestRecorderReferenceType,
    MedicationRequestReportedReferenceType,
    MedicationRequestRequesterReferenceType,
    MedicationRequestStatus,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

medication_request_id_seq = Sequence(
    "medication_request_pub_seq", start=90000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class MedicationRequestModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationRequest — https://www.hl7.org/fhir/R4/medicationrequest.html

    An order or request for both supply of the medication and the
    instructions for administration of the medication to a patient.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout,
    same as QuestionnaireResponse/ServiceRequest: `tenant_id`/
    `created_by`/`updated_by` are plain, gateway-forwarded request fields.
    Keeps a plain `user_id` column.

    `groupIdentifier` (0..1 Identifier) is flattened directly onto this
    row, same shape as ServiceRequest.requisition. `statusReason`/
    `medicationCodeableConcept`/`performerType`/`courseOfTherapyType`/
    `substitution.allowed[x]`'s CodeableConcept variant/`substitution.
    reason` are each 0..1 CodeableConcept flattened with `_text` here,
    their own `coding[]` promoted to a dedicated direct-child table —
    same promotion as ServiceRequest.code/performerType/asNeededCodeableConcept.

    `dispenseRequest` and `substitution` (both 0..1 BackboneElement) are
    flattened directly onto this row with a `dispense_request_`/
    `substitution_` column prefix — neither repeats, so no child table is
    needed for either as a whole.

    `dosageInstruction` (0..* Dosage) is the one genuinely complex nested
    structure here — see DosageInstruction's own docstring (in
    dosage_instruction.py) for how its own Timing/doseAndRate/
    maxDosePerPeriod sub-fields are handled (raw JSONB, same deliberate
    scope decision as ServiceRequest's own `occurrence_timing`)."""

    __tablename__ = "medication_request"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    medication_request_id = Column(
        BigInteger,
        medication_request_id_seq,
        server_default=medication_request_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)

    # ── instantiatesCanonical / instantiatesUri ────────────────────────────
    instantiates_canonical = Column(ARRAY(String), nullable=True)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    # ── status / intent (1..1, required, modifier) ─────────────────────────
    status = Column(Enum(MedicationRequestStatus, name="medication_request_status"), nullable=False)
    status_reason_text = Column(String, nullable=True)
    intent = Column(Enum(MedicationRequestIntent, name="medication_request_intent"), nullable=False)

    # ── priority / doNotPerform ─────────────────────────────────────────────
    priority = Column(Enum(MedicationRequestPriority, name="medication_request_priority"), nullable=True)
    do_not_perform = Column(Boolean, nullable=True)

    # ── reported[x] (0..1 choice: boolean | Reference) ─────────────────────
    reported_boolean = Column(Boolean, nullable=True)
    reported_reference_reference = Column(String, nullable=True)
    reported_reference_type = Column(
        Enum(MedicationRequestReportedReferenceType, name="medication_request_reported_reference_type"),
        nullable=True,
    )
    reported_reference_id = Column(BigInteger, nullable=True, index=True)
    reported_reference_display = Column(String, nullable=True)
    reported_reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    reported_reference_identifier_type_system = Column(String, nullable=True)
    reported_reference_identifier_type_version = Column(String, nullable=True)
    reported_reference_identifier_type_code = Column(String, nullable=True)
    reported_reference_identifier_type_display = Column(String, nullable=True)
    reported_reference_identifier_type_text = Column(String, nullable=True)
    reported_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reported_reference_identifier_system = Column(String, nullable=True)
    reported_reference_identifier_value = Column(String, nullable=True)
    reported_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reported_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── medication[x] (1..1 required choice: CodeableConcept | Reference) ──
    medication_codeable_concept_text = Column(String, nullable=True)
    medication_reference_reference = Column(String, nullable=True)
    medication_reference_type = Column(
        Enum(MedicationRequestMedicationReferenceType, name="medication_request_medication_reference_type"),
        nullable=True,
    )
    medication_reference_id = Column(BigInteger, nullable=True, index=True)
    medication_reference_display = Column(String, nullable=True)
    medication_reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    medication_reference_identifier_type_system = Column(String, nullable=True)
    medication_reference_identifier_type_version = Column(String, nullable=True)
    medication_reference_identifier_type_code = Column(String, nullable=True)
    medication_reference_identifier_type_display = Column(String, nullable=True)
    medication_reference_identifier_type_text = Column(String, nullable=True)
    medication_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    medication_reference_identifier_system = Column(String, nullable=True)
    medication_reference_identifier_value = Column(String, nullable=True)
    medication_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    medication_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── subject (1..1 Reference(Patient|Group)) ────────────────────────────
    subject_reference = Column(String, nullable=True)
    subject_type = Column(Enum(SubjectReferenceType, name="subject_reference_type", create_type=False), nullable=True)
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)
    subject_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── encounter (0..1 Reference(Encounter)) ──────────────────────────────
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False), nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)
    encounter_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    encounter_identifier_type_system = Column(String, nullable=True)
    encounter_identifier_type_version = Column(String, nullable=True)
    encounter_identifier_type_code = Column(String, nullable=True)
    encounter_identifier_type_display = Column(String, nullable=True)
    encounter_identifier_type_text = Column(String, nullable=True)
    encounter_identifier_type_user_selected = Column(Boolean, nullable=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)
    encounter_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    encounter_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── authoredOn ───────────────────────────────────────────────────────────
    authored_on = Column(DateTime(timezone=True), nullable=True)

    # ── requester (0..1 Reference, polymorphic across 6 types) ────────────
    requester_reference = Column(String, nullable=True)
    requester_type = Column(
        Enum(MedicationRequestRequesterReferenceType, name="medication_request_requester_reference_type"),
        nullable=True,
    )
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_display = Column(String, nullable=True)
    requester_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    requester_identifier_type_system = Column(String, nullable=True)
    requester_identifier_type_version = Column(String, nullable=True)
    requester_identifier_type_code = Column(String, nullable=True)
    requester_identifier_type_display = Column(String, nullable=True)
    requester_identifier_type_text = Column(String, nullable=True)
    requester_identifier_type_user_selected = Column(Boolean, nullable=True)
    requester_identifier_system = Column(String, nullable=True)
    requester_identifier_value = Column(String, nullable=True)
    requester_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    requester_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── performer (0..1 Reference, polymorphic across 7 types) ─────────────
    performer_reference = Column(String, nullable=True)
    performer_type = Column(
        Enum(MedicationRequestPerformerReferenceType, name="medication_request_performer_reference_type"),
        nullable=True,
    )
    performer_id = Column(BigInteger, nullable=True, index=True)
    performer_display = Column(String, nullable=True)
    performer_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    performer_identifier_type_system = Column(String, nullable=True)
    performer_identifier_type_version = Column(String, nullable=True)
    performer_identifier_type_code = Column(String, nullable=True)
    performer_identifier_type_display = Column(String, nullable=True)
    performer_identifier_type_text = Column(String, nullable=True)
    performer_identifier_type_user_selected = Column(Boolean, nullable=True)
    performer_identifier_system = Column(String, nullable=True)
    performer_identifier_value = Column(String, nullable=True)
    performer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    performer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── performerType (0..1 CodeableConcept) ────────────────────────────────
    performer_type_text = Column(String, nullable=True)

    # ── recorder (0..1 Reference(Practitioner|PractitionerRole)) ───────────
    recorder_reference = Column(String, nullable=True)
    recorder_type = Column(
        Enum(MedicationRequestRecorderReferenceType, name="medication_request_recorder_reference_type"),
        nullable=True,
    )
    recorder_id = Column(BigInteger, nullable=True, index=True)
    recorder_display = Column(String, nullable=True)
    recorder_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    recorder_identifier_type_system = Column(String, nullable=True)
    recorder_identifier_type_version = Column(String, nullable=True)
    recorder_identifier_type_code = Column(String, nullable=True)
    recorder_identifier_type_display = Column(String, nullable=True)
    recorder_identifier_type_text = Column(String, nullable=True)
    recorder_identifier_type_user_selected = Column(Boolean, nullable=True)
    recorder_identifier_system = Column(String, nullable=True)
    recorder_identifier_value = Column(String, nullable=True)
    recorder_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    recorder_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── groupIdentifier (0..1 Identifier) — flattened ──────────────────────
    group_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    group_identifier_type_text = Column(String, nullable=True)
    group_identifier_system = Column(String, nullable=True)
    group_identifier_value = Column(String, nullable=True)
    group_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    group_identifier_period_end = Column(DateTime(timezone=True), nullable=True)
    group_identifier_assigner_reference = Column(String, nullable=True)
    group_identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    group_identifier_assigner_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False), nullable=True
    )
    group_identifier_assigner_display = Column(String, nullable=True)
    group_identifier_assigner_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    group_identifier_assigner_identifier_type_system = Column(String, nullable=True)
    group_identifier_assigner_identifier_type_version = Column(String, nullable=True)
    group_identifier_assigner_identifier_type_code = Column(String, nullable=True)
    group_identifier_assigner_identifier_type_display = Column(String, nullable=True)
    group_identifier_assigner_identifier_type_text = Column(String, nullable=True)
    group_identifier_assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    group_identifier_assigner_identifier_system = Column(String, nullable=True)
    group_identifier_assigner_identifier_value = Column(String, nullable=True)
    group_identifier_assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    group_identifier_assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── courseOfTherapyType (0..1 CodeableConcept) ──────────────────────────
    course_of_therapy_type_text = Column(String, nullable=True)

    # ── dispenseRequest (0..1 BackboneElement) — flattened ─────────────────
    dispense_request_initial_fill_quantity_value = Column(Numeric, nullable=True)
    dispense_request_initial_fill_quantity_comparator = Column(
        Enum(MedicationRequestQuantityComparator, name="medication_request_quantity_comparator"), nullable=True
    )
    dispense_request_initial_fill_quantity_unit = Column(String, nullable=True)
    dispense_request_initial_fill_quantity_system = Column(String, nullable=True)
    dispense_request_initial_fill_quantity_code = Column(String, nullable=True)

    dispense_request_initial_fill_duration_value = Column(Numeric, nullable=True)
    dispense_request_initial_fill_duration_comparator = Column(
        Enum(MedicationRequestQuantityComparator, name="medication_request_quantity_comparator", create_type=False), nullable=True
    )
    dispense_request_initial_fill_duration_unit = Column(String, nullable=True)
    dispense_request_initial_fill_duration_system = Column(String, nullable=True)
    dispense_request_initial_fill_duration_code = Column(String, nullable=True)

    dispense_request_dispense_interval_value = Column(Numeric, nullable=True)
    dispense_request_dispense_interval_comparator = Column(
        Enum(MedicationRequestQuantityComparator, name="medication_request_quantity_comparator", create_type=False), nullable=True
    )
    dispense_request_dispense_interval_unit = Column(String, nullable=True)
    dispense_request_dispense_interval_system = Column(String, nullable=True)
    dispense_request_dispense_interval_code = Column(String, nullable=True)

    dispense_request_validity_period_start = Column(DateTime(timezone=True), nullable=True)
    dispense_request_validity_period_end = Column(DateTime(timezone=True), nullable=True)

    dispense_request_number_of_repeats_allowed = Column(Integer, nullable=True)

    dispense_request_quantity_value = Column(Numeric, nullable=True)
    dispense_request_quantity_comparator = Column(
        Enum(MedicationRequestQuantityComparator, name="medication_request_quantity_comparator", create_type=False), nullable=True
    )
    dispense_request_quantity_unit = Column(String, nullable=True)
    dispense_request_quantity_system = Column(String, nullable=True)
    dispense_request_quantity_code = Column(String, nullable=True)

    dispense_request_expected_supply_duration_value = Column(Numeric, nullable=True)
    dispense_request_expected_supply_duration_comparator = Column(
        Enum(MedicationRequestQuantityComparator, name="medication_request_quantity_comparator", create_type=False), nullable=True
    )
    dispense_request_expected_supply_duration_unit = Column(String, nullable=True)
    dispense_request_expected_supply_duration_system = Column(String, nullable=True)
    dispense_request_expected_supply_duration_code = Column(String, nullable=True)

    dispense_request_performer_reference = Column(String, nullable=True)
    dispense_request_performer_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False), nullable=True
    )
    dispense_request_performer_id = Column(BigInteger, nullable=True, index=True)
    dispense_request_performer_display = Column(String, nullable=True)
    dispense_request_performer_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    dispense_request_performer_identifier_type_system = Column(String, nullable=True)
    dispense_request_performer_identifier_type_version = Column(String, nullable=True)
    dispense_request_performer_identifier_type_code = Column(String, nullable=True)
    dispense_request_performer_identifier_type_display = Column(String, nullable=True)
    dispense_request_performer_identifier_type_text = Column(String, nullable=True)
    dispense_request_performer_identifier_type_user_selected = Column(Boolean, nullable=True)
    dispense_request_performer_identifier_system = Column(String, nullable=True)
    dispense_request_performer_identifier_value = Column(String, nullable=True)
    dispense_request_performer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    dispense_request_performer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── substitution (0..1 BackboneElement) — flattened ─────────────────────
    substitution_allowed_boolean = Column(Boolean, nullable=True)
    substitution_allowed_codeable_concept_text = Column(String, nullable=True)
    substitution_reason_text = Column(String, nullable=True)

    # ── priorPrescription (0..1 Reference(MedicationRequest)) ─────────────
    prior_prescription_reference = Column(String, nullable=True)
    prior_prescription_type = Column(
        Enum(MedicationRequestReferenceType, name="medication_request_reference_type", create_type=False), nullable=True
    )
    prior_prescription_id = Column(BigInteger, nullable=True, index=True)
    prior_prescription_display = Column(String, nullable=True)
    prior_prescription_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    prior_prescription_identifier_type_system = Column(String, nullable=True)
    prior_prescription_identifier_type_version = Column(String, nullable=True)
    prior_prescription_identifier_type_code = Column(String, nullable=True)
    prior_prescription_identifier_type_display = Column(String, nullable=True)
    prior_prescription_identifier_type_text = Column(String, nullable=True)
    prior_prescription_identifier_type_user_selected = Column(Boolean, nullable=True)
    prior_prescription_identifier_system = Column(String, nullable=True)
    prior_prescription_identifier_value = Column(String, nullable=True)
    prior_prescription_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    prior_prescription_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # ── Relationships ─────────────────────────────────────────────────────

    status_reason_codings = relationship(
        "MedicationRequestStatusReasonCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    medication_codings = relationship(
        "MedicationRequestMedicationCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    performer_type_codings = relationship(
        "MedicationRequestPerformerTypeCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    group_identifier_type_codings = relationship(
        "MedicationRequestGroupIdentifierTypeCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    course_of_therapy_type_codings = relationship(
        "MedicationRequestCourseOfTherapyTypeCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    substitution_allowed_codings = relationship(
        "MedicationRequestSubstitutionAllowedCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    substitution_reason_codings = relationship(
        "MedicationRequestSubstitutionReasonCoding", back_populates="medication_request", cascade="all, delete-orphan"
    )
    identifiers = relationship(
        "MedicationRequestIdentifier", back_populates="medication_request", cascade="all, delete-orphan"
    )
    categories = relationship(
        "MedicationRequestCategory", back_populates="medication_request", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "MedicationRequestReasonCode", back_populates="medication_request", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "MedicationRequestReasonReference", back_populates="medication_request", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "MedicationRequestBasedOn", back_populates="medication_request", cascade="all, delete-orphan"
    )
    insurances = relationship(
        "MedicationRequestInsurance", back_populates="medication_request", cascade="all, delete-orphan"
    )
    supporting_informations = relationship(
        "MedicationRequestSupportingInformation", back_populates="medication_request", cascade="all, delete-orphan"
    )
    notes = relationship(
        "MedicationRequestNote", back_populates="medication_request", cascade="all, delete-orphan"
    )
    dosage_instructions = relationship(
        "MedicationRequestDosageInstruction", back_populates="medication_request", cascade="all, delete-orphan"
    )
    detected_issues = relationship(
        "MedicationRequestDetectedIssue", back_populates="medication_request", cascade="all, delete-orphan"
    )
    event_histories = relationship(
        "MedicationRequestEventHistory", back_populates="medication_request", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Direct-child coding tables for the main row's own 0..1 CodeableConcepts
# ---------------------------------------------------------------------------


class MedicationRequestStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.statusReason.coding (0..*)."""

    __tablename__ = "medication_request_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="status_reason_codings")


class MedicationRequestMedicationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.medicationCodeableConcept.coding (0..*)."""

    __tablename__ = "medication_request_medication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="medication_codings")


class MedicationRequestPerformerTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.performerType.coding (0..*)."""

    __tablename__ = "medication_request_performer_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="performer_type_codings")


class MedicationRequestGroupIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.groupIdentifier.type.coding (0..*)."""

    __tablename__ = "medication_request_group_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="group_identifier_type_codings")


class MedicationRequestCourseOfTherapyTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.courseOfTherapyType.coding (0..*)."""

    __tablename__ = "medication_request_course_of_therapy_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="course_of_therapy_type_codings")


class MedicationRequestSubstitutionAllowedCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.substitution.allowedCodeableConcept.coding (0..*)."""

    __tablename__ = "medication_request_substitution_allowed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="substitution_allowed_codings")


class MedicationRequestSubstitutionReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of MedicationRequest.substitution.reason.coding (0..*)."""

    __tablename__ = "medication_request_substitution_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    medication_request = relationship("MedicationRequestModel", back_populates="substitution_reason_codings")

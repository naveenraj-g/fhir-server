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
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import EncounterReferenceType, IdentifierUse
from app.models.observation.enums import (
    ObservationDeviceReferenceType,
    ObservationQuantityComparator,
    ObservationSpecimenReferenceType,
    ObservationStatus,
    ObservationSubjectReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

observation_id_seq = Sequence(
    "observation_pub_seq", start=160000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class ObservationModel(TenantAuditMixin, Base):
    """FHIR R4 Observation — https://www.hl7.org/fhir/R4/observation.html

    Measurements and simple assertions made about a patient, device or
    other subject.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout,
    same as QuestionnaireResponse/ServiceRequest/MedicationRequest:
    `tenant_id`/`created_by`/`updated_by` are plain, gateway-forwarded
    request fields. Keeps a plain `user_id` column.

    `code`/`valueCodeableConcept`/`dataAbsentReason`/`bodySite`/`method`
    (each 0..1 or 1..1 CodeableConcept) are flattened with `_text` here,
    their own `coding[]` promoted to a dedicated direct-child table —
    same promotion pattern as every other 0..1 CodeableConcept in this
    codebase (ServiceRequest.code, MedicationRequest.medicationCodeableConcept,
    etc).

    `value[x]` (11 choice variants) is fully flattened: `valueQuantity`/
    `valueRange`/`valueRatio`/`valueSampledData` each get their own
    column group (Range/SampledData use SimpleQuantity sub-fields, which
    forbid `comparator` entirely — no column for it; Quantity/Ratio's own
    Quantity components DO carry `comparator`). This mirrors
    ServiceRequest's own fully-flattened `quantityRatio` — unlike
    MedicationRequest's Dosage sub-fields, no FHIR datatype here is
    complex/rare enough to justify raw JSONB, with the sole exception of
    `effectiveTiming` (Timing is FHIR's most structurally complex
    datatype — same deliberate scope decision as ServiceRequest's own
    `occurrenceTiming` and MedicationRequest.dosageInstruction.timing).
    """

    __tablename__ = "observation"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    observation_id = Column(
        BigInteger,
        observation_id_seq,
        server_default=observation_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )


    # ── status (1..1, required, modifier) ──────────────────────────────────
    status = Column(Enum(ObservationStatus, name="observation_status"), nullable=False)

    # ── code (1..1 CodeableConcept) ─────────────────────────────────────────
    code_text = Column(String, nullable=True)

    # ── subject (0..1 Reference(Patient|Group|Device|Location)) ───────────
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(ObservationSubjectReferenceType, name="observation_subject_reference_type"),
        nullable=True,
    )
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

    # ── effective[x] (0..1 choice: dateTime | Period | Timing | instant) ──
    effective_date_time = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)
    effective_timing = Column(JSONB, nullable=True)
    effective_instant = Column(DateTime(timezone=True), nullable=True)

    # ── issued (0..1 instant) ────────────────────────────────────────────────
    issued = Column(DateTime(timezone=True), nullable=True)

    # ── value[x] (0..1 choice: 11 variants) ────────────────────────────────
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator"), nullable=True
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    value_codeable_concept_text = Column(String, nullable=True)

    value_string = Column(String, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_integer = Column(Integer, nullable=True)

    value_range_low_value = Column(Numeric, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_low_system = Column(String, nullable=True)
    value_range_low_code = Column(String, nullable=True)
    value_range_high_value = Column(Numeric, nullable=True)
    value_range_high_unit = Column(String, nullable=True)
    value_range_high_system = Column(String, nullable=True)
    value_range_high_code = Column(String, nullable=True)

    value_ratio_numerator_value = Column(Numeric, nullable=True)
    value_ratio_numerator_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator", create_type=False), nullable=True
    )
    value_ratio_numerator_unit = Column(String, nullable=True)
    value_ratio_numerator_system = Column(String, nullable=True)
    value_ratio_numerator_code = Column(String, nullable=True)
    value_ratio_denominator_value = Column(Numeric, nullable=True)
    value_ratio_denominator_comparator = Column(
        Enum(ObservationQuantityComparator, name="observation_quantity_comparator", create_type=False), nullable=True
    )
    value_ratio_denominator_unit = Column(String, nullable=True)
    value_ratio_denominator_system = Column(String, nullable=True)
    value_ratio_denominator_code = Column(String, nullable=True)

    value_sampled_data_origin_value = Column(Numeric, nullable=True)
    value_sampled_data_origin_unit = Column(String, nullable=True)
    value_sampled_data_origin_system = Column(String, nullable=True)
    value_sampled_data_origin_code = Column(String, nullable=True)
    value_sampled_data_period = Column(Numeric, nullable=True)
    value_sampled_data_factor = Column(Numeric, nullable=True)
    value_sampled_data_lower_limit = Column(Numeric, nullable=True)
    value_sampled_data_upper_limit = Column(Numeric, nullable=True)
    value_sampled_data_dimensions = Column(Integer, nullable=True)
    value_sampled_data_data = Column(Text, nullable=True)

    value_time = Column(Time, nullable=True)
    value_date_time = Column(DateTime(timezone=True), nullable=True)
    value_period_start = Column(DateTime(timezone=True), nullable=True)
    value_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── dataAbsentReason (0..1 CodeableConcept) ────────────────────────────
    data_absent_reason_text = Column(String, nullable=True)

    # ── bodySite (0..1 CodeableConcept) ────────────────────────────────────
    body_site_text = Column(String, nullable=True)

    # ── method (0..1 CodeableConcept) ──────────────────────────────────────
    method_text = Column(String, nullable=True)

    # ── specimen (0..1 Reference(Specimen)) ────────────────────────────────
    specimen_reference = Column(String, nullable=True)
    specimen_type = Column(Enum(ObservationSpecimenReferenceType, name="observation_specimen_reference_type"), nullable=True)
    specimen_id = Column(BigInteger, nullable=True, index=True)
    specimen_display = Column(String, nullable=True)
    specimen_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    specimen_identifier_type_system = Column(String, nullable=True)
    specimen_identifier_type_version = Column(String, nullable=True)
    specimen_identifier_type_code = Column(String, nullable=True)
    specimen_identifier_type_display = Column(String, nullable=True)
    specimen_identifier_type_text = Column(String, nullable=True)
    specimen_identifier_type_user_selected = Column(Boolean, nullable=True)
    specimen_identifier_system = Column(String, nullable=True)
    specimen_identifier_value = Column(String, nullable=True)
    specimen_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    specimen_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── device (0..1 Reference(Device|DeviceMetric)) ───────────────────────
    device_reference = Column(String, nullable=True)
    device_type = Column(Enum(ObservationDeviceReferenceType, name="observation_device_reference_type"), nullable=True)
    device_id = Column(BigInteger, nullable=True, index=True)
    device_display = Column(String, nullable=True)
    device_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    device_identifier_type_system = Column(String, nullable=True)
    device_identifier_type_version = Column(String, nullable=True)
    device_identifier_type_code = Column(String, nullable=True)
    device_identifier_type_display = Column(String, nullable=True)
    device_identifier_type_text = Column(String, nullable=True)
    device_identifier_type_user_selected = Column(Boolean, nullable=True)
    device_identifier_system = Column(String, nullable=True)
    device_identifier_value = Column(String, nullable=True)
    device_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    device_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # ── Relationships ─────────────────────────────────────────────────────

    code_codings = relationship(
        "ObservationCodeCoding", back_populates="observation", cascade="all, delete-orphan"
    )
    value_codeable_concept_codings = relationship(
        "ObservationValueCodeableConceptCoding", back_populates="observation", cascade="all, delete-orphan"
    )
    data_absent_reason_codings = relationship(
        "ObservationDataAbsentReasonCoding", back_populates="observation", cascade="all, delete-orphan"
    )
    body_site_codings = relationship(
        "ObservationBodySiteCoding", back_populates="observation", cascade="all, delete-orphan"
    )
    method_codings = relationship(
        "ObservationMethodCoding", back_populates="observation", cascade="all, delete-orphan"
    )
    identifiers = relationship(
        "ObservationIdentifier", back_populates="observation", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "ObservationBasedOn", back_populates="observation", cascade="all, delete-orphan"
    )
    part_ofs = relationship(
        "ObservationPartOf", back_populates="observation", cascade="all, delete-orphan"
    )
    categories = relationship(
        "ObservationCategory", back_populates="observation", cascade="all, delete-orphan"
    )
    focuses = relationship(
        "ObservationFocus", back_populates="observation", cascade="all, delete-orphan"
    )
    performers = relationship(
        "ObservationPerformer", back_populates="observation", cascade="all, delete-orphan"
    )
    interpretations = relationship(
        "ObservationInterpretation", back_populates="observation", cascade="all, delete-orphan"
    )
    notes = relationship(
        "ObservationNote", back_populates="observation", cascade="all, delete-orphan"
    )
    reference_ranges = relationship(
        "ObservationReferenceRange", back_populates="observation", cascade="all, delete-orphan"
    )
    has_members = relationship(
        "ObservationHasMember", back_populates="observation", cascade="all, delete-orphan"
    )
    derived_froms = relationship(
        "ObservationDerivedFrom", back_populates="observation", cascade="all, delete-orphan"
    )
    components = relationship(
        "ObservationComponent", back_populates="observation", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Direct-child coding tables for the main row's own 0..1 CodeableConcepts
# ---------------------------------------------------------------------------


class ObservationCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.code.coding (0..*)."""

    __tablename__ = "observation_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    observation = relationship("ObservationModel", back_populates="code_codings")


class ObservationValueCodeableConceptCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.valueCodeableConcept.coding (0..*)."""

    __tablename__ = "observation_value_codeable_concept_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    observation = relationship("ObservationModel", back_populates="value_codeable_concept_codings")


class ObservationDataAbsentReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.dataAbsentReason.coding (0..*)."""

    __tablename__ = "observation_data_absent_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    observation = relationship("ObservationModel", back_populates="data_absent_reason_codings")


class ObservationBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.bodySite.coding (0..*)."""

    __tablename__ = "observation_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    observation = relationship("ObservationModel", back_populates="body_site_codings")


class ObservationMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.method.coding (0..*)."""

    __tablename__ = "observation_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    observation = relationship("ObservationModel", back_populates="method_codings")

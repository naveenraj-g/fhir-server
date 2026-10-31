from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import EncounterReferenceType, IdentifierUse, OrganizationReferenceType
from app.models.service_request.enums import (
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestQuantityComparator,
    ServiceRequestRequesterReferenceType,
    ServiceRequestStatus,
    ServiceRequestSubjectReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

service_request_id_seq = Sequence(
    "service_request_pub_seq", start=80000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class ServiceRequestModel(TenantAuditMixin, Base):
    """FHIR R4 ServiceRequest — https://www.hl7.org/fhir/R4/servicerequest.html

    A record of a request for a procedure or diagnostic/other service to
    be performed.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout,
    same as QuestionnaireResponse (see that resource's own docstring):
    `tenant_id`/`created_by`/`updated_by` are plain, gateway-forwarded
    request fields. Keeps a plain `user_id` column.

    `requisition` (0..1 Identifier) is flattened directly onto this row,
    same shape as QuestionnaireResponse.identifier — its own `.type`
    CodeableConcept still gets a real child coding table
    (ServiceRequestRequisitionTypeCoding) regardless of the 0..1
    cardinality. `code`/`asNeeded[x]`'s CodeableConcept variant/
    `performerType` are each 0..1 CodeableConcept flattened with `_text`
    here, their own `coding[]` promoted to a dedicated child table
    (ServiceRequestCodeCoding/ServiceRequestAsNeededCoding/
    ServiceRequestPerformerTypeCoding, all below) — same
    cancelationReason/appointmentType-style promotion Appointment uses.

    `quantity[x]` (0..1, choice of Quantity | Ratio | Range) is fully
    flattened: `quantity_quantity_*` (a plain Quantity), `quantity_ratio_
    numerator_*`/`_denominator_*` (two Quantities, Ratio's first use in
    this codebase), `quantity_range_low_*`/`_high_*` (a Range, same shape
    as Questionnaire.useContext's own Range flattening). `occurrence[x]`
    (0..1, choice of dateTime | Period | Timing) flattens the dateTime/
    Period variants the usual way; the Timing variant — FHIR's most
    structurally complex datatype (a `repeat` BackboneElement with ~15
    sub-fields plus `event[]`/`code`) — is stored as a single raw JSONB
    blob (`occurrence_timing`) instead of being fully exploded into
    columns, a deliberate scope decision given how rarely Timing is
    actually populated in practice; the mapper passes it through
    verbatim rather than reconstructing it field-by-field.

    `subject` (1..1, required — but still DB-nullable, like every other
    Reference field in this codebase; the FHIR validator layer enforces
    the "required" half, not a DB `NOT NULL`) and `requester` (0..1) are
    both flattened Reference fields with the standard `{prefix}_
    reference`/`_type`/`_id`/`_display` + `{prefix}_identifier_*`
    logical-reference fallback shape. `subject` is a small, finite
    4-type set (own enum below); `requester` likewise.
    """

    __tablename__ = "service_request"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    service_request_id = Column(
        BigInteger,
        service_request_id_seq,
        server_default=service_request_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Plain, gateway-forwarded user_id — default pattern, not derived from
    # any JWT.

    # ── instantiatesCanonical (0..* canonical) / instantiatesUri (0..* uri) ──
    # Plain canonical/uri string arrays, not flattened References — same
    # convention as Questionnaire.derivedFrom.
    instantiates_canonical = Column(ARRAY(String), nullable=True)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    # ── requisition (0..1 Identifier) — flattened ─────────────────────────

    requisition_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    requisition_type_text = Column(String, nullable=True)
    requisition_system = Column(String, nullable=True)
    requisition_value = Column(String, nullable=True)
    requisition_period_start = Column(DateTime(timezone=True), nullable=True)
    requisition_period_end = Column(DateTime(timezone=True), nullable=True)

    requisition_assigner_reference = Column(String, nullable=True)
    requisition_assigner_id = Column(BigInteger, nullable=True, index=True)
    requisition_assigner_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
        nullable=True,
    )
    requisition_assigner_display = Column(String, nullable=True)

    requisition_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    requisition_assigner_identifier_type_system = Column(String, nullable=True)
    requisition_assigner_identifier_type_version = Column(String, nullable=True)
    requisition_assigner_identifier_type_code = Column(String, nullable=True)
    requisition_assigner_identifier_type_display = Column(String, nullable=True)
    requisition_assigner_identifier_type_text = Column(String, nullable=True)
    requisition_assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    requisition_assigner_identifier_system = Column(String, nullable=True)
    requisition_assigner_identifier_value = Column(String, nullable=True)
    requisition_assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    requisition_assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── status / intent (1..1 code, required, modifier) ───────────────────

    status = Column(Enum(ServiceRequestStatus, name="service_request_status"), nullable=False)
    intent = Column(Enum(ServiceRequestIntent, name="service_request_intent"), nullable=False)

    # ── priority (0..1 code) ───────────────────────────────────────────────

    priority = Column(Enum(ServiceRequestPriority, name="service_request_priority"), nullable=True)

    # ── doNotPerform (0..1 boolean, modifier) ──────────────────────────────

    do_not_perform = Column(Boolean, nullable=True)

    # ── code (0..1 CodeableConcept) — text flattened, coding[] promoted ───

    code_text = Column(String, nullable=True)

    # ── quantity[x] (0..1 choice: Quantity | Ratio | Range) ────────────────

    quantity_quantity_value = Column(Numeric, nullable=True)
    quantity_quantity_comparator = Column(
        Enum(ServiceRequestQuantityComparator, name="service_request_quantity_comparator"),
        nullable=True,
    )
    quantity_quantity_unit = Column(String, nullable=True)
    quantity_quantity_system = Column(String, nullable=True)
    quantity_quantity_code = Column(String, nullable=True)

    quantity_ratio_numerator_value = Column(Numeric, nullable=True)
    quantity_ratio_numerator_comparator = Column(
        Enum(
            ServiceRequestQuantityComparator,
            name="service_request_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    quantity_ratio_numerator_unit = Column(String, nullable=True)
    quantity_ratio_numerator_system = Column(String, nullable=True)
    quantity_ratio_numerator_code = Column(String, nullable=True)
    quantity_ratio_denominator_value = Column(Numeric, nullable=True)
    quantity_ratio_denominator_comparator = Column(
        Enum(
            ServiceRequestQuantityComparator,
            name="service_request_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    quantity_ratio_denominator_unit = Column(String, nullable=True)
    quantity_ratio_denominator_system = Column(String, nullable=True)
    quantity_ratio_denominator_code = Column(String, nullable=True)

    quantity_range_low_value = Column(Numeric, nullable=True)
    quantity_range_low_unit = Column(String, nullable=True)
    quantity_range_low_system = Column(String, nullable=True)
    quantity_range_low_code = Column(String, nullable=True)
    quantity_range_high_value = Column(Numeric, nullable=True)
    quantity_range_high_unit = Column(String, nullable=True)
    quantity_range_high_system = Column(String, nullable=True)
    quantity_range_high_code = Column(String, nullable=True)

    # ── subject (1..1 Reference, polymorphic across 4 types) ──────────────

    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(ServiceRequestSubjectReferenceType, name="service_request_subject_reference_type"),
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
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False),
        nullable=True,
    )
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

    # ── occurrence[x] (0..1 choice: dateTime | Period | Timing) ───────────

    occurrence_date_time = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_end = Column(DateTime(timezone=True), nullable=True)
    # Raw Timing BackboneElement, verbatim — see class docstring.
    occurrence_timing = Column(JSONB, nullable=True)

    # ── asNeeded[x] (0..1 choice: boolean | CodeableConcept) ───────────────

    as_needed_boolean = Column(Boolean, nullable=True)
    as_needed_codeable_concept_text = Column(String, nullable=True)

    # ── authoredOn (0..1 dateTime) ─────────────────────────────────────────

    authored_on = Column(DateTime(timezone=True), nullable=True)

    # ── requester (0..1 Reference, polymorphic across 6 types) ────────────

    requester_reference = Column(String, nullable=True)
    requester_type = Column(
        Enum(ServiceRequestRequesterReferenceType, name="service_request_requester_reference_type"),
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

    # ── performerType (0..1 CodeableConcept) — text flattened ─────────────

    performer_type_text = Column(String, nullable=True)

    # ── patientInstruction (0..1 string) ───────────────────────────────────

    patient_instruction = Column(Text, nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not resource-specific). Same shape as
    # every other resource's extension column.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above.

    # ── Relationships ─────────────────────────────────────────────────────

    requisition_type_codings = relationship(
        "ServiceRequestRequisitionTypeCoding", back_populates="service_request", cascade="all, delete-orphan"
    )
    code_codings = relationship(
        "ServiceRequestCodeCoding", back_populates="service_request", cascade="all, delete-orphan"
    )
    as_needed_codings = relationship(
        "ServiceRequestAsNeededCoding", back_populates="service_request", cascade="all, delete-orphan"
    )
    performer_type_codings = relationship(
        "ServiceRequestPerformerTypeCoding", back_populates="service_request", cascade="all, delete-orphan"
    )
    identifiers = relationship(
        "ServiceRequestIdentifier", back_populates="service_request", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "ServiceRequestBasedOn", back_populates="service_request", cascade="all, delete-orphan"
    )
    replaces = relationship(
        "ServiceRequestReplaces", back_populates="service_request", cascade="all, delete-orphan"
    )
    categories = relationship(
        "ServiceRequestCategory", back_populates="service_request", cascade="all, delete-orphan"
    )
    order_details = relationship(
        "ServiceRequestOrderDetail", back_populates="service_request", cascade="all, delete-orphan"
    )
    location_codes = relationship(
        "ServiceRequestLocationCode", back_populates="service_request", cascade="all, delete-orphan"
    )
    location_references = relationship(
        "ServiceRequestLocationReference", back_populates="service_request", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "ServiceRequestReasonCode", back_populates="service_request", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "ServiceRequestReasonReference", back_populates="service_request", cascade="all, delete-orphan"
    )
    insurances = relationship(
        "ServiceRequestInsurance", back_populates="service_request", cascade="all, delete-orphan"
    )
    supporting_infos = relationship(
        "ServiceRequestSupportingInfo", back_populates="service_request", cascade="all, delete-orphan"
    )
    specimens = relationship(
        "ServiceRequestSpecimen", back_populates="service_request", cascade="all, delete-orphan"
    )
    relevant_histories = relationship(
        "ServiceRequestRelevantHistory", back_populates="service_request", cascade="all, delete-orphan"
    )
    notes = relationship(
        "ServiceRequestNote", back_populates="service_request", cascade="all, delete-orphan"
    )
    performers = relationship(
        "ServiceRequestPerformer", back_populates="service_request", cascade="all, delete-orphan"
    )
    body_sites = relationship(
        "ServiceRequestBodySite", back_populates="service_request", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# requisition.type.coding (0..*) — direct child of main row (requisition
# itself is 0..1 and flattened, see class docstring above)
# ---------------------------------------------------------------------------


class ServiceRequestRequisitionTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.requisition.type.coding (0..*)."""

    __tablename__ = "service_request_requisition_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    service_request = relationship("ServiceRequestModel", back_populates="requisition_type_codings")


# ---------------------------------------------------------------------------
# code.coding (0..*) — direct child of main row
# ---------------------------------------------------------------------------


class ServiceRequestCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.code.coding (0..*)."""

    __tablename__ = "service_request_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    service_request = relationship("ServiceRequestModel", back_populates="code_codings")


# ---------------------------------------------------------------------------
# asNeededCodeableConcept.coding (0..*) — direct child of main row
# ---------------------------------------------------------------------------


class ServiceRequestAsNeededCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.asNeededCodeableConcept.coding (0..*)."""

    __tablename__ = "service_request_as_needed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    service_request = relationship("ServiceRequestModel", back_populates="as_needed_codings")


# ---------------------------------------------------------------------------
# performerType.coding (0..*) — direct child of main row
# ---------------------------------------------------------------------------


class ServiceRequestPerformerTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of ServiceRequest.performerType.coding (0..*)."""

    __tablename__ = "service_request_performer_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    service_request = relationship("ServiceRequestModel", back_populates="performer_type_codings")

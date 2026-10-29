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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import (
    EncounterLengthComparator,
    EncounterStatus,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

encounter_id_seq = Sequence(
    "encounter_pub_seq", start=20000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class EncounterModel(FhirCodingMixin, TenantAuditMixin, Base):
    """FHIR R4 Encounter — https://www.hl7.org/fhir/R4/encounter.html

    An interaction between a patient and healthcare provider(s) for the
    purpose of providing healthcare service(s) or assessing the health
    status of a patient.

    Modeled to the same conventions as Organization/.../AppointmentResponse:
    BigInteger internal PK + public sequence ID, TenantAuditMixin
    (tenant_id, not a hand-declared org_id), flattened references with an
    Identifier logical-reference fallback (`subject`, `serviceProvider`,
    `partOf`), and every CodeableConcept's coding[] as a real 0..* child/
    grandchild table rather than a single flattened coding.

    `class` (1..1 **Coding**, not CodeableConcept — the first bare-Coding
    top-level field in this codebase) is flattened directly onto this row
    via the shared FhirCodingMixin with `_coding_prefix = "class_"` —
    there's no coding[] to promote, since a bare Coding has no nested
    list the way a CodeableConcept's own `coding[]` always does.

    `serviceType`/`priority` are each a 0..1 CodeableConcept — `text`
    stays flattened here, `coding[]` is promoted to a dedicated child
    table each (see service_type.py... no wait, see core.py's own
    relationships below and service_type_coding/priority_coding tables in
    this package), same reasoning as every other CodeableConcept
    promotion in this codebase.

    `length` (0..1 Duration) is flattened directly onto this row —
    `length_value`/`length_comparator`/`length_unit`/`length_system`/
    `length_code` — since a Duration has no nested 0..* structure of its
    own to promote (same treatment as Period, just with more fields).

    `partOf` (0..1 Reference(Encounter)) is self-referential, same
    pattern as Location.partOf — Encounter must register itself in
    RESOURCE_REGISTRY for this existence check to work at all.

    This resource IS part of the JWT auth rollout (see CLAUDE.md's
    Multi-Tenancy & Ownership section) — org_id comes from the verified
    JWT's activeOrganizationId claim, never a client-suppliable field.
    There is deliberately no user_id: like every other auth-rollout
    resource, an Encounter is a shared tenant-level entity, not scoped to
    one end user's own account.
    """

    __tablename__ = "encounter"

    _coding_prefix = "class_"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    encounter_id = Column(
        BigInteger,
        encounter_id_seq,
        server_default=encounter_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── status (1..1 code) — required ─────────────────────────────────────────

    status = Column(Enum(EncounterStatus, name="encounter_status"), nullable=False)

    # ── class (1..1 Coding) — required — flattened via FhirCodingMixin ───────
    # (system/version/code/display/user_selected, all class_-prefixed, all
    # individually nullable — the FHIR *field* is 1..1, but Coding's own
    # sub-elements are each independently 0..1; the structural "this field
    # must be present" rule is enforced by the validator, not a DB NOT NULL
    # on every sub-column)

    # ── serviceType (0..1 CodeableConcept) — text flattened here, ────────────
    # coding[] promoted to a dedicated child table (EncounterServiceTypeCoding)

    service_type_text = Column(String, nullable=True)

    # ── priority (0..1 CodeableConcept) — text flattened here, ───────────────
    # coding[] promoted to a dedicated child table (EncounterPriorityCoding)

    priority_text = Column(String, nullable=True)

    # ── subject (0..1 Reference(Patient|Group)) ───────────────────────────────
    # Shared SubjectReferenceType (Patient|Group) — neither is a modeled
    # resource in this system today, so this reference's existence check
    # is never attempted; kept for parity with every other reference field.

    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type", create_type=False),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
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

    # ── period (0..1 Period) ───────────────────────────────────────────────────

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # ── length (0..1 Duration) — flattened, no nested structure to promote ───

    length_value = Column(Numeric(18, 6), nullable=True)
    length_comparator = Column(
        Enum(EncounterLengthComparator, name="encounter_length_comparator"),
        nullable=True,
    )
    length_unit = Column(String, nullable=True)
    length_system = Column(String, nullable=True)
    length_code = Column(String, nullable=True)

    # ── serviceProvider (0..1 Reference(Organization)) ────────────────────────

    service_provider_reference = Column(String, nullable=True)
    service_provider_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    service_provider_id = Column(BigInteger, nullable=True, index=True)
    service_provider_display = Column(String, nullable=True)

    service_provider_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    service_provider_identifier_type_system = Column(String, nullable=True)
    service_provider_identifier_type_version = Column(String, nullable=True)
    service_provider_identifier_type_code = Column(String, nullable=True)
    service_provider_identifier_type_display = Column(String, nullable=True)
    service_provider_identifier_type_text = Column(String, nullable=True)
    service_provider_identifier_type_user_selected = Column(Boolean, nullable=True)
    service_provider_identifier_system = Column(String, nullable=True)
    service_provider_identifier_value = Column(String, nullable=True)
    service_provider_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    service_provider_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    # ── partOf (0..1 Reference(Encounter)) — self-referential ─────────────────

    part_of_reference = Column(String, nullable=True)
    part_of_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False),
        nullable=True,
    )
    part_of_id = Column(BigInteger, nullable=True, index=True)
    part_of_display = Column(String, nullable=True)

    part_of_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    part_of_identifier_type_system = Column(String, nullable=True)
    part_of_identifier_type_version = Column(String, nullable=True)
    part_of_identifier_type_code = Column(String, nullable=True)
    part_of_identifier_type_display = Column(String, nullable=True)
    part_of_identifier_type_text = Column(String, nullable=True)
    part_of_identifier_type_user_selected = Column(Boolean, nullable=True)
    part_of_identifier_system = Column(String, nullable=True)
    part_of_identifier_value = Column(String, nullable=True)
    part_of_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    part_of_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not Encounter-specific). Raw
    # [{url, valueType, value}, ...]; validated against registered
    # extension definitions by the (not-yet-built) profile pipeline, not by
    # the database. Same shape as OrganizationModel.extension.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above — no hand-declared org_id here, same
    # as OrganizationModel/.../AppointmentResponseModel.

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "EncounterIdentifier", back_populates="encounter", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "EncounterStatusHistory", back_populates="encounter", cascade="all, delete-orphan"
    )
    class_history = relationship(
        "EncounterClassHistory", back_populates="encounter", cascade="all, delete-orphan"
    )
    types = relationship(
        "EncounterType", back_populates="encounter", cascade="all, delete-orphan"
    )
    service_type_codings = relationship(
        "EncounterServiceTypeCoding", back_populates="encounter", cascade="all, delete-orphan"
    )
    priority_codings = relationship(
        "EncounterPriorityCoding", back_populates="encounter", cascade="all, delete-orphan"
    )
    episode_of_cares = relationship(
        "EncounterEpisodeOfCare", back_populates="encounter", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "EncounterBasedOn", back_populates="encounter", cascade="all, delete-orphan"
    )
    appointments = relationship(
        "EncounterAppointment", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "EncounterReasonCode", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "EncounterReasonReference", back_populates="encounter", cascade="all, delete-orphan"
    )
    accounts = relationship(
        "EncounterAccount", back_populates="encounter", cascade="all, delete-orphan"
    )
    participants = relationship(
        "EncounterParticipant", back_populates="encounter", cascade="all, delete-orphan"
    )
    diagnoses = relationship(
        "EncounterDiagnosis", back_populates="encounter", cascade="all, delete-orphan"
    )
    hospitalization = relationship(
        "EncounterHospitalization",
        back_populates="encounter",
        cascade="all, delete-orphan",
        uselist=False,
    )
    locations = relationship(
        "EncounterLocationRow", back_populates="encounter", cascade="all, delete-orphan"
    )

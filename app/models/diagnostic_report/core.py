from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.diagnostic_report.enums import (
    DiagnosticReportStatus,
    DiagnosticReportSubjectReferenceType,
)
from app.models.enums import EncounterReferenceType, IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin

diagnostic_report_id_seq = Sequence(
    "diagnostic_report_pub_seq", start=110000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class DiagnosticReportModel(TenantAuditMixin, Base):
    """FHIR R4 DiagnosticReport — https://www.hl7.org/fhir/R4/diagnosticreport.html

    The findings and interpretation of diagnostic tests performed on
    patients, groups of patients, devices, and locations, and/or
    specimens derived from these.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout,
    same as Observation/QuestionnaireResponse/ServiceRequest/
    MedicationRequest: `tenant_id`/`created_by`/`updated_by` are plain,
    gateway-forwarded request fields. Keeps a plain `user_id` column.

    `code` (1..1 CodeableConcept) is flattened with `_text` here, its own
    `coding[]` promoted to a dedicated direct-child table — same
    promotion pattern as every other 0..1/1..1 CodeableConcept in this
    codebase. `effective[x]` here is only `dateTime | Period` (no
    Timing/instant variants, unlike Observation's own `effective[x]`) —
    per spec, DiagnosticReport doesn't carry those two choices at all.
    """

    __tablename__ = "diagnostic_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    diagnostic_report_id = Column(
        BigInteger,
        diagnostic_report_id_seq,
        server_default=diagnostic_report_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── status (1..1, required, modifier) ──────────────────────────────────
    status = Column(Enum(DiagnosticReportStatus, name="diagnostic_report_status"), nullable=False)

    # ── code (1..1 CodeableConcept) ─────────────────────────────────────────
    code_text = Column(String, nullable=True)

    # ── subject (0..1 Reference(Patient|Group|Device|Location)) ───────────
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(DiagnosticReportSubjectReferenceType, name="diagnostic_report_subject_reference_type"),
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

    # ── effective[x] (0..1 choice: dateTime | Period) ──────────────────────
    effective_date_time = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── issued (0..1 instant) ────────────────────────────────────────────────
    issued = Column(DateTime(timezone=True), nullable=True)

    # ── conclusion (0..1 string) ────────────────────────────────────────────
    conclusion = Column(String, nullable=True)

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # ── Relationships ─────────────────────────────────────────────────────

    code_codings = relationship(
        "DiagnosticReportCodeCoding", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    identifiers = relationship(
        "DiagnosticReportIdentifier", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "DiagnosticReportBasedOn", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    categories = relationship(
        "DiagnosticReportCategory", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    performers = relationship(
        "DiagnosticReportPerformer", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    results_interpreters = relationship(
        "DiagnosticReportResultsInterpreter", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    specimens = relationship(
        "DiagnosticReportSpecimen", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    results = relationship(
        "DiagnosticReportResult", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    imaging_studies = relationship(
        "DiagnosticReportImagingStudy", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    media = relationship(
        "DiagnosticReportMedia", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    conclusion_codes = relationship(
        "DiagnosticReportConclusionCode", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )
    presented_forms = relationship(
        "DiagnosticReportPresentedForm", back_populates="diagnostic_report", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Direct-child coding table for the main row's own 1..1 CodeableConcept
# ---------------------------------------------------------------------------


class DiagnosticReportCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DiagnosticReport.code.coding (0..*)."""

    __tablename__ = "diagnostic_report_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="code_codings")

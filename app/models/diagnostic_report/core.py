from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import DiagnosticReportStatus

diagnostic_report_id_seq = Sequence(
    "diagnostic_report_pub_seq", start=110000, increment=1, metadata=Base.metadata
)

# R4 targets of DiagnosticReport.subject.
SUBJECT_TYPES = ("Patient", "Group", "Device", "Location")


class DiagnosticReportModel(TenantAuditMixin, Base):
    """FHIR R4 DiagnosticReport — Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.diagnostic_report). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 DiagnosticReport search parameter filters on it
    (https://www.hl7.org/fhir/R4/diagnosticreport.html#search), and is derived
    from `content` on every write by app.repository.diagnostic_report._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so
                          `entered-in-error` is the real FHIR code)
      date             -> effective_date_start/_end (effective[x] as a dateTime or
                          a Period, columns; the half-open range covered,
                          NULL = open)
      issued           -> issued (0..1 instant, column)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (0..1 Reference(Patient | Group | Device | Location),
                          columns; `patient` is the same columns narrowed to
                          Patient)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
                          (0..1 Reference(Encounter), columns)
      identifier       -> DiagnosticReportIdentifier (0..*)
      category, code, conclusion
                       -> DiagnosticReportToken (0..*, one shared table;
                          `conclusion` reads conclusionCode)
      based-on, media, result, specimen
                       -> DiagnosticReportReference (0..*, one shared table;
                          `media` reads media.link)
      performer, results-interpreter
                       -> DiagnosticReportPerformer (one row per performer /
                          resultsInterpreter Reference, told apart by `param`)
      _id              -> diagnostic_report_id;  _lastUpdated -> updated_at/created_at

    `imagingStudy`, `media.comment`, `conclusion` (the string), `presentedForm` and
    `extension` have no search parameter and live only in `content`.

    `subject`, `performer`, `results-interpreter` and `based-on` can point at
    several resource types, so `*_type` records which one a relative `Type/<id>`
    names (a plain string, not a Postgres enum): a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`; `patient`, `encounter`, `media`,
    `result` and `specimen` have one target so a bare id works).

    All index columns are nullable: R4 makes `status` and `code` mandatory, but
    that is the validator's rule (enforced by the `java_validator` backend), not
    the database's. No `user_id`: a DiagnosticReport is a shared tenant-level
    entity. No DB-level CHECK constraints."""

    __tablename__ = "diagnostic_report"
    __table_args__ = (
        Index(
            "ix_diagnostic_report_effective_date",
            "effective_date_start",
            "effective_date_end",
        ),
        Index("ix_diagnostic_report_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    diagnostic_report_id = Column(
        BigInteger,
        diagnostic_report_id_seq,
        server_default=diagnostic_report_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            DiagnosticReportStatus,
            name="diagnostic_report_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # effective[x] as a dateTime or a Period: the half-open [start, end) range of
    # instants it covers (NULL = open / absent), matched with period_match.
    effective_date_start = Column(DateTime(timezone=True), nullable=True)
    effective_date_end = Column(DateTime(timezone=True), nullable=True)

    # issued is an instant: matched with date_match.
    issued = Column(DateTime(timezone=True), nullable=True, index=True)

    # subject (0..1 Reference(Patient | Group | Device | Location))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "DiagnosticReportIdentifier",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "DiagnosticReportToken",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "DiagnosticReportReference",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "DiagnosticReportPerformer",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )

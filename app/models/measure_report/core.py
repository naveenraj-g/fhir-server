from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MeasureReportStatus

measure_report_id_seq = Sequence(
    "measure_report_pub_seq", start=570000, increment=1, metadata=Base.metadata
)


class MeasureReportModel(TenantAuditMixin, Base):
    """FHIR R4 MeasureReport - stored whole in `content`, like QuestionnaireResponse, CarePlan and
    the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.measure_report). Nothing else in this table or
    its child tables is a second copy of the resource: every other column exists only because a
    FHIR R4 MeasureReport search parameter filters on it
    (https://www.hl7.org/fhir/R4/measurereport.html#search), and is derived from `content` on
    every write by app.repository.measure_report._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, required binding)
      date              -> date_start/_end (0..1 dateTime, the half-open range it covers at its
                           written precision; columns)
      period            -> period_start/_end (1..1 Period, half-open range, NULL = open; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (0..1
                           Reference(Practitioner | Group | Device | Patient | PractitionerRole |
                           RelatedPerson | Location), columns; `patient` is `subject` narrowed to
                           Patients)
      reporter          -> reporter_reference/_type/_id + reporter_identifier_* (0..1
                           Reference(Practitioner | PractitionerRole | Location | Organization),
                           columns)
      identifier        -> MeasureReportIdentifier (0..*)
      measure,
      evaluated-resource -> MeasureReportReference (one shared table, told apart by `param`;
                           `measure` is a canonical URL, `evaluated-resource` Reference(Any))
      _id               -> measure_report_id;  _lastUpdated -> updated_at/created_at

    Everything else - `type` (a required binding no search parameter reads, so not an enum
    column), `improvementNotation`, the whole `group` tree (population counts, `subjectResults`,
    `measureScore`, stratifier / stratum / component / population results) and `extension` -
    lives only in `content`.

    `subject` points at several resource types, so a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`); `patient` is `subject` narrowed to Patients (a bare id
    works); `measure` has one target.

    All index columns are nullable. No `user_id`: a MeasureReport is a shared tenant-level
    entity. No DB-level CHECK constraints (R4 rules - e.g. mrp-1 - are the validator's)."""

    __tablename__ = "measure_report"
    __table_args__ = (
        Index("ix_measure_report_date", "date_start", "date_end"),
        Index("ix_measure_report_period", "period_start", "period_end"),
        Index("ix_measure_report_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    measure_report_id = Column(
        BigInteger,
        measure_report_id_seq,
        server_default=measure_report_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MeasureReportStatus,
            name="measure_report_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # date (0..1 dateTime) and period (1..1 Period): half-open [start, end) ranges.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # reporter (0..1 Reference)
    reporter_reference = Column(String, nullable=True)
    reporter_type = Column(String, nullable=True)
    reporter_id = Column(BigInteger, nullable=True, index=True)
    reporter_identifier_system = Column(String, nullable=True)
    reporter_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MeasureReportIdentifier",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MeasureReportReference",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )

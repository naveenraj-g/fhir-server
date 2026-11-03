from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.measure_report.enums import (
    MeasureReportReporterReferenceType,
    MeasureReportStatus,
    MeasureReportSubjectReferenceType,
    MeasureReportType,
)
from app.models.shared import TenantAuditMixin

measure_report_pub_seq = Sequence(
    "measure_report_pub_seq", start=570000, increment=1, metadata=Base.metadata
)


class MeasureReportModel(TenantAuditMixin, Base):
    """MeasureReport resource model (FHIR R4)."""

    __tablename__ = "measure_report"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    measure_report_id = Column(
        BigInteger,
        measure_report_pub_seq,
        server_default=measure_report_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    status = Column(
        Enum(MeasureReportStatus, name="measure_report_status"),
        nullable=False,
    )
    type = Column(
        Enum(MeasureReportType, name="measure_report_type"),
        nullable=False,
    )
    measure = Column(String, nullable=False)

    # subject (0..1 Reference(Patient | Practitioner | PractitionerRole | Location | Device | RelatedPerson | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            MeasureReportSubjectReferenceType,
            name="measure_report_subject_reference_type",
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

    date = Column(DateTime(timezone=True), nullable=True)

    # reporter (0..1 Reference(Practitioner | PractitionerRole | Organization | Location))
    reporter_reference = Column(String, nullable=True)
    reporter_type = Column(
        Enum(
            MeasureReportReporterReferenceType,
            name="measure_report_reporter_reference_type",
        ),
        nullable=True,
    )
    reporter_id = Column(BigInteger, nullable=True, index=True)
    reporter_display = Column(String, nullable=True)

    # reporter.identifier fallback (11 columns)
    reporter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reporter_identifier_type_system = Column(String, nullable=True)
    reporter_identifier_type_version = Column(String, nullable=True)
    reporter_identifier_type_code = Column(String, nullable=True)
    reporter_identifier_type_display = Column(String, nullable=True)
    reporter_identifier_type_user_selected = Column(Boolean, nullable=True)
    reporter_identifier_type_text = Column(String, nullable=True)
    reporter_identifier_system = Column(String, nullable=True)
    reporter_identifier_value = Column(String, nullable=True)
    reporter_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reporter_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # period (1..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # improvementNotation (0..1 CodeableConcept)
    improvement_notation_text = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "MeasureReportIdentifier",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )
    improvement_notation_coding = relationship(
        "MeasureReportImprovementNotationCoding",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )
    evaluated_resources = relationship(
        "MeasureReportEvaluatedResource",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )
    groups = relationship(
        "MeasureReportGroup",
        back_populates="measure_report",
        cascade="all, delete-orphan",
    )

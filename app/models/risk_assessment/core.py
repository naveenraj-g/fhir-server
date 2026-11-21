from sqlalchemy import BigInteger, Column, DateTime, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

risk_assessment_id_seq = Sequence("risk_assessment_pub_seq", start=520000, increment=1, metadata=Base.metadata)

# The R4 targets of RiskAssessment.subject and .performer.
SUBJECT_TYPES = ("Patient", "Group")
PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Device")


class RiskAssessmentModel(TenantAuditMixin, Base):
    """FHIR R4 RiskAssessment — Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, DiagnosticReport, Immunization and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns — see app.fhir.mappers.risk_assessment). Nothing else in
    this table or its child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 RiskAssessment search parameter filters on it
    (https://www.hl7.org/fhir/R4/riskassessment.html#search), and is derived from `content` on
    every write by app.repository.risk_assessment._indexer.

    Search parameter -> storage:
      date             -> date_start/_end (`occurrenceDateTime`, as the half-open range it
                          covers at its written precision; columns). The R4 expression is
                          `(RiskAssessment.occurrence as dateTime)`, so an `occurrencePeriod` is
                          not indexed and counts as missing.
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (0..1 Reference(Patient | Group), columns; `patient` is `subject`
                          narrowed to Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (columns)
      condition        -> condition_reference/_type/_id + condition_identifier_* (columns)
      performer        -> performer_reference/_type/_id + performer_identifier_*
                          (0..1 Reference(Practitioner | PractitionerRole | Device), columns)
      identifier       -> RiskAssessmentIdentifier (0..*)
      method, risk     -> RiskAssessmentToken (one shared table, one row per coding of each
                          concept; `risk` reads prediction.qualitativeRisk of every prediction)
      probability      -> RiskAssessmentPrediction (one row per prediction with a probability:
                          its lower and upper bound — a decimal is a point)
      _id              -> risk_assessment_id;  _lastUpdated -> updated_at/created_at

    `status` has no R4 search parameter on this resource, so it lives only in `content`, as do
    `basedOn`, `parent`, `code`, `reasonCode`, `reasonReference`, `basis`, `mitigation`, `note`,
    `occurrencePeriod`, every prediction element except the probability and the qualitative
    risk (`outcome`, `relativeRisk`, `when[x]`, `rationale`) and `extension`.

    `subject` and `performer` can point at several resource types, so `reference_type`
    records which one a relative `Type/<id>` names (a plain string, not a Postgres enum): a
    search by bare id is ambiguous for them (`subject=Type/id` or `subject:Type=id`; `patient`,
    `encounter` and `condition` have one target so a bare id works).

    All index columns are nullable: R4 makes `status` and `subject` mandatory, but that is the
    validator's rule (enforced by the `java_validator` backend), not the database's. No
    `user_id`: a RiskAssessment is a shared tenant-level entity. No DB-level CHECK constraints
    (rules ras-1 / ras-2 are the validator's job)."""

    __tablename__ = "risk_assessment"
    __table_args__ = (Index("ix_risk_assessment_date", "date_start", "date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    risk_assessment_id = Column(
        BigInteger,
        risk_assessment_id_seq,
        server_default=risk_assessment_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    # date: the half-open [start, end) range of instants the occurrenceDateTime covers.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)

    # condition (0..1 Reference(Condition))
    condition_reference = Column(String, nullable=True)
    condition_type = Column(String, nullable=True)
    condition_id = Column(BigInteger, nullable=True, index=True)
    condition_identifier_system = Column(String, nullable=True)
    condition_identifier_value = Column(String, nullable=True)

    # performer (0..1 Reference(Practitioner | PractitionerRole | Device))
    performer_reference = Column(String, nullable=True)
    performer_type = Column(String, nullable=True)
    performer_id = Column(BigInteger, nullable=True, index=True)
    performer_identifier_system = Column(String, nullable=True)
    performer_identifier_value = Column(String, nullable=True)

    identifiers = relationship("RiskAssessmentIdentifier", back_populates="risk_assessment", cascade="all, delete-orphan")
    tokens = relationship("RiskAssessmentToken", back_populates="risk_assessment", cascade="all, delete-orphan")
    predictions = relationship("RiskAssessmentPrediction", back_populates="risk_assessment", cascade="all, delete-orphan")

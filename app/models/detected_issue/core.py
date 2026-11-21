from sqlalchemy import BigInteger, Column, DateTime, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

detected_issue_id_seq = Sequence(
    "detected_issue_pub_seq", start=540000, increment=1, metadata=Base.metadata
)

# The R4 targets of DetectedIssue.author.
AUTHOR_TYPES = ("Practitioner", "PractitionerRole", "Device")


class DetectedIssueModel(TenantAuditMixin, Base):
    """FHIR R4 DetectedIssue — Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, DiagnosticReport, RiskAssessment, ClinicalImpression and the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns — see app.fhir.mappers.detected_issue). Nothing else in
    this table or its child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 DetectedIssue search parameter filters on it
    (https://www.hl7.org/fhir/R4/detectedissue.html#search), and is derived from `content` on
    every write by app.repository.detected_issue._indexer.

    Search parameter -> storage:
      identified       -> identified_start/_end (`identified[x]`, a dateTime or a Period, as the
                          half-open range of instants it covers; columns)
      patient          -> patient_reference/_type/_id + patient_identifier_*
                          (0..1 Reference(Patient), columns)
      author           -> author_reference/_type/_id + author_identifier_*
                          (0..1 Reference(Practitioner | PractitionerRole | Device), columns)
      identifier       -> DetectedIssueIdentifier (0..*)
      code             -> DetectedIssueToken (one row per coding of the 0..1 CodeableConcept)
      implicated       -> DetectedIssueReference (one row per Reference(Any))
      _id              -> detected_issue_id;  _lastUpdated -> updated_at/created_at

    R4 defines **no `status` or `severity` search parameter** for this resource, so both live
    only in `content`, as do `detail`, `reference`, `evidence`, `mitigation` and `extension`.

    `author` and `implicated` can point at several resource types, so `reference_type` records
    which one a relative `Type/<id>` names (a plain string, not a Postgres enum): a search by
    bare id is ambiguous for them (`author=Type/id` or `author:Type=id`; `patient` has one
    target so a bare id works).

    All index columns are nullable: R4 makes `status` mandatory, but that is the validator's
    rule (enforced by the `java_validator` backend), not the database's. No `user_id`: a
    DetectedIssue is a shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "detected_issue"
    __table_args__ = (
        Index("ix_detected_issue_identified", "identified_start", "identified_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    detected_issue_id = Column(
        BigInteger,
        detected_issue_id_seq,
        server_default=detected_issue_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    # identified: the half-open [start, end) range of instants identified[x] covers.
    identified_start = Column(DateTime(timezone=True), nullable=True)
    identified_end = Column(DateTime(timezone=True), nullable=True)

    # patient (0..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    # author (0..1 Reference(Practitioner | PractitionerRole | Device))
    author_reference = Column(String, nullable=True)
    author_type = Column(String, nullable=True)
    author_id = Column(BigInteger, nullable=True, index=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "DetectedIssueIdentifier",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "DetectedIssueToken",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "DetectedIssueReference",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
    )

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ClinicalImpressionStatus

clinical_impression_id_seq = Sequence("clinical_impression_pub_seq", start=530000, increment=1, metadata=Base.metadata)

# The R4 targets of ClinicalImpression.subject and .assessor.
SUBJECT_TYPES = ("Patient", "Group")
ASSESSOR_TYPES = ("Practitioner", "PractitionerRole")


class ClinicalImpressionModel(TenantAuditMixin, Base):
    """FHIR R4 ClinicalImpression — Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, DiagnosticReport, Immunization, RiskAssessment and the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns — see app.fhir.mappers.clinical_impression). Nothing else in
    this table or its child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 ClinicalImpression search parameter filters on it
    (https://www.hl7.org/fhir/R4/clinicalimpression.html#search), and is derived from `content`
    on every write by app.repository.clinical_impression._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so `in-progress` /
                          `entered-in-error` are the real FHIR codes)
      date             -> date_start/_end (the 0..1 `date` dateTime, as the half-open range it
                          covers at its written precision; columns). `effective[x]` is not
                          searchable and lives only in `content`.
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (1..1 Reference(Patient | Group), columns; `patient` is `subject`
                          narrowed to Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (columns)
      assessor         -> assessor_reference/_type/_id + assessor_identifier_*
                          (0..1 Reference(Practitioner | PractitionerRole), columns)
      previous         -> previous_reference/_type/_id + previous_identifier_*
                          (0..1 Reference(ClinicalImpression), columns)
      identifier       -> ClinicalImpressionIdentifier (0..*)
      finding-code     -> ClinicalImpressionToken (one row per coding of every finding's
                          itemCodeableConcept)
      problem, investigation, finding-ref, supporting-info
                       -> ClinicalImpressionReference (one shared table, one row per Reference,
                          told apart by `param`; `investigation` reads investigation.item and
                          `finding-ref` reads finding.itemReference)
      _id              -> clinical_impression_id;  _lastUpdated -> updated_at/created_at

    `statusReason`, `code`, `description`, `effective[x]`, `protocol`, `summary`, every finding
    element except `itemCodeableConcept` / `itemReference` (`basis`), every investigation
    element except `item` (`code`), `prognosisCodeableConcept`, `prognosisReference`, `note` and
    `extension` have no search parameter and live only in `content`.

    `subject`, `assessor`, `problem`, `investigation`, `finding-ref` and `supporting-info` can
    point at several resource types, so `reference_type` records which one a relative
    `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is ambiguous for
    them (`subject=Type/id` or `subject:Type=id`; `patient`, `encounter` and `previous` have one
    target so a bare id works).

    All index columns are nullable: R4 makes `status` and `subject` mandatory, but that is the
    validator's rule (enforced by the `java_validator` backend), not the database's. No
    `user_id`: a ClinicalImpression is a shared tenant-level entity. No DB-level CHECK
    constraints."""

    __tablename__ = "clinical_impression"
    __table_args__ = (Index("ix_clinical_impression_date", "date_start", "date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    clinical_impression_id = Column(
        BigInteger,
        clinical_impression_id_seq,
        server_default=clinical_impression_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            ClinicalImpressionStatus,
            name="clinical_impression_status",
            # Store `in-progress`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # date: the half-open [start, end) range of instants the `date` dateTime covers.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group))
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

    # assessor (0..1 Reference(Practitioner | PractitionerRole))
    assessor_reference = Column(String, nullable=True)
    assessor_type = Column(String, nullable=True)
    assessor_id = Column(BigInteger, nullable=True, index=True)
    assessor_identifier_system = Column(String, nullable=True)
    assessor_identifier_value = Column(String, nullable=True)

    # previous (0..1 Reference(ClinicalImpression))
    previous_reference = Column(String, nullable=True)
    previous_type = Column(String, nullable=True)
    previous_id = Column(BigInteger, nullable=True, index=True)
    previous_identifier_system = Column(String, nullable=True)
    previous_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "ClinicalImpressionIdentifier", back_populates="clinical_impression", cascade="all, delete-orphan"
    )
    tokens = relationship("ClinicalImpressionToken", back_populates="clinical_impression", cascade="all, delete-orphan")
    references = relationship(
        "ClinicalImpressionReference", back_populates="clinical_impression", cascade="all, delete-orphan"
    )

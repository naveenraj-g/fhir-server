from sqlalchemy import BigInteger, Column, DateTime, Index, Numeric, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

condition_id_seq = Sequence("condition_pub_seq", start=120000, increment=1, metadata=Base.metadata)

# R4 targets of Condition.subject, and of Condition.asserter (and recorder).
SUBJECT_TYPES = ("Patient", "Group")
ACTOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")


class ConditionModel(TenantAuditMixin, Base):
    """FHIR R4 Condition — Medplum-style storage, same as Patient, Encounter,
    AllergyIntolerance and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.condition). Nothing else in this table or its child tables
    is a second copy of the resource: every other column exists only because a
    FHIR R4 Condition search parameter filters on it
    (https://www.hl7.org/fhir/R4/condition.html#search), and is derived from
    `content` on every write by app.repository.condition._indexer.

    Search parameter -> storage:
      recorded-date    -> recorded_date_start/_end (0..1 dateTime, columns; the
                          half-open range the dateTime covers, so a partial
                          dateTime works — see period_bounds)
      onset-date,
      abatement-date   -> onset_date_start/_end, abatement_date_start/_end
                          (onset[x] / abatement[x] as dateTime or Period, columns;
                          the half-open range covered, NULL = open)
      onset-age,
      abatement-age    -> onset_age_low/_high/_system/_code/_unit and the
                          abatement_age_* twin (onset[x] / abatement[x] as an Age —
                          low = high — or a Range, columns; matched with
                          quantity_range_match)
      onset-info,
      abatement-string -> onset_string/_norm, abatement_string/_norm (0..1
                          string, columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (1..1 Reference(Patient | Group), columns; `patient`
                          is the same columns narrowed to Patient)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
                          (0..1 Reference(Encounter), columns)
      asserter         -> asserter_reference/_type/_id + asserter_identifier_*
                          (0..1 Reference to one of ACTOR_TYPES, columns)
      identifier       -> ConditionIdentifier (0..*)
      body-site, category, clinical-status, code, evidence, severity, stage,
      verification-status
                       -> ConditionToken (0..*, one shared table; `evidence`
                          reads evidence.code and `stage` reads stage.summary)
      evidence-detail  -> ConditionEvidenceDetail (one row per
                          evidence.detail Reference)
      _id              -> condition_id;  _lastUpdated -> updated_at/created_at

    `recorder`, `note`, `stage.assessment`/`.type`, `evidence` structure beyond
    the two searched elements, `extension` and the other onset/abatement
    choices live only in `content`.

    `subject` and `asserter` can point at several resource types, so `*_type`
    records which one a relative `Type/<id>` names (a plain string, not a
    Postgres enum): a search by bare id is ambiguous (`subject=Type/id` or
    `subject:Type=id`; `patient` has one target so a bare id works).

    All index columns are nullable: R4 makes `subject` mandatory (and rules
    con-3/con-4/con-5 tie clinicalStatus to verificationStatus, category and
    abatement), but those are the validator's rules (enforced by the
    `java_validator` backend), not the database's. No `user_id`: a Condition is
    a shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "condition"
    __table_args__ = (
        Index("ix_condition_recorded_date", "recorded_date_start", "recorded_date_end"),
        Index("ix_condition_onset_date", "onset_date_start", "onset_date_end"),
        Index("ix_condition_abatement_date", "abatement_date_start", "abatement_date_end"),
        Index("ix_condition_subject_type_id", "subject_type", "subject_id"),
        Index("ix_condition_asserter_type_id", "asserter_type", "asserter_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    condition_id = Column(
        BigInteger,
        condition_id_seq,
        server_default=condition_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    recorded_date_start = Column(DateTime(timezone=True), nullable=True)
    recorded_date_end = Column(DateTime(timezone=True), nullable=True)

    # onset[x] — dateTime / Period as a range, Age / Range as quantity bounds, string.
    onset_date_start = Column(DateTime(timezone=True), nullable=True)
    onset_date_end = Column(DateTime(timezone=True), nullable=True)
    onset_age_low = Column(Numeric, nullable=True)
    onset_age_high = Column(Numeric, nullable=True)
    onset_age_system = Column(String, nullable=True)
    onset_age_code = Column(String, nullable=True)
    onset_age_unit = Column(String, nullable=True)
    onset_string = Column(String, nullable=True)
    onset_string_norm = Column(String, nullable=True)

    # abatement[x] — same shapes as onset[x].
    abatement_date_start = Column(DateTime(timezone=True), nullable=True)
    abatement_date_end = Column(DateTime(timezone=True), nullable=True)
    abatement_age_low = Column(Numeric, nullable=True)
    abatement_age_high = Column(Numeric, nullable=True)
    abatement_age_system = Column(String, nullable=True)
    abatement_age_code = Column(String, nullable=True)
    abatement_age_unit = Column(String, nullable=True)
    abatement_string = Column(String, nullable=True)
    abatement_string_norm = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group))
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

    # asserter (0..1 Reference to one of ACTOR_TYPES)
    asserter_reference = Column(String, nullable=True)
    asserter_type = Column(String, nullable=True)
    asserter_id = Column(BigInteger, nullable=True)
    asserter_identifier_system = Column(String, nullable=True)
    asserter_identifier_value = Column(String, nullable=True)

    identifiers = relationship("ConditionIdentifier", back_populates="condition", cascade="all, delete-orphan")
    tokens = relationship("ConditionToken", back_populates="condition", cascade="all, delete-orphan")
    evidence_details = relationship(
        "ConditionEvidenceDetail", back_populates="condition", cascade="all, delete-orphan"
    )

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import AllergyIntoleranceCriticality, AllergyIntoleranceType

allergy_intolerance_id_seq = Sequence(
    "allergy_intolerance_pub_seq", start=260000, increment=1, metadata=Base.metadata
)

# The four R4 targets of both AllergyIntolerance.recorder and .asserter.
ACTOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")


class AllergyIntoleranceModel(TenantAuditMixin, Base):
    """FHIR R4 AllergyIntolerance — Medplum-style storage, same as Patient,
    Appointment, Encounter and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.allergy_intolerance). Nothing else in this table or its
    child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 AllergyIntolerance search parameter filters on it
    (https://www.hl7.org/fhir/R4/allergyintolerance.html#search), and is derived
    from `content` on every write by app.repository.allergy_intolerance._indexer.

    Search parameter -> storage:
      type             -> type (0..1 code, Enum column, stored by value)
      criticality      -> criticality (0..1 code, Enum column, stored by value so
                          `unable-to-assess` is the real FHIR code)
      date             -> recorded_date_start/_end (0..1 dateTime, columns; the
                          half-open range the dateTime covers, so a partial
                          dateTime works — see period_bounds)
      last-date        -> last_occurrence_start/_end (0..1 dateTime, same shape)
      patient          -> patient_reference/_type/_id +
                          patient_identifier_system/_value (1..1
                          Reference(Patient), columns)
      recorder         -> recorder_reference/_type/_id + recorder_identifier_*
                          (0..1 Reference to one of ACTOR_TYPES, columns)
      asserter         -> asserter_reference/_type/_id + asserter_identifier_*
                          (0..1 Reference to one of ACTOR_TYPES, columns)
      identifier       -> AllergyIntoleranceIdentifier (0..*)
      category, clinical-status, verification-status, code, manifestation,
      route, severity  -> AllergyIntoleranceToken (0..*, one shared table; `code`
                          also covers reaction.substance)
      onset            -> AllergyIntoleranceReaction (one row per reaction.onset)
      _id              -> allergy_intolerance_id;  _lastUpdated -> updated_at/created_at

    `encounter`, `onset[x]`, `note` and every reaction element no search
    parameter reads live only in `content`.

    `recorder` and `asserter` can each point at four resource types, so
    `*_type` records which one a relative `Type/<id>` names (a plain string, not
    a Postgres enum): a search by bare id is ambiguous (`asserter=Type/id` or
    `asserter:Type=id`).

    All index columns are nullable: R4 makes `patient` mandatory (and rules
    ait-1/ait-2 tie clinicalStatus to verificationStatus), but those are the
    validator's rules (enforced by the `java_validator` backend), not the
    database's. No `user_id`: an AllergyIntolerance is a shared tenant-level
    entity. No DB-level CHECK constraints."""

    __tablename__ = "allergy_intolerance"
    __table_args__ = (
        Index(
            "ix_allergy_intolerance_recorded_date",
            "recorded_date_start",
            "recorded_date_end",
        ),
        Index(
            "ix_allergy_intolerance_recorder_type_id", "recorder_type", "recorder_id"
        ),
        Index(
            "ix_allergy_intolerance_asserter_type_id", "asserter_type", "asserter_id"
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    allergy_intolerance_id = Column(
        BigInteger,
        allergy_intolerance_id_seq,
        server_default=allergy_intolerance_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    type = Column(
        Enum(
            AllergyIntoleranceType,
            name="allergy_intolerance_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    criticality = Column(
        Enum(
            AllergyIntoleranceCriticality,
            name="allergy_intolerance_criticality",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # recordedDate / lastOccurrence are FHIR dateTimes that may be partial
    # (`2024`, `2024-03`): held as the half-open [start, end) range of instants
    # they cover (NULL = absent), matched with period_match.
    recorded_date_start = Column(DateTime(timezone=True), nullable=True)
    recorded_date_end = Column(DateTime(timezone=True), nullable=True)
    last_occurrence_start = Column(DateTime(timezone=True), nullable=True)
    last_occurrence_end = Column(DateTime(timezone=True), nullable=True)

    # patient (1..1 Reference(Patient)); `patient_type` is a plain string.
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    # recorder (0..1 Reference to one of ACTOR_TYPES)
    recorder_reference = Column(String, nullable=True)
    recorder_type = Column(String, nullable=True)
    recorder_id = Column(BigInteger, nullable=True)
    recorder_identifier_system = Column(String, nullable=True)
    recorder_identifier_value = Column(String, nullable=True)

    # asserter (0..1 Reference to one of ACTOR_TYPES)
    asserter_reference = Column(String, nullable=True)
    asserter_type = Column(String, nullable=True)
    asserter_id = Column(BigInteger, nullable=True)
    asserter_identifier_system = Column(String, nullable=True)
    asserter_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "AllergyIntoleranceIdentifier",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "AllergyIntoleranceToken",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
    )
    reactions = relationship(
        "AllergyIntoleranceReaction",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
    )

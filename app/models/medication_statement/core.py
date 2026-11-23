from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MedicationStatementStatus

medication_statement_id_seq = Sequence(
    "medication_statement_pub_seq", start=500000, increment=1, metadata=Base.metadata
)


class MedicationStatementModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationStatement - stored whole in `content`, like MedicationRequest,
    QuestionnaireResponse, CareTeam and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.medication_statement). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 MedicationStatement search parameter filters on it
    (https://www.hl7.org/fhir/R4/medicationstatement.html#search), and is derived from `content`
    on every write by app.repository.medication_statement._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value, required binding)
      effective         -> effective_start/_end (0..1 dateTime *or* Period, the half-open range it
                           covers at its written precision; NULL end = open; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (1..1
                           Reference(Patient | Group), columns; `patient` is `subject` narrowed to
                           Patients)
      context           -> context_reference/_type/_id + context_identifier_* (0..1
                           Reference(Encounter | EpisodeOfCare), columns)
      source            -> source_reference/_type/_id + source_identifier_* (0..1 informationSource,
                           Reference(Practitioner | Organization | Patient | PractitionerRole |
                           RelatedPerson), columns)
      medication        -> medication_reference/_type/_id + medication_identifier_* (the
                           medicationReference, Reference(Medication), columns)
      code              -> MedicationStatementToken (param `code`: medicationCodeableConcept)
      category          -> MedicationStatementToken (param `category`: the 0..1 category)
      identifier        -> MedicationStatementIdentifier (one row per identifier x type coding)
      part-of           -> MedicationStatementReference (one row per partOf Reference)
      _id               -> medication_statement_id;  _lastUpdated -> updated_at/created_at

    `basedOn`, `statusReason`, `dateAsserted`, `derivedFrom`, `reasonCode`, `reasonReference`,
    `note`, `dosage` (and `medication[x]` when it is a reference, apart from the index above) and
    `extension` have no search parameter, so they live only in `content`.

    `*_type` is a plain string, not a Postgres enum: `subject`, `source` and `part-of` have several
    targets, so a search by bare id is ambiguous (`subject=Type/id` or `subject:Type=id`);
    `patient`, `context` and `medication` take a type or a bare id.

    All index columns are nullable. No `user_id`: a MedicationStatement is a shared tenant-level
    entity. No DB-level CHECK constraints (R4 rules - e.g. mst-1 - are the validator's)."""

    __tablename__ = "medication_statement"
    __table_args__ = (
        Index("ix_medication_statement_effective", "effective_start", "effective_end"),
        Index("ix_medication_statement_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_statement_id = Column(
        BigInteger,
        medication_statement_id_seq,
        server_default=medication_statement_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MedicationStatementStatus,
            name="medication_statement_status",
            # Store `entered-in-error` / `on-hold` / `not-taken`, not the Python member names.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # effective[x] (0..1 dateTime | Period): the half-open [start, end) range it covers.
    effective_start = Column(DateTime(timezone=True), nullable=True)
    effective_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # context (0..1 Reference(Encounter | EpisodeOfCare))
    context_reference = Column(String, nullable=True)
    context_type = Column(String, nullable=True)
    context_id = Column(BigInteger, nullable=True, index=True)
    context_identifier_system = Column(String, nullable=True)
    context_identifier_value = Column(String, nullable=True)

    # informationSource (0..1 Reference(Practitioner | Organization | Patient |
    # PractitionerRole | RelatedPerson)), searched as `source`
    source_reference = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(BigInteger, nullable=True, index=True)
    source_identifier_system = Column(String, nullable=True)
    source_identifier_value = Column(String, nullable=True)

    # medicationReference (Reference(Medication)), searched as `medication`
    medication_reference = Column(String, nullable=True)
    medication_type = Column(String, nullable=True)
    medication_id = Column(BigInteger, nullable=True, index=True)
    medication_identifier_system = Column(String, nullable=True)
    medication_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MedicationStatementIdentifier",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "MedicationStatementToken",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MedicationStatementReference",
        back_populates="medication_statement",
        cascade="all, delete-orphan",
    )

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MedicationDispenseStatus

medication_dispense_id_seq = Sequence(
    "medication_dispense_pub_seq", start=590000, increment=1, metadata=Base.metadata
)


class MedicationDispenseModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationDispense - stored whole in `content`, like MedicationAdministration,
    MedicationStatement and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.medication_dispense). Nothing else in this table
    or its child tables is a second copy of the resource: every other column exists only because
    a FHIR R4 MedicationDispense search parameter filters on it
    (https://www.hl7.org/fhir/R4/medicationdispense.html#search), and is derived from `content` on
    every write by app.repository.medication_dispense._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value, required binding)
      whenprepared      -> whenprepared_start/_end (0..1 dateTime, the half-open range it covers at
                           its written precision; columns)
      whenhandedover    -> whenhandedover_start/_end (0..1 dateTime, the same)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (0..1
                           Reference(Patient | Group), columns; `patient` is `subject` narrowed to
                           Patients)
      context           -> context_reference/_type/_id + context_identifier_* (0..1
                           Reference(Encounter | EpisodeOfCare), columns)
      medication        -> medication_reference/_type/_id + medication_identifier_* (the
                           medicationReference, Reference(Medication), columns)
      destination       -> destination_reference/_type/_id + destination_identifier_* (0..1
                           Reference(Location), columns)
      code              -> MedicationDispenseToken (param `code`: medicationCodeableConcept)
      type              -> MedicationDispenseToken (param `type`: the 0..1 type)
      identifier        -> MedicationDispenseIdentifier (one row per identifier x type coding)
      performer,
      prescription,
      receiver,
      responsibleparty  -> MedicationDispenseReference (one row per `performer.actor`,
                           `authorizingPrescription`, `receiver` and
                           `substitution.responsibleParty`, told apart by `param`)
      _id               -> medication_dispense_id;  _lastUpdated -> updated_at/created_at

    `partOf`, `statusReason[x]`, `category`, `supportingInformation`, `performer.function`,
    `location`, `quantity`, `daysSupply`, `note`, `dosageInstruction`, `substitution` (apart from
    `responsibleParty`), `detectedIssue`, `eventHistory` and `extension` have no search parameter,
    so they live only in `content`.

    `*_type` is a plain string, not a Postgres enum: `subject`, `performer`, `receiver` and
    `responsibleparty` have several targets, so a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`); `patient`, `context`, `medication`, `destination` and
    `prescription` take a type or a bare id.

    All index columns are nullable. No `user_id`: a MedicationDispense is a shared tenant-level
    entity. No DB-level CHECK constraints (R4 rules - e.g. mdd-1 - are the validator's)."""

    __tablename__ = "medication_dispense"
    __table_args__ = (
        Index(
            "ix_medication_dispense_whenprepared",
            "whenprepared_start",
            "whenprepared_end",
        ),
        Index(
            "ix_medication_dispense_whenhandedover",
            "whenhandedover_start",
            "whenhandedover_end",
        ),
        Index("ix_medication_dispense_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_dispense_id = Column(
        BigInteger,
        medication_dispense_id_seq,
        server_default=medication_dispense_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MedicationDispenseStatus,
            name="medication_dispense_status",
            # Store `in-progress` / `on-hold` / `entered-in-error`, not the member names.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # whenPrepared / whenHandedOver (0..1 dateTime): the half-open [start, end) range each covers.
    whenprepared_start = Column(DateTime(timezone=True), nullable=True)
    whenprepared_end = Column(DateTime(timezone=True), nullable=True)
    whenhandedover_start = Column(DateTime(timezone=True), nullable=True)
    whenhandedover_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Patient | Group))
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

    # medicationReference (Reference(Medication)), searched as `medication`
    medication_reference = Column(String, nullable=True)
    medication_type = Column(String, nullable=True)
    medication_id = Column(BigInteger, nullable=True, index=True)
    medication_identifier_system = Column(String, nullable=True)
    medication_identifier_value = Column(String, nullable=True)

    # destination (0..1 Reference(Location))
    destination_reference = Column(String, nullable=True)
    destination_type = Column(String, nullable=True)
    destination_id = Column(BigInteger, nullable=True, index=True)
    destination_identifier_system = Column(String, nullable=True)
    destination_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MedicationDispenseIdentifier",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "MedicationDispenseToken",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MedicationDispenseReference",
        back_populates="medication_dispense",
        cascade="all, delete-orphan",
    )

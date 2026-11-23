from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MedicationAdministrationStatus

medication_administration_id_seq = Sequence(
    "medication_administration_pub_seq",
    start=580000,
    increment=1,
    metadata=Base.metadata,
)


class MedicationAdministrationModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationAdministration - stored whole in `content`, like MedicationStatement,
    MedicationRequest and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.medication_administration). Nothing else in
    this table or its child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 MedicationAdministration search parameter filters on it
    (https://www.hl7.org/fhir/R4/medicationadministration.html#search), and is derived from
    `content` on every write by app.repository.medication_administration._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value, required binding)
      effective-time    -> effective_start/_end (1..1 dateTime *or* Period, the half-open range it
                           covers at its written precision; NULL end = open; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (1..1
                           Reference(Patient | Group), columns; `patient` is `subject` narrowed to
                           Patients)
      context           -> context_reference/_type/_id + context_identifier_* (0..1
                           Reference(Encounter | EpisodeOfCare), columns)
      medication        -> medication_reference/_type/_id + medication_identifier_* (the
                           medicationReference, Reference(Medication), columns)
      request           -> request_reference/_type/_id + request_identifier_* (0..1
                           Reference(MedicationRequest), columns)
      code              -> MedicationAdministrationToken (param `code`: medicationCodeableConcept)
      reason-given      -> MedicationAdministrationToken (param `reason-given`: every reasonCode)
      reason-not-given  -> MedicationAdministrationToken (param `reason-not-given`: every
                           statusReason)
      identifier        -> MedicationAdministrationIdentifier (one row per identifier x type
                           coding)
      device, performer -> MedicationAdministrationReference (one row per `device` reference /
                           per `performer.actor`, told apart by `param`)
      _id               -> medication_administration_id;  _lastUpdated -> updated_at/created_at

    `instantiates`, `partOf`, `category`, `supportingInformation`, `performer.function`,
    `reasonReference`, `note`, `dosage`, `eventHistory` and `extension` have no search parameter,
    so they live only in `content`.

    `*_type` is a plain string, not a Postgres enum: `subject` and `performer` have several
    targets, so a search by bare id is ambiguous (`subject=Type/id` or `subject:Type=id`);
    `patient`, `context`, `medication`, `request` and `device` take a type or a bare id.

    All index columns are nullable. No `user_id`: a MedicationAdministration is a shared
    tenant-level entity. No DB-level CHECK constraints (R4 rules - e.g. mad-1 - are the
    validator's)."""

    __tablename__ = "medication_administration"
    __table_args__ = (
        Index(
            "ix_medication_administration_effective", "effective_start", "effective_end"
        ),
        Index(
            "ix_medication_administration_subject_type_id", "subject_type", "subject_id"
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_administration_id = Column(
        BigInteger,
        medication_administration_id_seq,
        server_default=medication_administration_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MedicationAdministrationStatus,
            name="medication_administration_status",
            # Store `in-progress` / `not-done` / `entered-in-error`, not the member names.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # effective[x] (1..1 dateTime | Period): the half-open [start, end) range it covers.
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

    # medicationReference (Reference(Medication)), searched as `medication`
    medication_reference = Column(String, nullable=True)
    medication_type = Column(String, nullable=True)
    medication_id = Column(BigInteger, nullable=True, index=True)
    medication_identifier_system = Column(String, nullable=True)
    medication_identifier_value = Column(String, nullable=True)

    # request (0..1 Reference(MedicationRequest))
    request_reference = Column(String, nullable=True)
    request_type = Column(String, nullable=True)
    request_id = Column(BigInteger, nullable=True, index=True)
    request_identifier_system = Column(String, nullable=True)
    request_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MedicationAdministrationIdentifier",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "MedicationAdministrationToken",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MedicationAdministrationReference",
        back_populates="medication_administration",
        cascade="all, delete-orphan",
    )

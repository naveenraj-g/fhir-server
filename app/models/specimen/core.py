from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Index,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import SpecimenStatus

specimen_id_seq = Sequence(
    "specimen_pub_seq", start=310000, increment=1, metadata=Base.metadata
)

# The R4 targets of Specimen.subject and Specimen.collection.collector.
SUBJECT_TYPES = ("Patient", "Group", "Device", "Substance", "Location")
COLLECTOR_TYPES = ("Practitioner", "PractitionerRole")


class SpecimenModel(TenantAuditMixin, Base):
    """FHIR R4 Specimen — Medplum-style storage, same as Patient, Encounter, Condition, Procedure,
    DiagnosticReport, Observation and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns — see app.fhir.mappers.specimen). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Specimen search parameter filters on it
    (https://www.hl7.org/fhir/R4/specimen.html#search), and is derived from `content` on every
    write by app.repository.specimen._indexer.

    Search parameter -> storage:
      status           -> status (0..1 code, Enum column, stored by value so `entered-in-error`
                          is the real FHIR code)
      collected        -> collected_start/_end (`collection.collected[x]`, a dateTime or a
                          Period, as the half-open range of instants it covers; columns)
      accession        -> accession_system / accession_value (the 0..1 accessionIdentifier;
                          columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (0..1 Reference(Patient | Group | Device | Substance | Location),
                          columns; `patient` is `subject` narrowed to Patients)
      collector        -> collector_reference/_type/_id + collector_identifier_*
                          (0..1 Reference(Practitioner | PractitionerRole), columns)
      identifier       -> SpecimenIdentifier (0..*)
      container-id     -> SpecimenContainerIdentifier (container.identifier of every container)
      type, bodysite, container
                       -> SpecimenToken (one shared table, one row per coding of each concept,
                          told apart by `param`; `container` reads container.type of every
                          container)
      parent           -> SpecimenReference (one row per Reference(Specimen))
      _id              -> specimen_id;  _lastUpdated -> updated_at/created_at

    `receivedTime`, `request`, `collection.duration` / `.quantity` / `.method` /
    `.fastingStatus[x]`, `processing`, every container element except `type` and `identifier`,
    `condition`, `note` and `extension` have no search parameter and live only in `content`.

    `subject` can point at several resource types, so `reference_type` records which one a
    relative `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is ambiguous
    for it (`subject=Type/id` or `subject:Type=id`); `patient`, `parent` (one target) and
    `collector` (two) — a bare id works for `patient` and `parent` only.

    All index columns are nullable. No `user_id`: a Specimen is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "specimen"
    __table_args__ = (
        Index("ix_specimen_collected", "collected_start", "collected_end"),
        Index("ix_specimen_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    specimen_id = Column(
        BigInteger,
        specimen_id_seq,
        server_default=specimen_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            SpecimenStatus,
            name="specimen_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # collected: the half-open [start, end) range of instants collection.collected[x] covers.
    collected_start = Column(DateTime(timezone=True), nullable=True)
    collected_end = Column(DateTime(timezone=True), nullable=True)

    # accessionIdentifier (0..1 Identifier)
    accession_system = Column(String, nullable=True)
    accession_value = Column(String, nullable=True, index=True)

    # subject (0..1 Reference(Patient | Group | Device | Substance | Location))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # collection.collector (0..1 Reference(Practitioner | PractitionerRole))
    collector_reference = Column(String, nullable=True)
    collector_type = Column(String, nullable=True)
    collector_id = Column(BigInteger, nullable=True, index=True)
    collector_identifier_system = Column(String, nullable=True)
    collector_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "SpecimenIdentifier", back_populates="specimen", cascade="all, delete-orphan"
    )
    container_identifiers = relationship(
        "SpecimenContainerIdentifier",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "SpecimenToken", back_populates="specimen", cascade="all, delete-orphan"
    )
    references = relationship(
        "SpecimenReference", back_populates="specimen", cascade="all, delete-orphan"
    )

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import CommunicationStatus

communication_id_seq = Sequence(
    "communication_pub_seq", start=480000, increment=1, metadata=Base.metadata
)

# The R4 targets of the 0..1 reference elements held as columns.
SUBJECT_TYPES = ("Patient", "Group")
ENCOUNTER_TYPES = ("Encounter",)
SENDER_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "HealthcareService",
)


class CommunicationModel(TenantAuditMixin, Base):
    """FHIR R4 Communication - content-based storage, same as Task, Goal, Consent, CarePlan and
    the other rebuilt resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.communication). Every other column exists only
    because a FHIR R4 Communication search parameter filters on it
    (https://www.hl7.org/fhir/R4/communication.html#search) and is derived from `content` on every
    write by app.repository.communication._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so `in-progress` /
                          `entered-in-error` are the real FHIR codes)
      sent, received   -> sent_start/_end and received_start/_end (the half-open range each
                          dateTime covers; NULL = absent; columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_* (0..1
                          Reference(Patient | Group), columns; `patient` is `subject` narrowed to
                          Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (0..1
                          Reference(Encounter), columns)
      sender           -> sender_reference/_type/_id + sender_identifier_* (0..1 reference to one
                          of seven types, columns)
      identifier       -> CommunicationIdentifier (0..*)
      category, medium -> CommunicationToken (one shared table, one row per coding of each
                          concept, told apart by `param`)
      based-on, part-of, recipient, instantiates-canonical
                       -> CommunicationReference (one shared table, told apart by `param`;
                          `based-on` and `part-of` are Reference(Any), `instantiates-canonical`
                          holds canonical URLs)
      instantiates-uri -> CommunicationInstantiatesUri (one row per URI)
      _id              -> communication_id;  _lastUpdated -> updated_at/created_at

    **R4 defines no search parameter for `priority`, `statusReason`, `topic`, `about`,
    `inResponseTo`, `reasonCode`, `reasonReference`, `payload` or `note`**, so none of them has a
    column or an enum (the old `communication_priority` enum was dropped; the values live only in
    `content`).

    `subject`, `sender` and `recipient` point at several resource types, so a search by bare id is
    ambiguous (`subject=Type/id` or `subject:Type=id`); `based-on` and `part-of` are
    Reference(Any); `patient` is `subject` narrowed to Patients (a bare id works; a Group or
    logical subject counts as missing it); `encounter` has one target.

    All index columns are nullable. No `user_id`: a Communication is a shared tenant-level entity.
    No DB-level CHECK constraints."""

    __tablename__ = "communication"
    __table_args__ = (
        Index("ix_communication_sent", "sent_start", "sent_end"),
        Index("ix_communication_received", "received_start", "received_end"),
        Index("ix_communication_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    communication_id = Column(
        BigInteger,
        communication_id_seq,
        server_default=communication_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            CommunicationStatus,
            name="communication_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # sent / received (dateTime): half-open [start, end) ranges (NULL = absent).
    sent_start = Column(DateTime(timezone=True), nullable=True)
    sent_end = Column(DateTime(timezone=True), nullable=True)
    received_start = Column(DateTime(timezone=True), nullable=True)
    received_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Patient | Group))
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

    # sender (0..1 Reference(Device | Organization | Patient | Practitioner | ...))
    sender_reference = Column(String, nullable=True)
    sender_type = Column(String, nullable=True)
    sender_id = Column(BigInteger, nullable=True, index=True)
    sender_identifier_system = Column(String, nullable=True)
    sender_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "CommunicationIdentifier",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "CommunicationToken",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "CommunicationReference",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    instantiates_uris = relationship(
        "CommunicationInstantiatesUri",
        back_populates="communication",
        cascade="all, delete-orphan",
    )

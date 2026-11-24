from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import CommunicationRequestPriority, CommunicationRequestStatus

communication_request_id_seq = Sequence(
    "communication_request_pub_seq", start=470000, increment=1, metadata=Base.metadata
)

# The R4 targets of the 0..1 reference elements held as columns.
SUBJECT_TYPES = ("Patient", "Group")
ENCOUNTER_TYPES = ("Encounter",)
REQUESTER_TYPES = (
    "Practitioner",
    "Organization",
    "Device",
    "Patient",
    "PractitionerRole",
    "RelatedPerson",
)
SENDER_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "HealthcareService",
)


class CommunicationRequestModel(TenantAuditMixin, Base):
    """FHIR R4 CommunicationRequest - content-based storage, same as Communication, Task, Goal and
    the other rebuilt resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.communication_request). Every other column exists
    only because a FHIR R4 CommunicationRequest search parameter filters on it
    (https://www.hl7.org/fhir/R4/communicationrequest.html#search) and is derived from `content` on
    every write by app.repository.communication_request._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so `on-hold` /
                          `entered-in-error` are the real FHIR codes)
      priority         -> priority (0..1 code, Enum column: a required binding read by a search
                          parameter)
      authored         -> authored_start/_end (the half-open range `authoredOn` covers; columns)
      occurrence       -> occurrence_start/_end (the range `occurrenceDateTime` covers - R4's
                          expression is `(CommunicationRequest.occurrence as dateTime)`, so an
                          `occurrencePeriod` is not indexed and counts as missing; columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_* (0..1
                          Reference(Patient | Group), columns; `patient` is `subject` narrowed to
                          Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (0..1
                          Reference(Encounter), columns)
      requester        -> requester_reference/_type/_id + requester_identifier_* (0..1 reference
                          to one of six types, columns)
      sender           -> sender_reference/_type/_id + sender_identifier_* (0..1 reference to one
                          of seven types, columns)
      group-identifier -> group_identifier_system/_value (0..1 Identifier, columns)
      identifier       -> CommunicationRequestIdentifier (0..*)
      category, medium -> CommunicationRequestToken (one shared table, one row per coding of each
                          concept, told apart by `param`)
      based-on, replaces, recipient
                       -> CommunicationRequestReference (one shared table, told apart by `param`;
                          `based-on` is Reference(Any))
      _id              -> communication_request_id;  _lastUpdated -> updated_at/created_at

    Everything else - `statusReason`, `doNotPerform`, `about`, `payload`, `reasonCode`,
    `reasonReference`, `note`, `occurrencePeriod`, `extension` - lives only in `content`.

    `subject`, `requester`, `sender` and `recipient` point at several resource types, so a search
    by bare id is ambiguous (`subject=Type/id` or `subject:Type=id`); `based-on` is Reference(Any);
    `patient` is `subject` narrowed to Patients (a bare id works; a Group or logical subject counts
    as missing it); `encounter` and `replaces` have one target.

    All index columns are nullable. No `user_id`: a CommunicationRequest is a shared tenant-level
    entity. No DB-level CHECK constraints."""

    __tablename__ = "communication_request"
    __table_args__ = (
        Index("ix_communication_request_authored", "authored_start", "authored_end"),
        Index(
            "ix_communication_request_occurrence", "occurrence_start", "occurrence_end"
        ),
        Index("ix_communication_request_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    communication_request_id = Column(
        BigInteger,
        communication_request_id_seq,
        server_default=communication_request_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            CommunicationRequestStatus,
            name="communication_request_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )
    priority = Column(
        Enum(
            CommunicationRequestPriority,
            name="communication_request_priority",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # authoredOn / occurrenceDateTime: half-open [start, end) ranges (NULL = absent).
    authored_start = Column(DateTime(timezone=True), nullable=True)
    authored_end = Column(DateTime(timezone=True), nullable=True)
    occurrence_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_end = Column(DateTime(timezone=True), nullable=True)

    # groupIdentifier (0..1 Identifier)
    group_identifier_system = Column(String, nullable=True)
    group_identifier_value = Column(String, nullable=True)

    # subject (0..1 Reference)
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # encounter (0..1 Reference)
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)

    # requester (0..1 Reference)
    requester_reference = Column(String, nullable=True)
    requester_type = Column(String, nullable=True)
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_identifier_system = Column(String, nullable=True)
    requester_identifier_value = Column(String, nullable=True)

    # sender (0..1 Reference)
    sender_reference = Column(String, nullable=True)
    sender_type = Column(String, nullable=True)
    sender_id = Column(BigInteger, nullable=True, index=True)
    sender_identifier_system = Column(String, nullable=True)
    sender_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "CommunicationRequestIdentifier",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "CommunicationRequestToken",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "CommunicationRequestReference",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )

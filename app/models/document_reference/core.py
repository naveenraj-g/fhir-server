from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import DocumentReferenceStatus

document_reference_id_seq = Sequence(
    "document_reference_pub_seq", start=320000, increment=1, metadata=Base.metadata
)

# The R4 targets of DocumentReference.subject, .authenticator and .custodian.
SUBJECT_TYPES = ("Patient", "Practitioner", "Group", "Device")
AUTHENTICATOR_TYPES = ("Practitioner", "Organization", "PractitionerRole")
CUSTODIAN_TYPES = ("Organization",)


class DocumentReferenceModel(TenantAuditMixin, Base):
    """FHIR R4 DocumentReference - Medplum-style storage, same as CareTeam, CarePlan, Encounter
    and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.document_reference). Nothing else in this table
    or its child tables is a second copy of the resource: every other column exists only because
    a FHIR R4 DocumentReference search parameter filters on it
    (https://www.hl7.org/fhir/R4/documentreference.html#search), and is derived from `content` on
    every write by app.repository.document_reference._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value so `entered-in-error` is the
                           real FHIR code; required binding)
      date              -> date (0..1 instant, column)
      description       -> description + description_norm (0..1 string, columns)
      period            -> context_period_start/_end (`context.period`, the half-open range of
                           instants it covers; NULL = open; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (0..1
                           Reference(Patient | Practitioner | Group | Device), columns; `patient`
                           is `subject` narrowed to Patients)
      authenticator     -> authenticator_reference/_type/_id + _identifier_* (0..1, columns)
      custodian         -> custodian_reference/_type/_id + _identifier_* (0..1
                           Reference(Organization), columns)
      identifier        -> DocumentReferenceIdentifier (masterIdentifier and every identifier)
      type, category,
      security-label,
      event, facility,
      setting           -> DocumentReferenceToken (one row per coding of each concept)
      author, encounter,
      related           -> DocumentReferenceReference (one row per Reference)
      relatesto,
      relation,
      relationship      -> DocumentReferenceRelatesTo (one row per relatesTo entry)
      contenttype,
      language,
      location, format  -> DocumentReferenceContent (one row per content entry)
      _id               -> document_reference_id;  _lastUpdated -> updated_at/created_at

    `docStatus`, `content.attachment` (apart from contentType, language and url) and
    `context.sourcePatientInfo` have no search parameter and live only in `content`, as does
    `extension`.

    `subject`, `author`, `authenticator` and `context.encounter` can point at several resource
    types, so `*_type` / `reference_type` records which one a relative `Type/<id>` names (a plain
    string, not a Postgres enum): a search by bare id is ambiguous for them (`subject=Type/id` or
    `subject:Type=id`); `patient`, `custodian` and `relatesto` have one target, so a bare id works.

    All index columns are nullable. No `user_id`: a DocumentReference is a shared tenant-level
    entity. No DB-level CHECK constraints (rule docRef-1, `relatesTo` must name a
    DocumentReference, is the validator's)."""

    __tablename__ = "document_reference"
    __table_args__ = (
        Index(
            "ix_document_reference_context_period",
            "context_period_start",
            "context_period_end",
        ),
        Index("ix_document_reference_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    document_reference_id = Column(
        BigInteger,
        document_reference_id_seq,
        server_default=document_reference_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            DocumentReferenceStatus,
            name="document_reference_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # date (0..1 instant)
    date = Column(DateTime(timezone=True), nullable=True)

    # description (0..1 string): raw (answers :exact) and normalized (starts-with / :contains)
    description = Column(String, nullable=True)
    description_norm = Column(String, nullable=True)

    # context.period: the half-open [start, end) range of instants it covers.
    context_period_start = Column(DateTime(timezone=True), nullable=True)
    context_period_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Patient | Practitioner | Group | Device))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # authenticator (0..1 Reference(Practitioner | Organization | PractitionerRole))
    authenticator_reference = Column(String, nullable=True)
    authenticator_type = Column(String, nullable=True)
    authenticator_id = Column(BigInteger, nullable=True, index=True)
    authenticator_identifier_system = Column(String, nullable=True)
    authenticator_identifier_value = Column(String, nullable=True)

    # custodian (0..1 Reference(Organization))
    custodian_reference = Column(String, nullable=True)
    custodian_type = Column(String, nullable=True)
    custodian_id = Column(BigInteger, nullable=True, index=True)
    custodian_identifier_system = Column(String, nullable=True)
    custodian_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "DocumentReferenceIdentifier",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "DocumentReferenceToken",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "DocumentReferenceReference",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    relates_to = relationship(
        "DocumentReferenceRelatesTo",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )
    contents = relationship(
        "DocumentReferenceContent",
        back_populates="document_reference",
        cascade="all, delete-orphan",
    )

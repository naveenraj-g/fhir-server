from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ConsentStatus

consent_id_seq = Sequence(
    "consent_pub_seq", start=440000, increment=1, metadata=Base.metadata
)

# The R4 targets of the reference elements held as columns.
PATIENT_TYPES = ("Patient",)
SOURCE_TYPES = ("Consent", "DocumentReference", "Contract", "QuestionnaireResponse")


class ConsentModel(TenantAuditMixin, Base):
    """FHIR R4 Consent - content-based storage, same as Goal, Task, Flag, CarePlan and the other
    rebuilt resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.consent). Every other column exists only because
    a FHIR R4 Consent search parameter filters on it
    (https://www.hl7.org/fhir/R4/consent.html#search) and is derived from `content` on every write
    by app.repository.consent._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so `entered-in-error` is
                          the real FHIR code)
      date             -> date_start/_end (`dateTime`, the half-open range it covers; columns)
      period           -> period_start/_end (`provision.period`, the half-open range of instants it
                          covers; NULL = open; columns)
      patient          -> patient_reference/_type/_id + patient_identifier_* (0..1
                          Reference(Patient), columns)
      source-reference -> source_reference/_type/_id + source_identifier_* (`sourceReference` of
                          the 0..1 source[x]: Reference(Consent | DocumentReference | Contract |
                          QuestionnaireResponse), columns; a `sourceAttachment` is not a
                          reference, so it counts as missing)
      identifier       -> ConsentIdentifier (0..*)
      category, scope, action, purpose, security-label
                       -> ConsentToken (one shared table, one row per coding of each concept,
                          told apart by `param`; `action` reads `provision.action`, `purpose` and
                          `security-label` the Codings `provision.purpose` / `.securityLabel`)
      consentor, organization, actor, data
                       -> ConsentReference (one shared table, told apart by `param`; `consentor`
                          reads `performer`, `actor` reads `provision.actor.reference`, `data`
                          reads `provision.data.reference`, a Reference(Any))
      _id              -> consent_id;  _lastUpdated -> updated_at/created_at

    **The search parameters read the top-level `provision` only** (R4's expressions are
    `Consent.provision.actor.reference`, not a recursive path): an actor, data reference, action,
    purpose, security label or period of a nested `provision.provision` is stored in `content` but
    not indexed. `policy`, `policyRule`, `verification`, `provision.type`, `.class`, `.code`,
    `.dataPeriod`, `.actor.role`, `.data.meaning` and `extension` have no search parameter and
    live only in `content`.

    `actor` (eight types), `consentor` (five) and `source-reference` (four) are multi-target (a
    search by bare id is ambiguous: `actor=Type/id` or `actor:Type=id`); `data` is Reference(Any);
    `patient` and `organization` have one target, so a bare id works.

    All index columns are nullable. No `user_id`: a Consent is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "consent"
    __table_args__ = (
        Index("ix_consent_date", "date_start", "date_end"),
        Index("ix_consent_period", "period_start", "period_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    consent_id = Column(
        BigInteger,
        consent_id_seq,
        server_default=consent_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            ConsentStatus,
            name="consent_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # dateTime and provision.period: half-open [start, end) ranges (NULL = absent / open).
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # patient (0..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    # source[x] when it is a Reference(Consent | DocumentReference | Contract | QuestionnaireResponse)
    source_reference = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(BigInteger, nullable=True, index=True)
    source_identifier_system = Column(String, nullable=True)
    source_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "ConsentIdentifier", back_populates="consent", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "ConsentToken", back_populates="consent", cascade="all, delete-orphan"
    )
    references = relationship(
        "ConsentReference", back_populates="consent", cascade="all, delete-orphan"
    )

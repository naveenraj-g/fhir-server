from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import QuestionnaireResponseStatus

questionnaire_response_id_seq = Sequence(
    "questionnaire_response_pub_seq", start=60000, increment=1, metadata=Base.metadata
)


class QuestionnaireResponseModel(TenantAuditMixin, Base):
    """FHIR R4 QuestionnaireResponse - stored whole in `content`, like CareTeam, CarePlan,
    Encounter and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.questionnaire_response). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 QuestionnaireResponse search parameter filters on it
    (https://www.hl7.org/fhir/R4/questionnaireresponse.html#search), and is derived from `content`
    on every write by app.repository.questionnaire_response._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value so `in-progress` and
                           `entered-in-error` are the real FHIR codes; required binding)
      authored          -> authored_start/_end (0..1 dateTime, the half-open range it covers at
                           its written precision; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_* (0..1
                           Reference(Any), columns; `patient` is `subject` narrowed to Patients)
      encounter         -> encounter_reference/_type/_id + encounter_identifier_* (0..1, columns)
      author            -> author_reference/_type/_id + author_identifier_* (0..1, columns)
      source            -> source_reference/_type/_id + source_identifier_* (0..1, columns)
      identifier        -> QuestionnaireResponseIdentifier (0..1 identifier)
      based-on, part-of,
      questionnaire     -> QuestionnaireResponseReference (one row per Reference / canonical)
      _id               -> questionnaire_response_id;  _lastUpdated -> updated_at/created_at

    **`item` has no search parameter at all** (R4 defines none), so the answers - the nested
    `item` / `answer` / `answer.item` tree and every `value[x]` - live only in `content`; nothing of
    it is indexed. `extension` too.

    `subject` is Reference(Any), so `*_type` records which type a relative `Type/<id>` names (a
    plain string, not a Postgres enum): a search by bare id is ambiguous for `subject`, `author`,
    `source`, `based-on` and `part-of` (`subject=Type/id` or `subject:Type=id`); `patient` and
    `encounter` have one target, so a bare id works.

    All index columns are nullable. No `user_id`: a QuestionnaireResponse is a shared tenant-level
    entity. No DB-level CHECK constraints (rules qrs-1 - an item has `item` or `answer`, not both
    - is the validator's)."""

    __tablename__ = "questionnaire_response"
    __table_args__ = (
        Index("ix_questionnaire_response_authored", "authored_start", "authored_end"),
        Index(
            "ix_questionnaire_response_subject_type_id", "subject_type", "subject_id"
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    questionnaire_response_id = Column(
        BigInteger,
        questionnaire_response_id_seq,
        server_default=questionnaire_response_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            QuestionnaireResponseStatus,
            name="questionnaire_response_status",
            # Store `in-progress` / `entered-in-error`, not the Python member names.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # authored (0..1 dateTime): the half-open [start, end) range of instants it covers.
    authored_start = Column(DateTime(timezone=True), nullable=True)
    authored_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Any))
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

    # author (0..1 Reference(Device | Practitioner | PractitionerRole | Patient | RelatedPerson |
    # Organization))
    author_reference = Column(String, nullable=True)
    author_type = Column(String, nullable=True)
    author_id = Column(BigInteger, nullable=True, index=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)

    # source (0..1 Reference(Patient | Practitioner | PractitionerRole | RelatedPerson))
    source_reference = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(BigInteger, nullable=True, index=True)
    source_identifier_system = Column(String, nullable=True)
    source_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "QuestionnaireResponseIdentifier",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "QuestionnaireResponseReference",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )

from sqlalchemy import BigInteger, Column, DateTime, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

flag_id_seq = Sequence(
    "flag_pub_seq", start=450000, increment=1, metadata=Base.metadata
)

# The R4 targets of the 0..1 / 1..1 reference elements held as columns.
SUBJECT_TYPES = (
    "Patient",
    "Location",
    "Group",
    "Organization",
    "Practitioner",
    "PlanDefinition",
    "Medication",
    "Procedure",
)
ENCOUNTER_TYPES = ("Encounter",)
AUTHOR_TYPES = ("Device", "Organization", "Patient", "Practitioner", "PractitionerRole")


class FlagModel(TenantAuditMixin, Base):
    """FHIR R4 Flag - content-based storage, same as Goal, Task, CarePlan and the other rebuilt
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.flag). Every other column exists only because a
    FHIR R4 Flag search parameter filters on it (https://www.hl7.org/fhir/R4/flag.html#search)
    and is derived from `content` on every write by app.repository.flag._indexer.

    Search parameter -> storage:
      date             -> period_start/_end (`period`, the half-open range of instants it covers;
                          NULL = open; columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_* (1..1 reference to one
                          of eight types, columns; `patient` is `subject` narrowed to Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (0..1
                          Reference(Encounter), columns)
      author           -> author_reference/_type/_id + author_identifier_* (0..1 reference to one
                          of five types, columns)
      identifier       -> FlagIdentifier (0..*)
      _id              -> flag_id;  _lastUpdated -> updated_at/created_at

    **R4 defines no search parameter for `status`, `category` or `code`**, so none of them has a
    column or an enum (the old `flag_status` enum was dropped; the values live only in `content`)
    and `?status=` / `?category=` / `?code=` are unknown parameters. `extension` lives only in
    `content` too.

    `subject` and `author` point at several resource types, so a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`); `patient` is `subject` narrowed to Patients (a
    reference to another type or a logical subject counts as missing it); `encounter` has one
    target so a bare id works.

    All index columns are nullable. No `user_id`: a Flag is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "flag"
    __table_args__ = (
        Index("ix_flag_period", "period_start", "period_end"),
        Index("ix_flag_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    flag_id = Column(
        BigInteger,
        flag_id_seq,
        server_default=flag_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Location | Group | Organization | Practitioner | ...))
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

    # author (0..1 Reference(Device | Organization | Patient | Practitioner | PractitionerRole))
    author_reference = Column(String, nullable=True)
    author_type = Column(String, nullable=True)
    author_id = Column(BigInteger, nullable=True, index=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "FlagIdentifier", back_populates="flag", cascade="all, delete-orphan"
    )

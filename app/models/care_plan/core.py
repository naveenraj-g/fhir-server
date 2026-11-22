from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import CarePlanIntent, CarePlanStatus

care_plan_id_seq = Sequence(
    "care_plan_pub_seq", start=290000, increment=1, metadata=Base.metadata
)

# The R4 targets of CarePlan.subject and CarePlan.encounter.
SUBJECT_TYPES = ("Patient", "Group")
ENCOUNTER_TYPES = ("Encounter",)


class CarePlanModel(TenantAuditMixin, Base):
    """FHIR R4 CarePlan - Medplum-style storage, same as Patient, Encounter, Condition,
    ServiceRequest, CareTeam, Group and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.care_plan). Nothing else in this table or its
    child tables is a second copy of the resource: every other column exists only because a FHIR
    R4 CarePlan search parameter filters on it
    (https://www.hl7.org/fhir/R4/careplan.html#search), and is derived from `content` on every
    write by app.repository.care_plan._indexer.

    Search parameter -> storage:
      status, intent    -> status / intent (1..1 codes, Enum columns, stored by value so
                           `entered-in-error` / `on-hold` are the real FHIR codes)
      date              -> period_start/_end (`period`, the half-open range of instants it
                           covers; NULL = open; columns)
      subject, patient  -> subject_reference/_type/_id + subject_identifier_*
                           (1..1 Reference(Patient | Group), columns; `patient` is `subject`
                           narrowed to Patients)
      encounter         -> encounter_reference/_type/_id + encounter_identifier_*
                           (0..1 Reference(Encounter), columns)
      identifier        -> CarePlanIdentifier (0..*)
      category, activity-code
                        -> CarePlanToken (one shared table, one row per coding of each concept,
                           told apart by `param`; `activity-code` reads activity.detail.code of
                           every activity)
      based-on, replaces, part-of, care-team, condition, goal, instantiates-canonical
                        -> CarePlanReference (one shared table, told apart by `param`;
                           `condition` reads `addresses`)
      instantiates-uri  -> CarePlanInstantiatesUri (one row per URI)
      performer         -> CarePlanPerformer (activity.detail.performer of every activity)
      activity-reference, activity-date
                        -> CarePlanActivity (one row per activity with a reference or a schedule)
      _id               -> care_plan_id;  _lastUpdated -> updated_at/created_at

    `title`, `description`, `created`, `author`, `contributor`, `supportingInfo`, `note`, every
    `activity` element except the ones above and `extension` have no search parameter and live
    only in `content`.

    `subject`, `performer` and `activity-reference` can point at several resource types, so
    `reference_type` records which one a relative `Type/<id>` names (a plain string, not a
    Postgres enum): a search by bare id is ambiguous for them (`subject=Type/id` or
    `subject:Type=id`); `patient`, `encounter`, `based-on`, `replaces`, `part-of`, `care-team`,
    `condition` and `goal` have one target, so a bare id works.

    All index columns are nullable: R4 makes `status`, `intent` and `subject` mandatory, but that
    is the validator's rule (enforced by the `java_validator` backend), not the database's. No
    `user_id`: a CarePlan is a shared tenant-level entity. No DB-level CHECK constraints (rule
    cpl-3, an activity has a `reference` or a `detail`, not both, is the validator's)."""

    __tablename__ = "care_plan"
    __table_args__ = (
        Index("ix_care_plan_period", "period_start", "period_end"),
        Index("ix_care_plan_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    care_plan_id = Column(
        BigInteger,
        care_plan_id_seq,
        server_default=care_plan_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            CarePlanStatus,
            name="care_plan_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )
    intent = Column(
        Enum(
            CarePlanIntent,
            name="care_plan_intent",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # period: the half-open [start, end) range of instants CarePlan.period covers.
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group))
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

    identifiers = relationship(
        "CarePlanIdentifier", back_populates="care_plan", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "CarePlanToken", back_populates="care_plan", cascade="all, delete-orphan"
    )
    references = relationship(
        "CarePlanReference", back_populates="care_plan", cascade="all, delete-orphan"
    )
    performers = relationship(
        "CarePlanPerformer", back_populates="care_plan", cascade="all, delete-orphan"
    )
    instantiates_uris = relationship(
        "CarePlanInstantiatesUri",
        back_populates="care_plan",
        cascade="all, delete-orphan",
    )
    activities = relationship(
        "CarePlanActivity", back_populates="care_plan", cascade="all, delete-orphan"
    )

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import CareTeamStatus

care_team_id_seq = Sequence(
    "care_team_pub_seq", start=390000, increment=1, metadata=Base.metadata
)

# The R4 targets of CareTeam.subject and CareTeam.encounter.
SUBJECT_TYPES = ("Patient", "Group")
ENCOUNTER_TYPES = ("Encounter",)


class CareTeamModel(TenantAuditMixin, Base):
    """FHIR R4 CareTeam - Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, Specimen, Group and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns - see app.fhir.mappers.care_team). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 CareTeam search parameter filters on it
    (https://www.hl7.org/fhir/R4/careteam.html#search), and is derived from `content` on every
    write by app.repository.care_team._indexer.

    Search parameter -> storage:
      status           -> status (0..1 code, Enum column, stored by value so `entered-in-error`
                          is the real FHIR code)
      date             -> period_start/_end (`period`, the half-open range of instants it
                          covers; NULL = open; columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (0..1 Reference(Patient | Group), columns; `patient` is `subject`
                          narrowed to Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
                          (0..1 Reference(Encounter), columns)
      identifier       -> CareTeamIdentifier (0..*)
      category         -> CareTeamToken (one row per coding of each category)
      participant      -> CareTeamParticipant (one row per participant.member)
      _id              -> care_team_id;  _lastUpdated -> updated_at/created_at

    `name`, `participant.role` / `.onBehalfOf` / `.period`, `reasonCode`, `reasonReference`,
    `managingOrganization`, `telecom`, `note` and `extension` have no search parameter and live
    only in `content`.

    `subject` and `participant.member` can point at several resource types, so `reference_type`
    records which one a relative `Type/<id>` names (a plain string, not a Postgres enum): a
    search by bare id is ambiguous for them (`subject=Type/id` or `subject:Type=id`);
    `patient` and `encounter` have one target, so a bare id works.

    All index columns are nullable. No `user_id`: a CareTeam is a shared tenant-level entity.
    No DB-level CHECK constraints (rule ctm-1, `onBehalfOf` only when the member is a
    Practitioner, is the validator's)."""

    __tablename__ = "care_team"
    __table_args__ = (
        Index("ix_care_team_period", "period_start", "period_end"),
        Index("ix_care_team_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    care_team_id = Column(
        BigInteger,
        care_team_id_seq,
        server_default=care_team_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            CareTeamStatus,
            name="care_team_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # period: the half-open [start, end) range of instants CareTeam.period covers.
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

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

    identifiers = relationship(
        "CareTeamIdentifier", back_populates="care_team", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "CareTeamToken", back_populates="care_team", cascade="all, delete-orphan"
    )
    participants = relationship(
        "CareTeamParticipant", back_populates="care_team", cascade="all, delete-orphan"
    )

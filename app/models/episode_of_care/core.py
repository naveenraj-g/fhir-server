from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import EpisodeOfCareStatus

episode_of_care_id_seq = Sequence(
    "episode_of_care_pub_seq", start=350000, increment=1, metadata=Base.metadata
)

# The R4 targets of EpisodeOfCare.patient, .managingOrganization and .careManager.
PATIENT_TYPES = ("Patient",)
ORGANIZATION_TYPES = ("Organization",)
CARE_MANAGER_TYPES = ("Practitioner", "PractitionerRole")


class EpisodeOfCareModel(TenantAuditMixin, Base):
    """FHIR R4 EpisodeOfCare - Medplum-style storage, same as CareTeam, CarePlan, Encounter and
    the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.episode_of_care). Nothing else in this table or
    its child tables is a second copy of the resource: every other column exists only because a
    FHIR R4 EpisodeOfCare search parameter filters on it
    (https://www.hl7.org/fhir/R4/episodeofcare.html#search), and is derived from `content` on
    every write by app.repository.episode_of_care._indexer.

    Search parameter -> storage:
      status            -> status (Enum column, stored by value so `entered-in-error` is the
                           real FHIR code; required binding)
      date              -> period_start/_end (`period`, the half-open range of instants it
                           covers; NULL = open; columns)
      patient           -> patient_reference/_type/_id + patient_identifier_* (1..1
                           Reference(Patient), columns)
      organization      -> managing_organization_reference/_type/_id + _identifier_* (0..1
                           Reference(Organization), columns)
      care-manager      -> care_manager_reference/_type/_id + _identifier_* (0..1
                           Reference(Practitioner | PractitionerRole), columns; the parameter is
                           `careManager` resolved to a Practitioner)
      identifier        -> EpisodeOfCareIdentifier (0..*)
      type              -> EpisodeOfCareToken (one row per coding of each type)
      condition,
      incoming-referral -> EpisodeOfCareReference (one row per diagnosis.condition /
                           referralRequest)
      _id               -> episode_of_care_id;  _lastUpdated -> updated_at/created_at

    `statusHistory`, `diagnosis.role` / `.rank`, `team`, `account` and `extension` have no search
    parameter and live only in `content`.

    All index columns are nullable. No `user_id`: an EpisodeOfCare is a shared tenant-level
    entity. No DB-level CHECK constraints."""

    __tablename__ = "episode_of_care"
    __table_args__ = (
        Index("ix_episode_of_care_period", "period_start", "period_end"),
        Index("ix_episode_of_care_patient_type_id", "patient_type", "patient_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    episode_of_care_id = Column(
        BigInteger,
        episode_of_care_id_seq,
        server_default=episode_of_care_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            EpisodeOfCareStatus,
            name="episode_of_care_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # period: the half-open [start, end) range of instants EpisodeOfCare.period covers.
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    # managingOrganization (0..1 Reference(Organization))
    managing_organization_reference = Column(String, nullable=True)
    managing_organization_type = Column(String, nullable=True)
    managing_organization_id = Column(BigInteger, nullable=True, index=True)
    managing_organization_identifier_system = Column(String, nullable=True)
    managing_organization_identifier_value = Column(String, nullable=True)

    # careManager (0..1 Reference(Practitioner | PractitionerRole))
    care_manager_reference = Column(String, nullable=True)
    care_manager_type = Column(String, nullable=True)
    care_manager_id = Column(BigInteger, nullable=True, index=True)
    care_manager_identifier_system = Column(String, nullable=True)
    care_manager_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "EpisodeOfCareIdentifier",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "EpisodeOfCareToken",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "EpisodeOfCareReference",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
    )

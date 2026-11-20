from sqlalchemy import BigInteger, Column, DateTime, Enum, Numeric, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import EncounterStatus

encounter_id_seq = Sequence("encounter_pub_seq", start=20000, increment=1, metadata=Base.metadata)

# The two R4 targets of Encounter.subject.
SUBJECT_TYPES = ("Patient", "Group")


class EncounterModel(TenantAuditMixin, Base):
    """FHIR R4 Encounter — Medplum-style storage, same as Organization,
    Location, Practitioner, HealthcareService, Endpoint, PractitionerRole,
    Schedule, Slot, Patient, Appointment and AppointmentResponse.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.encounter). Nothing else in this table or its child tables
    is a second copy of the resource: every other column exists only because a
    FHIR R4 Encounter search parameter filters on it
    (https://www.hl7.org/fhir/R4/encounter.html#search), and is derived from
    `content` on every write by app.repository.encounter._indexer.

    Search parameter -> storage:
      status          -> status (1..1 code, Enum column, stored by value)
      class           -> class_system / class_code / class_display_norm
                         (1..1 Coding, columns)
      date            -> period_start / period_end (0..1 Period, half-open range)
      length          -> length_value / length_system / length_code /
                         length_unit (0..1 Duration, a quantity search)
      subject, patient -> subject_* (0..1 Reference(Group | Patient))
      part-of         -> part_of_* (0..1 Reference(Encounter))
      service-provider -> service_provider_* (0..1 Reference(Organization))
      identifier      -> EncounterIdentifier (0..*)
      type, reason-code, special-arrangement, participant-type
                      -> EncounterToken (one row per coding, `param` says which)
      account, appointment, based-on, diagnosis, episode-of-care,
      reason-reference -> EncounterReference (one row per Reference, `param`
                         says which; `reference_type` is the target type)
      participant, practitioner -> EncounterParticipant (one row per
                         participant individual)
      location, location-period -> EncounterLocation (one row per location)
      _id             -> encounter_id;  _lastUpdated -> updated_at/created_at

    `statusHistory`, `classHistory`, `serviceType`, `priority`,
    `participant.period`, `diagnosis.use/rank`, `hospitalization` (apart from
    `specialArrangement`), `location.status/physicalType` and `extension` have
    no search parameter and live only in `content`.

    All index columns are nullable: R4 makes `status` and `class` mandatory,
    but that is the validator's rule (enforced by the `java_validator`
    backend), not the database's. No `user_id`: an Encounter is a shared
    tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "encounter"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    encounter_id = Column(
        BigInteger,
        encounter_id_seq,
        server_default=encounter_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            EncounterStatus,
            name="encounter_status",
            # Store `in-progress` / `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # Encounter.class (a bare Coding)
    class_system = Column(String, nullable=True)
    class_code = Column(String, nullable=True, index=True)
    class_display_norm = Column(String, nullable=True)

    # Encounter.period
    period_start = Column(DateTime(timezone=True), nullable=True, index=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Encounter.length (Duration)
    length_value = Column(Numeric, nullable=True)
    length_system = Column(String, nullable=True)
    length_code = Column(String, nullable=True)
    length_unit = Column(String, nullable=True)

    # Encounter.subject — Reference(Group | Patient); `subject_type` is a plain string.
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # Encounter.partOf — Reference(Encounter)
    part_of_reference = Column(String, nullable=True)
    part_of_type = Column(String, nullable=True)
    part_of_id = Column(BigInteger, nullable=True, index=True)
    part_of_identifier_system = Column(String, nullable=True)
    part_of_identifier_value = Column(String, nullable=True)

    # Encounter.serviceProvider — Reference(Organization)
    service_provider_reference = Column(String, nullable=True)
    service_provider_type = Column(String, nullable=True)
    service_provider_id = Column(BigInteger, nullable=True, index=True)
    service_provider_identifier_system = Column(String, nullable=True)
    service_provider_identifier_value = Column(String, nullable=True)

    identifiers = relationship("EncounterIdentifier", back_populates="encounter", cascade="all, delete-orphan")
    tokens = relationship("EncounterToken", back_populates="encounter", cascade="all, delete-orphan")
    references = relationship("EncounterReference", back_populates="encounter", cascade="all, delete-orphan")
    participants = relationship("EncounterParticipant", back_populates="encounter", cascade="all, delete-orphan")
    locations = relationship("EncounterLocation", back_populates="encounter", cascade="all, delete-orphan")

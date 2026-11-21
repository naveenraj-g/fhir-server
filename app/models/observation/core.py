from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ObservationStatus

observation_id_seq = Sequence("observation_pub_seq", start=160000, increment=1, metadata=Base.metadata)

# The R4 targets of Observation.subject and Observation.device.
SUBJECT_TYPES = ("Patient", "Group", "Device", "Location")
DEVICE_TYPES = ("Device", "DeviceMetric")


class ObservationModel(TenantAuditMixin, Base):
    """FHIR R4 Observation — Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, DiagnosticReport, RiskAssessment and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns — see app.fhir.mappers.observation). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Observation search parameter filters on it
    (https://www.hl7.org/fhir/R4/observation.html#search), and is derived from `content` on
    every write by app.repository.observation._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so `entered-in-error`
                          is the real FHIR code)
      date             -> date_start/_end (`effective[x]`: a dateTime, instant, Period or Timing,
                          as the half-open range of instants it covers; columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (0..1 Reference(Patient | Group | Device | Location), columns;
                          `patient` is `subject` narrowed to Patients)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_* (columns)
      specimen         -> specimen_reference/_type/_id + specimen_identifier_* (columns)
      device           -> device_reference/_type/_id + device_identifier_*
                          (0..1 Reference(Device | DeviceMetric), columns)
      identifier       -> ObservationIdentifier (0..*)
      category, code, method, data-absent-reason, value-concept, component-code,
      component-data-absent-reason, component-value-concept
                       -> ObservationToken (one shared table, one row per coding of each
                          concept, told apart by `param`; `slot` says which element — the
                          Observation (0) or its n-th component — a row came from)
      value-quantity, component-value-quantity, value-string, value-date
                       -> ObservationValue (one row per value occurrence, by `param` and `slot`)
      based-on, part-of, focus, has-member, derived-from, performer
                       -> ObservationReference (one shared table, one row per Reference)
      combo-code, combo-value-concept, combo-data-absent-reason, combo-value-quantity
                       -> the union of an Observation-level and a component-level parameter
                          above (no storage of their own)
      the 8 composite parameters (`code-value-quantity`, `component-code-value-concept`, ...)
                       -> a token row and a value/token row *with the same slot*
      _id              -> observation_id;  _lastUpdated -> updated_at/created_at

    `issued`, `interpretation`, `note`, `bodySite`, `referenceRange`, every value[x] choice no
    parameter reads (boolean, integer, Range, Ratio, SampledData, time), `effective[x]` beyond
    its date range and `extension` have no search parameter and live only in `content`.

    `subject`, `device`, `based-on`, `part-of`, `focus`, `has-member`, `derived-from` and `performer`
    can point at several resource types, so `reference_type` records which one a relative
    `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is ambiguous for
    them (`subject=Type/id` or `subject:Type=id`; `patient`, `encounter` and `specimen` have one
    target so a bare id works).

    All index columns are nullable: R4 makes `status` and `code` mandatory, but that is the
    validator's rule (enforced by the `java_validator` backend), not the database's. No `user_id`:
    an Observation is a shared tenant-level entity. No DB-level CHECK constraints (rules obs-3,
    obs-6 and obs-7 are the validator's job)."""

    __tablename__ = "observation"
    __table_args__ = (
        Index("ix_observation_date", "date_start", "date_end"),
        # Observations are searched by patient far more than by anything else.
        Index("ix_observation_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    observation_id = Column(
        BigInteger,
        observation_id_seq,
        server_default=observation_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            ObservationStatus,
            name="observation_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )

    # date: the half-open [start, end) range of instants effective[x] covers.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    # subject (0..1 Reference(Patient | Group | Device | Location))
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

    # specimen (0..1 Reference(Specimen))
    specimen_reference = Column(String, nullable=True)
    specimen_type = Column(String, nullable=True)
    specimen_id = Column(BigInteger, nullable=True, index=True)
    specimen_identifier_system = Column(String, nullable=True)
    specimen_identifier_value = Column(String, nullable=True)

    # device (0..1 Reference(Device | DeviceMetric))
    device_reference = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    device_id = Column(BigInteger, nullable=True, index=True)
    device_identifier_system = Column(String, nullable=True)
    device_identifier_value = Column(String, nullable=True)

    identifiers = relationship("ObservationIdentifier", back_populates="observation", cascade="all, delete-orphan")
    tokens = relationship("ObservationToken", back_populates="observation", cascade="all, delete-orphan")
    values = relationship("ObservationValue", back_populates="observation", cascade="all, delete-orphan")
    references = relationship("ObservationReference", back_populates="observation", cascade="all, delete-orphan")

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ImmunizationStatus

immunization_id_seq = Sequence("immunization_pub_seq", start=330000, increment=1, metadata=Base.metadata)


class ImmunizationModel(TenantAuditMixin, Base):
    """FHIR R4 Immunization — Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure, DiagnosticReport and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.immunization). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Immunization search parameter filters on it
    (https://www.hl7.org/fhir/R4/immunization.html#search), and is derived from
    `content` on every write by app.repository.immunization._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so
                          `entered-in-error` / `not-done` are the real FHIR codes)
      date             -> occurrence_date_start/_end (occurrence[x] as a dateTime,
                          columns; the half-open range it covers — a string
                          occurrence is not a date and is not indexed)
      lot-number       -> lot_number + lot_number_norm (0..1 string, columns)
      patient          -> patient_reference/_type/_id + patient_identifier_*
                          (1..1 Reference(Patient), columns)
      location         -> location_reference/_type/_id + location_identifier_*
                          (0..1 Reference(Location), columns)
      manufacturer     -> manufacturer_reference/_type/_id + manufacturer_identifier_*
                          (0..1 Reference(Organization), columns)
      identifier       -> ImmunizationIdentifier (0..*)
      reason-code, status-reason, target-disease, vaccine-code
                       -> ImmunizationToken (0..*, one shared table;
                          `target-disease` reads protocolApplied.targetDisease)
      series           -> ImmunizationProtocol (one row per protocolApplied with a series)
      performer        -> ImmunizationPerformer (one row per performer.actor)
      reaction, reaction-date
                       -> ImmunizationReaction (one row per reaction: the `detail`
                          reference plus `date` as a range)
      reason-reference -> ImmunizationReasonReference (one row per Reference)
      _id              -> immunization_id;  _lastUpdated -> updated_at/created_at

    `encounter`, `recorded`, `primarySource`, `reportOrigin`, `expirationDate`, `site`,
    `route`, `doseQuantity`, `performer.function`, `note`, `isSubpotent`,
    `subpotentReason`, `education`, `programEligibility`, `fundingSource`,
    `reaction.reported`, `protocolApplied` apart from `series`/`targetDisease`,
    `occurrenceString` and `extension` have no search parameter and live only in
    `content`.

    `performer` and `reason-reference` can point at several resource types, so
    `reference_type` records which one a relative `Type/<id>` names (a plain string,
    not a Postgres enum): a search by bare id is ambiguous (`performer=Type/id` or
    `performer:Type=id`; `patient`, `location`, `manufacturer` and `reaction` have
    one target so a bare id works).

    All index columns are nullable: R4 makes `status`, `vaccineCode`, `patient` and
    `occurrence[x]` mandatory, but that is the validator's rule (enforced by the
    `java_validator` backend), not the database's. No `user_id`: an Immunization
    is a shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "immunization"
    __table_args__ = (Index("ix_immunization_occurrence_date", "occurrence_date_start", "occurrence_date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_id = Column(
        BigInteger,
        immunization_id_seq,
        server_default=immunization_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            ImmunizationStatus,
            name="immunization_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # occurrence[x] as a dateTime: the half-open [start, end) range of instants it
    # covers (NULL = absent), matched with period_match.
    occurrence_date_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_date_end = Column(DateTime(timezone=True), nullable=True)

    lot_number = Column(String, nullable=True)
    lot_number_norm = Column(String, nullable=True, index=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    # location (0..1 Reference(Location))
    location_reference = Column(String, nullable=True)
    location_type = Column(String, nullable=True)
    location_id = Column(BigInteger, nullable=True, index=True)
    location_identifier_system = Column(String, nullable=True)
    location_identifier_value = Column(String, nullable=True)

    # manufacturer (0..1 Reference(Organization))
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(String, nullable=True)
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)

    identifiers = relationship("ImmunizationIdentifier", back_populates="immunization", cascade="all, delete-orphan")
    tokens = relationship("ImmunizationToken", back_populates="immunization", cascade="all, delete-orphan")
    protocols = relationship("ImmunizationProtocol", back_populates="immunization", cascade="all, delete-orphan")
    reactions = relationship("ImmunizationReaction", back_populates="immunization", cascade="all, delete-orphan")
    performers = relationship("ImmunizationPerformer", back_populates="immunization", cascade="all, delete-orphan")
    reason_references = relationship(
        "ImmunizationReasonReference", back_populates="immunization", cascade="all, delete-orphan"
    )

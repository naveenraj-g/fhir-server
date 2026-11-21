from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ProcedureStatus

procedure_id_seq = Sequence(
    "procedure_pub_seq", start=100000, increment=1, metadata=Base.metadata
)

# R4 targets of Procedure.subject, and of Procedure.recorder / .asserter.
SUBJECT_TYPES = ("Patient", "Group")
ACTOR_TYPES = ("Patient", "RelatedPerson", "Practitioner", "PractitionerRole")


class ProcedureModel(TenantAuditMixin, Base):
    """FHIR R4 Procedure — Medplum-style storage, same as Patient, Encounter,
    Condition and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.procedure). Nothing else in this table or its child tables
    is a second copy of the resource: every other column exists only because a
    FHIR R4 Procedure search parameter filters on it
    (https://www.hl7.org/fhir/R4/procedure.html#search), and is derived from
    `content` on every write by app.repository.procedure._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so
                          `in-progress` / `not-done` are the real FHIR codes)
      date             -> performed_date_start/_end (performed[x] as a dateTime or
                          a Period, columns; the half-open range covered,
                          NULL = open)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (1..1 Reference(Patient | Group), columns; `patient` is
                          the same columns narrowed to Patient)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
                          (0..1 Reference(Encounter), columns)
      location         -> location_reference/_type/_id + location_identifier_*
                          (0..1 Reference(Location), columns)
      identifier       -> ProcedureIdentifier (0..*)
      category, code, reason-code
                       -> ProcedureToken (0..*, one shared table)
      based-on, instantiates-canonical, part-of, reason-reference
                       -> ProcedureReference (0..*, one shared table)
      performer        -> ProcedurePerformer (one row per performer.actor)
      instantiates-uri -> ProcedureInstantiatesUri (one row per URI)
      _id              -> procedure_id;  _lastUpdated -> updated_at/created_at

    `statusReason`, `outcome`, `recorder`, `asserter`, `performed[x]` other than
    dateTime / Period, `performer.function` / `.onBehalfOf`, `bodySite`, `report`,
    `complication`, `complicationDetail`, `followUp`, `note`, `focalDevice`,
    `usedReference`, `usedCode` and `extension` have no search parameter and live
    only in `content`.

    `subject`, `performer` and the reference-table parameters can point at
    several resource types, so `*_type` records which one a relative `Type/<id>`
    names (a plain string, not a Postgres enum): a search by bare id is ambiguous
    (`subject=Type/id` or `subject:Type=id`; `patient`, `encounter` and
    `location` have one target so a bare id works).

    All index columns are nullable: R4 makes `status` and `subject` mandatory, but
    that is the validator's rule (enforced by the `java_validator` backend), not
    the database's. No `user_id`: a Procedure is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "procedure"
    __table_args__ = (
        Index(
            "ix_procedure_performed_date", "performed_date_start", "performed_date_end"
        ),
        Index("ix_procedure_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    procedure_id = Column(
        BigInteger,
        procedure_id_seq,
        server_default=procedure_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            ProcedureStatus,
            name="procedure_status",
            # Store `in-progress`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # performed[x] as a dateTime or a Period: the half-open [start, end) range of
    # instants it covers (NULL = open / absent), matched with period_match.
    performed_date_start = Column(DateTime(timezone=True), nullable=True)
    performed_date_end = Column(DateTime(timezone=True), nullable=True)

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

    # location (0..1 Reference(Location))
    location_reference = Column(String, nullable=True)
    location_type = Column(String, nullable=True)
    location_id = Column(BigInteger, nullable=True, index=True)
    location_identifier_system = Column(String, nullable=True)
    location_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "ProcedureIdentifier", back_populates="procedure", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "ProcedureToken", back_populates="procedure", cascade="all, delete-orphan"
    )
    references = relationship(
        "ProcedureReference", back_populates="procedure", cascade="all, delete-orphan"
    )
    performers = relationship(
        "ProcedurePerformer", back_populates="procedure", cascade="all, delete-orphan"
    )
    instantiates_uris = relationship(
        "ProcedureInstantiatesUri",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )

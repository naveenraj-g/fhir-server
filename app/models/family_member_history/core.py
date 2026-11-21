from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import FamilyMemberHistoryStatus

family_member_history_id_seq = Sequence(
    "family_member_history_pub_seq", start=490000, increment=1, metadata=Base.metadata
)


class FamilyMemberHistoryModel(TenantAuditMixin, Base):
    """FHIR R4 FamilyMemberHistory — Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure, DiagnosticReport, Immunization and the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at
    read time from this row's own columns — see app.fhir.mappers.family_member_history).
    Nothing else in this table or its child tables is a second copy of the resource: every
    other column exists only because a FHIR R4 FamilyMemberHistory search parameter filters
    on it (https://www.hl7.org/fhir/R4/familymemberhistory.html#search), and is derived from
    `content` on every write by app.repository.family_member_history._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so
                          `entered-in-error` / `health-unknown` are the real FHIR codes)
      date             -> date_start/_end (the 0..1 dateTime, as the half-open range it
                          covers at its written precision; columns)
      patient          -> patient_reference/_type/_id + patient_identifier_*
                          (1..1 Reference(Patient), columns)
      identifier       -> FamilyMemberHistoryIdentifier (0..*)
      code, relationship, sex
                       -> FamilyMemberHistoryToken (one shared table, one row per coding of
                          each concept; `code` reads condition.code across every condition)
      instantiates-canonical
                       -> FamilyMemberHistoryReference (one row per canonical URL)
      instantiates-uri -> FamilyMemberHistoryInstantiatesUri (one row per URI)
      _id              -> family_member_history_id;  _lastUpdated -> updated_at/created_at

    `dataAbsentReason`, `name`, `born[x]`, `age[x]`, `estimatedAge`, `deceased[x]`,
    `reasonCode`, `reasonReference`, `note`, every condition element except `code`
    (`outcome`, `contributedToDeath`, `onset[x]`, `note`) and `extension` have no search
    parameter and live only in `content`.

    All index columns are nullable: R4 makes `status`, `patient` and `relationship`
    mandatory, but that is the validator's rule (enforced by the `java_validator` backend),
    not the database's. No `user_id`: a FamilyMemberHistory is a shared tenant-level entity.
    No DB-level CHECK constraints (rules fhs-1 / fhs-2 are the validator's job)."""

    __tablename__ = "family_member_history"
    __table_args__ = (Index("ix_family_member_history_date", "date_start", "date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    family_member_history_id = Column(
        BigInteger,
        family_member_history_id_seq,
        server_default=family_member_history_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            FamilyMemberHistoryStatus,
            name="family_member_history_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # date: the half-open [start, end) range of instants the dateTime covers.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "FamilyMemberHistoryIdentifier",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "FamilyMemberHistoryToken",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "FamilyMemberHistoryReference",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    instantiates_uris = relationship(
        "FamilyMemberHistoryInstantiatesUri",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )

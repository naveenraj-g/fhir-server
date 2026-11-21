from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ImmunizationEvaluationStatus

immunization_evaluation_id_seq = Sequence(
    "immunization_evaluation_pub_seq", start=610000, increment=1, metadata=Base.metadata
)


class ImmunizationEvaluationModel(TenantAuditMixin, Base):
    """FHIR R4 ImmunizationEvaluation — Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure, DiagnosticReport, Immunization and the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at
    read time from this row's own columns — see app.fhir.mappers.immunization_evaluation).
    Nothing else in this table or its child tables is a second copy of the resource: every
    other column exists only because a FHIR R4 ImmunizationEvaluation search parameter
    filters on it (https://www.hl7.org/fhir/R4/immunizationevaluation.html#search), and is
    derived from `content` on every write by
    app.repository.immunization_evaluation._indexer.

    Search parameter -> storage:
      status           -> status (1..1 code, Enum column, stored by value so
                          `entered-in-error` is the real FHIR code)
      date             -> date_start/_end (the 0..1 dateTime, as the half-open range it
                          covers at its written precision; columns)
      patient          -> patient_reference/_type/_id + patient_identifier_*
                          (1..1 Reference(Patient), columns)
      immunization-event -> immunization_event_reference/_type/_id + immunization_event_identifier_*
                          (1..1 Reference(Immunization), columns)
      identifier       -> ImmunizationEvaluationIdentifier (0..*)
      dose-status, target-disease
                       -> ImmunizationEvaluationToken (one shared table, one row per
                          coding of each concept)
      _id              -> immunization_evaluation_id;  _lastUpdated -> updated_at/created_at

    `authority`, `doseStatusReason`, `description`, `series`, `doseNumber[x]`,
    `seriesDoses[x]` and `extension` have no search parameter and live only in `content`.

    All index columns are nullable: R4 makes `status`, `patient`, `targetDisease`,
    `immunizationEvent` and `doseStatus` mandatory, but that is the validator's rule
    (enforced by the `java_validator` backend), not the database's. No `user_id`: an
    ImmunizationEvaluation is a shared tenant-level entity. No DB-level CHECK constraints
    (the old dose-number / series-doses choice checks are the validator's job)."""

    __tablename__ = "immunization_evaluation"
    __table_args__ = (
        Index("ix_immunization_evaluation_date", "date_start", "date_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_evaluation_id = Column(
        BigInteger,
        immunization_evaluation_id_seq,
        server_default=immunization_evaluation_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    status = Column(
        Enum(
            ImmunizationEvaluationStatus,
            name="immunization_evaluation_status",
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

    # immunizationEvent (1..1 Reference(Immunization))
    immunization_event_reference = Column(String, nullable=True)
    immunization_event_type = Column(String, nullable=True)
    immunization_event_id = Column(BigInteger, nullable=True, index=True)
    immunization_event_identifier_system = Column(String, nullable=True)
    immunization_event_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "ImmunizationEvaluationIdentifier",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "ImmunizationEvaluationToken",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
    )

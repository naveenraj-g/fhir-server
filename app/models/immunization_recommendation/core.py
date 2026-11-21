from sqlalchemy import BigInteger, Column, DateTime, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

immunization_recommendation_id_seq = Sequence(
    "immunization_recommendation_pub_seq", start=510000, increment=1, metadata=Base.metadata
)


class ImmunizationRecommendationModel(TenantAuditMixin, Base):
    """FHIR R4 ImmunizationRecommendation — Medplum-style storage, same as Patient,
    Encounter, Condition, Procedure, DiagnosticReport, Immunization and the other
    content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.immunization_recommendation). Nothing else in this table or
    its child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 ImmunizationRecommendation search parameter filters on
    it (https://www.hl7.org/fhir/R4/immunizationrecommendation.html#search), and is
    derived from `content` on every write by
    app.repository.immunization_recommendation._indexer.

    Search parameter -> storage:
      date             -> date_start/_end (the 1..1 dateTime, as the half-open range
                          it covers at its written precision; columns)
      patient          -> patient_reference/_type/_id + patient_identifier_*
                          (1..1 Reference(Patient), columns)
      identifier       -> ImmunizationRecommendationIdentifier (0..*)
      status, target-disease, vaccine-type
                       -> ImmunizationRecommendationToken (one shared table, one row
                          per coding of each concept; `status` reads
                          recommendation.forecastStatus, `target-disease` reads
                          recommendation.targetDisease, `vaccine-type` reads
                          recommendation.vaccineCode)
      support, information
                       -> ImmunizationRecommendationReference (one shared table, one
                          row per Reference; `support` reads
                          recommendation.supportingImmunization,
                          `information` reads recommendation.supportingPatientInformation)
      _id              -> immunization_recommendation_id;  _lastUpdated -> updated_at/created_at

    `authority`, `recommendation.contraindicatedVaccineCode`, `.forecastReason`,
    `.dateCriterion`, `.description`, `.series`, `.doseNumber[x]`, `.seriesDoses[x]`
    and `extension` have no search parameter and live only in `content`.

    `support` (Immunization | ImmunizationEvaluation) and `information` (Reference(Any))
    can point at several resource types, so `reference_type` records which one a
    relative `Type/<id>` names (a plain string, not a Postgres enum): a search by bare
    id is ambiguous (`support=Type/id` or `support:Type=id`).

    All index columns are nullable: R4 makes `patient`, `date` and `recommendation`
    mandatory, but that is the validator's rule (enforced by the `java_validator`
    backend), not the database's. No `user_id`: an ImmunizationRecommendation is a
    shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "immunization_recommendation"
    __table_args__ = (Index("ix_immunization_recommendation_date", "date_start", "date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_recommendation_id = Column(
        BigInteger,
        immunization_recommendation_id_seq,
        server_default=immunization_recommendation_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
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
        "ImmunizationRecommendationIdentifier", back_populates="immunization_recommendation", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "ImmunizationRecommendationToken", back_populates="immunization_recommendation", cascade="all, delete-orphan"
    )
    references = relationship(
        "ImmunizationRecommendationReference", back_populates="immunization_recommendation", cascade="all, delete-orphan"
    )

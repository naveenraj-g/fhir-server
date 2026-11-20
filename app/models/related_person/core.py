from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender

related_person_id_seq = Sequence("related_person_pub_seq", start=300000, increment=1, metadata=Base.metadata)


class RelatedPersonModel(TenantAuditMixin, Base):
    """FHIR R4 RelatedPerson — Medplum-style storage, same as Patient,
    Appointment and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it
    is the single source of truth, and GET serves it back as-is (`id`/`meta` are
    stamped on at read time from this row's own columns — see
    app.fhir.mappers.related_person). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 RelatedPerson search parameter filters on it
    (https://www.hl7.org/fhir/R4/relatedperson.html#search), and is derived from
    `content` on every write by app.repository.related_person._indexer.

    Search parameter -> storage:
      active           -> active (0..1, column)
      gender           -> gender (0..1, column)
      birthdate        -> birth_date_start/_end (0..1, columns; the half-open
                          range the date covers, so a partial date like
                          `1990-05` works — see period_bounds)
      patient          -> patient_reference/_type/_id +
                          patient_identifier_system/_value (1..1 reference,
                          columns)
      name, phonetic   -> RelatedPersonName (0..*, one row per HumanName)
      identifier       -> RelatedPersonIdentifier (0..*)
      telecom, phone,
      email            -> RelatedPersonTelecom (0..*)
      address, address-*
                       -> RelatedPersonAddress (0..*)
      relationship     -> RelatedPersonRelationship (0..*, one row per coding)
      _id              -> related_person_id;  _lastUpdated -> updated_at/created_at

    `photo`, `period` and `communication` have no search parameter and live only
    in `content`.

    String parameters are stored twice: as written (for `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) — for
    R4's default case/accent-insensitive starts-with match and `:contains`.

    All index columns are nullable: R4 makes `patient` mandatory, but that is the
    validator's rule (enforced by the `java_validator` backend), not the
    database's. No `user_id`: a RelatedPerson is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "related_person"
    __table_args__ = (Index("ix_related_person_birth_date", "birth_date_start", "birth_date_end"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    related_person_id = Column(
        BigInteger,
        related_person_id_seq,
        server_default=related_person_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # ── Search index (derived from `content`) ─────────────────────────────
    active = Column(Boolean, nullable=True)
    gender = Column(Enum(AdministrativeGender, name="administrative_gender", create_type=False), nullable=True)

    # birthDate is a FHIR date that may be partial (`1990`, `1990-05`): held as
    # the half-open [start, end) range of instants it covers (NULL = absent),
    # matched with period_match.
    birth_date_start = Column(DateTime(timezone=True), nullable=True)
    birth_date_end = Column(DateTime(timezone=True), nullable=True)

    # RelatedPerson.patient — Reference(Patient); `patient_type` is a plain string.
    patient_reference = Column(String, nullable=True)
    patient_type = Column(String, nullable=True)
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)

    identifiers = relationship("RelatedPersonIdentifier", back_populates="related_person", cascade="all, delete-orphan")
    names = relationship("RelatedPersonName", back_populates="related_person", cascade="all, delete-orphan")
    telecoms = relationship("RelatedPersonTelecom", back_populates="related_person", cascade="all, delete-orphan")
    addresses = relationship("RelatedPersonAddress", back_populates="related_person", cascade="all, delete-orphan")
    relationships = relationship(
        "RelatedPersonRelationship", back_populates="related_person", cascade="all, delete-orphan"
    )

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Index,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender

patient_id_seq = Sequence(
    "patient_pub_seq", start=10000, increment=1, metadata=Base.metadata
)


class PatientModel(TenantAuditMixin, Base):
    """FHIR R4 Patient — Medplum-style storage, same as Practitioner and
    the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write;
    it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.patient). Nothing else in this table or its child
    tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Patient search parameter filters on it
    (https://www.hl7.org/fhir/R4/patient.html#search), and is derived from
    `content` on every write by app.repository.patient._indexer.

    Search parameter -> storage:
      active              -> active (0..1, column)
      gender              -> gender (0..1, column)
      birthdate           -> birth_date_start/_end (0..1, columns; the
                             half-open range the date covers, so a partial
                             date like `1990-05` works — see period_bounds)
      death-date          -> death_date_start/_end (same, from deceasedDateTime)
      deceased            -> deceased (0..1 column): true when deceased[x] is
                             present and not false, false for deceasedBoolean
                             false, NULL when absent
      organization        -> managing_organization_reference/_type/_id +
                             managing_organization_identifier_system/_value
                             (0..1, columns)
      name, family,
      given, phonetic     -> PatientName (0..*, one row per HumanName)
      identifier          -> PatientIdentifier (0..*)
      telecom, phone,
      email               -> PatientTelecom (0..*)
      address, address-*  -> PatientAddress (0..*)
      language            -> PatientCommunication (0..*, one row per coding of
                             communication.language)
      general-practitioner,
      link                -> PatientReference (0..*, told apart by `param`)
      _id                 -> patient_id;  _lastUpdated -> updated_at/created_at

    `user_id` is not a FHIR element and not a search parameter: it links the
    record to the IAM user who is this patient (a patient portal user) and
    scopes the `/me` route. It is never in `content` and is never a body field —
    it is set by the permission-gated `PUT/DELETE /patients/{id}/user`, or on
    create when the caller explicitly asks to link themselves (self-signup).

    String parameters are stored twice: as written (for `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) —
    for R4's default case/accent-insensitive starts-with match and
    `:contains`.

    No DB-level CHECK constraints — every R4 rule is enforced by the FHIR
    validator before anything is written."""

    __tablename__ = "patient"
    __table_args__ = (
        Index("ix_patient_birth_date", "birth_date_start", "birth_date_end"),
        Index("ix_patient_death_date", "death_date_start", "death_date_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    patient_id = Column(
        BigInteger,
        patient_id_seq,
        server_default=patient_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # The IAM user linked to this record (see the docstring); NULL = unlinked.
    user_id = Column(String, nullable=True, index=True)

    # ── Search index (derived from `content`) ─────────────────────────────
    # active (0..1) — R4 removed the R3 default of true; absent means
    # unknown, not false.
    active = Column(Boolean, nullable=True)
    gender = Column(
        Enum(AdministrativeGender, name="administrative_gender"), nullable=True
    )

    # birthDate / deceasedDateTime are FHIR dates that may be partial
    # (`1990`, `1990-05`): each is held as the half-open [start, end) range of
    # instants it covers (NULL = absent), matched with period_match.
    birth_date_start = Column(DateTime(timezone=True), nullable=True)
    birth_date_end = Column(DateTime(timezone=True), nullable=True)
    death_date_start = Column(DateTime(timezone=True), nullable=True)
    death_date_end = Column(DateTime(timezone=True), nullable=True)
    deceased = Column(Boolean, nullable=True)

    # managingOrganization (0..1 Reference(Organization)) -> `organization`.
    managing_organization_reference = Column(String, nullable=True)
    managing_organization_type = Column(String, nullable=True)
    managing_organization_id = Column(BigInteger, nullable=True, index=True)
    managing_organization_identifier_system = Column(String, nullable=True)
    managing_organization_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "PatientIdentifier", back_populates="patient", cascade="all, delete-orphan"
    )
    names = relationship(
        "PatientName", back_populates="patient", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PatientTelecom", back_populates="patient", cascade="all, delete-orphan"
    )
    addresses = relationship(
        "PatientAddress", back_populates="patient", cascade="all, delete-orphan"
    )
    communications = relationship(
        "PatientCommunication", back_populates="patient", cascade="all, delete-orphan"
    )
    references = relationship(
        "PatientReference", back_populates="patient", cascade="all, delete-orphan"
    )

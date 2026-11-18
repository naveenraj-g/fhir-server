from sqlalchemy import BigInteger, Boolean, Column, Enum, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender

practitioner_id_seq = Sequence(
    "practitioner_pub_seq", start=30000, increment=1, metadata=Base.metadata
)


class PractitionerModel(TenantAuditMixin, Base):
    """FHIR R4 Practitioner — Medplum-style storage, same as Organization
    and Location.

    `content` (JSONB) holds the whole resource exactly as validated on
    write; it is the single source of truth, and GET serves it back as-is
    (`id`/`meta` are stamped on at read time from this row's own columns —
    see app.fhir.mappers.practitioner). Nothing else in this table or its
    child tables is a second copy of the resource: every other column exists
    only because a FHIR R4 Practitioner search parameter filters on it
    (https://www.hl7.org/fhir/R4/practitioner.html#search), and is derived
    from `content` on every write by app.repository.practitioner._indexer.

    Search parameter -> storage:
      active             -> active (0..1, column)
      gender             -> gender (0..1, column)
      name, family,
      given, phonetic    -> PractitionerName (0..*, one row per HumanName)
      identifier         -> PractitionerIdentifier (0..*)
      telecom, phone,
      email              -> PractitionerTelecom (0..*)
      address, address-* -> PractitionerAddress (0..*)
      communication      -> PractitionerCommunication (0..*, one row per coding)
      _id                -> practitioner_id;  _lastUpdated -> updated_at/created_at

    `user_id` is not a FHIR element and not a search parameter: it links the
    record to the IAM user who acts as this practitioner and scopes the
    `/me` route. It is never in `content` and never set by create/patch —
    only by the permission-gated `PUT/DELETE /practitioners/{id}/user`
    (the equivalent of Medplum ProjectMembership.profile, kept on the row
    instead of a separate membership record).

    String parameters are stored twice: as written (for `:exact`) and
    normalized — accents stripped, case-folded (app.fhir.search.normalize) —
    for R4's default case/accent-insensitive starts-with match and
    `:contains`.

    No DB-level CHECK constraints — every R4 rule is enforced by the FHIR
    validator before anything is written."""

    __tablename__ = "practitioner"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    practitioner_id = Column(
        BigInteger,
        practitioner_id_seq,
        server_default=practitioner_id_seq.next_value(),
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

    identifiers = relationship(
        "PractitionerIdentifier",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "PractitionerName", back_populates="practitioner", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PractitionerTelecom",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "PractitionerAddress",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "PractitionerCommunication",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )

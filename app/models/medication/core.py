from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MedicationStatus

medication_id_seq = Sequence(
    "medication_pub_seq", start=250000, increment=1, metadata=Base.metadata
)

# R4 target of Medication.manufacturer.
MANUFACTURER_TYPES = ("Organization",)


class MedicationModel(TenantAuditMixin, Base):
    """FHIR R4 Medication - Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, ServiceRequest and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at
    read time from this row's own columns - see app.fhir.mappers.medication). Nothing else
    in this table or its child tables is a second copy of the resource: every other column
    exists only because a FHIR R4 Medication search parameter filters on it
    (https://www.hl7.org/fhir/R4/medication.html#search), and is derived from `content` on
    every write by app.repository.medication._indexer.

    Search parameter -> storage:
      status           -> status (0..1 code, Enum column, stored by value so
                          `entered-in-error` is the real FHIR code)
      expiration-date  -> expiration_start/_end (batch.expirationDate, the range the dateTime
                          covers, columns)
      lot-number       -> lot_number (batch.lotNumber, 0..1 string searched as a token, column)
      manufacturer     -> manufacturer_reference/_type/_id + manufacturer_identifier_*
                          (0..1 Reference(Organization), columns)
      identifier       -> MedicationIdentifier (0..*)
      code, form, ingredient-code
                       -> MedicationToken (one shared table; `ingredient-code` reads
                          ingredient.itemCodeableConcept of *every* ingredient)
      ingredient       -> MedicationReference (one row per ingredient.itemReference, a
                          Reference(Substance | Medication))
      _id              -> medication_id;  _lastUpdated -> updated_at/created_at

    `amount`, `ingredient.isActive`, `ingredient.strength` and `extension` have no search
    parameter and live only in `content`.

    `ingredient` can point at two resource types, so `reference_type` records which one a
    relative `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is
    ambiguous (`ingredient=Type/id` or `ingredient:Type=id`; `manufacturer` has one target so
    a bare id works).

    All index columns are nullable (every Medication element is optional in R4). No
    `user_id`: a Medication is a shared tenant-level entity. No DB-level CHECK constraints."""

    __tablename__ = "medication"
    __table_args__ = (
        Index("ix_medication_expiration", "expiration_start", "expiration_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_id = Column(
        BigInteger,
        medication_id_seq,
        server_default=medication_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MedicationStatus,
            name="medication_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # batch.expirationDate: the half-open [start, end) range of instants the dateTime covers
    # (NULL = absent), matched with period_match.
    expiration_start = Column(DateTime(timezone=True), nullable=True)
    expiration_end = Column(DateTime(timezone=True), nullable=True)

    # batch.lotNumber (0..1 string, searched as a token)
    lot_number = Column(String, nullable=True, index=True)

    # manufacturer (0..1 Reference(Organization))
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(String, nullable=True)
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MedicationIdentifier",
        back_populates="medication",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "MedicationToken", back_populates="medication", cascade="all, delete-orphan"
    )
    references = relationship(
        "MedicationReference",
        back_populates="medication",
        cascade="all, delete-orphan",
    )

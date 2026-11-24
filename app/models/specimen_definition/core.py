from sqlalchemy import BigInteger, Column, Sequence
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

specimen_definition_id_seq = Sequence(
    "specimen_definition_pub_seq", start=550000, increment=1, metadata=Base.metadata
)


class SpecimenDefinitionModel(TenantAuditMixin, Base):
    """FHIR R4 SpecimenDefinition - stored whole in `content`, like the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.specimen_definition). Every other table exists
    only because a FHIR R4 SpecimenDefinition search parameter filters on it
    (https://www.hl7.org/fhir/R4/specimendefinition.html#search) and is derived from `content`
    on every write by app.repository.specimen_definition._indexer.

    Search parameter -> storage (R4 defines exactly three, all tokens):
      identifier -> SpecimenDefinitionIdentifier (0..1 Identifier, one row per type coding)
      type       -> SpecimenDefinitionToken (`typeCollected`, one row per coding)
      container  -> SpecimenDefinitionToken (`typeTested.container.type` of every typeTested
                    entry, one row per coding)
      _id        -> specimen_definition_id;  _lastUpdated -> updated_at/created_at

    Everything else - `patientPreparation`, `timeAspect`, `collection`, the rest of `typeTested`
    (`isDerived`, `type`, `preference`, the container's other elements, `requirement`,
    `retentionTime`, `rejectionCriterion`, `handling`) and `extension` - lives only in `content`.
    R4's `typeTested.preference` (a required binding) is not read by any search parameter, so it
    is not an enum column.

    No `user_id`: a SpecimenDefinition is a shared tenant-level entity. No DB-level CHECK
    constraints (R4 rules - e.g. spd-1 - are the validator's)."""

    __tablename__ = "specimen_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    specimen_definition_id = Column(
        BigInteger,
        specimen_definition_id_seq,
        server_default=specimen_definition_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    identifiers = relationship(
        "SpecimenDefinitionIdentifier",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "SpecimenDefinitionToken",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )

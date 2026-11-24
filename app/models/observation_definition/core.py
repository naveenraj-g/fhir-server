from sqlalchemy import BigInteger, Column, Sequence
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

observation_definition_id_seq = Sequence(
    "observation_definition_pub_seq", start=400000, increment=1, metadata=Base.metadata
)


class ObservationDefinitionModel(TenantAuditMixin, Base):
    """FHIR R4 ObservationDefinition - stored whole in `content`, like the other content-based
    resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.observation_definition).

    **R4 defines no search parameter for ObservationDefinition** (its resource page has no
    Search Parameters section; only the common `_id` and `_lastUpdated` apply, and they read the
    public id and the audit timestamps), so there is nothing to index: no column besides the
    ones below and no child table. Every element - `identifier`, `category`, `code`,
    `permittedDataType`, `multipleResultsAllowed`, `method`, `preferredReportName`,
    `quantitativeDetails`, `qualifiedInterval`, the four `*CodedValueSet` references and
    `extension` - lives only in `content`. Should a later R4 point release add a search
    parameter, add its column / table, populate it in the indexer and backfill it from `content`.

    No `user_id`: an ObservationDefinition is a shared tenant-level entity. No DB-level CHECK
    constraints (R4 rules - e.g. obd-1 - are the validator's)."""

    __tablename__ = "observation_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    observation_definition_id = Column(
        BigInteger,
        observation_definition_id_seq,
        server_default=observation_definition_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

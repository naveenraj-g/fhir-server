from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import PlanDefinitionStatus

plan_definition_id_seq = Sequence(
    "plan_definition_pub_seq", start=420000, increment=1, metadata=Base.metadata
)


class PlanDefinitionModel(TenantAuditMixin, Base):
    """FHIR R4 PlanDefinition - stored whole in `content`, like Questionnaire, CarePlan and
    the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the single
    source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read time from
    this row's own columns - see app.fhir.mappers.plan_definition). Nothing else in this
    table or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 PlanDefinition search parameter filters on it
    (https://www.hl7.org/fhir/R4/plandefinition.html#search), and is derived from `content`
    on every write by app.repository.plan_definition._indexer.

    Search parameter -> storage:
      url                   -> url (0..1 uri, column; exact, `:below` / `:above`)
      version               -> version (0..1 string read as a token: the code only, exact)
      name, title,
      description,
      publisher             -> name/name_norm, title/title_norm, description/description_norm,
                               publisher/publisher_norm (0..1 strings, columns; each stored as
                               written and normalized)
      status                -> status (Enum column, required binding)
      date                  -> date_start/_end (0..1 dateTime, the half-open range it covers at
                               its written precision)
      effective             -> effective_start/_end (0..1 Period, half-open range; NULL = open)
      identifier            -> PlanDefinitionIdentifier (one row per identifier x type coding)
      jurisdiction, topic,
      type, context-type,
      context               -> PlanDefinitionToken (one row per coding, told apart by `param`;
                               `context-type` / `context` carry the useContext's slot)
      composed-of, depends-on,
      derived-from,
      predecessor,
      successor, definition -> PlanDefinitionReference (one row per canonical URL: each
                               relatedArtifact.resource of that type, each `library` (also
                               `depends-on`), and each action's `definitionCanonical` at every
                               depth - `definition`)
      context-quantity      -> PlanDefinitionContextQuantity (one row per useContext whose
                               value is a Quantity or a Range)
      context-type-value,
      context-type-quantity -> composites over the useContext rows above (same slot)
      _id                   -> plan_definition_id;  _lastUpdated -> updated_at/created_at

    Everything else - `subtitle`, `experimental`, `subject[x]`, `contact`, `purpose`, `usage`,
    `copyright`, `approvalDate`, `lastReviewDate`, `author` / `editor` / `reviewer` / `endorser`,
    the `relatedArtifact` entries themselves, `library`, `goal`, the whole `action` tree
    (everything but `definitionCanonical`) and `extension` - lives only in `content`.

    All index columns are nullable. No `user_id`: a PlanDefinition is a shared tenant-level
    entity. No DB-level CHECK constraints (R4 rules - e.g. pld-0 - are the validator's)."""

    __tablename__ = "plan_definition"
    __table_args__ = (
        Index("ix_plan_definition_date", "date_start", "date_end"),
        Index("ix_plan_definition_effective", "effective_start", "effective_end"),
        Index("ix_plan_definition_name_norm", "name_norm"),
        Index("ix_plan_definition_title_norm", "title_norm"),
        Index("ix_plan_definition_url", "url"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    plan_definition_id = Column(
        BigInteger,
        plan_definition_id_seq,
        server_default=plan_definition_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            PlanDefinitionStatus,
            name="plan_definition_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
        index=True,
    )
    url = Column(String, nullable=True)
    version = Column(String, nullable=True)
    name = Column(String, nullable=True)
    name_norm = Column(String, nullable=True)
    title = Column(String, nullable=True)
    title_norm = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_norm = Column(Text, nullable=True)
    publisher = Column(String, nullable=True)
    publisher_norm = Column(String, nullable=True)

    # date (0..1 dateTime) and effectivePeriod: half-open [start, end) ranges.
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)
    effective_start = Column(DateTime(timezone=True), nullable=True)
    effective_end = Column(DateTime(timezone=True), nullable=True)

    identifiers = relationship(
        "PlanDefinitionIdentifier",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "PlanDefinitionToken",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "PlanDefinitionReference",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )
    context_quantities = relationship(
        "PlanDefinitionContextQuantity",
        back_populates="plan_definition",
        cascade="all, delete-orphan",
    )

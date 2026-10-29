from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.questionnaire.enums import QuestionnaireStatus
from app.models.shared import TenantAuditMixin

questionnaire_id_seq = Sequence(
    "questionnaire_pub_seq", start=380000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class QuestionnaireModel(TenantAuditMixin, Base):
    """FHIR R4 Questionnaire — https://www.hl7.org/fhir/R4/questionnaire.html

    A structured set of questions intended to guide the collection of
    answers from end-users. Questionnaire is a *canonical*/metadata
    resource (the first one built in this codebase) — it carries the
    common `url`/`version`/`name`/`title`/`status`/`contact`/`useContext`/
    `jurisdiction`/`purpose`/`copyright`/`approvalDate`/`lastReviewDate`
    fields shared by every HL7 "definitional" resource (ValueSet,
    StructureDefinition, PlanDefinition, ...), none of which existed in
    this codebase before.

    Modeled to the same conventions as every other reworked resource:
    BigInteger internal PK + public sequence ID, TenantAuditMixin
    (tenant_id, not a hand-declared org_id), every CodeableConcept's
    coding[] as a real 0..* child/grandchild table.

    Questionnaire now gets the JWT-auth-rollout treatment (see CLAUDE.md's
    Multi-Tenancy & Ownership section and `/resource-auth-rollout`):
    `tenant_id`/`created_by`/`updated_by` are derived from the verified
    JWT (`actor.org_id`/`actor.sub`), never request-body fields, and there
    is no org-less/super-admin bypass. Like Practitioner (and unlike
    Organization/Location/HealthcareService/PractitionerRole/Schedule/
    Slot/Appointment/AppointmentResponse/Encounter), Questionnaire keeps a
    plain `user_id` column — a questionnaire definition isn't inherently a
    shared tenant-level-only entity the way those nine are.

    `item` (0..*, recursive — a question/group can itself contain nested
    items to unbounded depth) is NOT modeled as a chain of selectinload()
    hops (impossible — the nesting depth isn't known ahead of time).
    Instead every QuestionnaireItem row, at every depth, carries BOTH a
    `parent_item_id` self-referential FK (NULL for a top-level item) AND a
    denormalized `questionnaire_pk` FK straight back to this table. One
    eager-loaded, flat `items` relationship (below) therefore fetches every
    item in the whole tree in a single query; the mapper reconstructs the
    nested FHIR `item[]` shape in Python by grouping the flat list on
    `parent_item_id`. The denormalized `questionnaire_pk` also makes
    patch_full()'s list-replace a single `DELETE ... WHERE questionnaire_pk
    = :id` regardless of how deep the old tree was — see
    app/repository/questionnaire/full.py.
    """

    __tablename__ = "questionnaire"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    questionnaire_id = Column(
        BigInteger,
        questionnaire_id_seq,
        server_default=questionnaire_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Plain, gateway-forwarded user_id — unlike tenant_id/created_by/
    # updated_by (TenantAuditMixin), this one is NOT derived from the JWT.
    # Same shape as Practitioner's own user_id.
    user_id = Column(String, nullable=True, index=True)

    # ── url (0..1 uri) ─────────────────────────────────────────────────────
    url = Column(String, nullable=True)

    # ── version (0..1 string) ─────────────────────────────────────────────
    version = Column(String, nullable=True)

    # ── name (0..1 string) ────────────────────────────────────────────────
    name = Column(String, nullable=True)

    # ── title (0..1 string) ───────────────────────────────────────────────
    title = Column(String, nullable=True)

    # ── derivedFrom (0..* canonical(Questionnaire)) ───────────────────────
    # Plain canonical-URI strings, not a flattened Reference — a canonical
    # reference is just a uri/version string, never resolved to a public
    # id the way a Reference(ResourceType) is. Real Postgres ARRAY(String),
    # not comma-text — see CLAUDE.md's FHIR DB Model Design Step 2.
    derived_from = Column(ARRAY(String), nullable=True)

    # ── status (1..1 code) — required ─────────────────────────────────────
    status = Column(Enum(QuestionnaireStatus, name="questionnaire_status"), nullable=False)

    # ── experimental (0..1 boolean) ───────────────────────────────────────
    experimental = Column(Boolean, nullable=True)

    # ── subjectType (0..* code) ───────────────────────────────────────────
    # Bound to the (huge, ever-growing) ResourceType value set — ARRAY(String)
    # rather than an Enum with hundreds of members, same reasoning as
    # Location.type staying open-coded where the bound value set is large.
    subject_type = Column(ARRAY(String), nullable=True)

    # ── date (0..1 dateTime) ──────────────────────────────────────────────
    date = Column(DateTime(timezone=True), nullable=True)

    # ── publisher (0..1 string) ───────────────────────────────────────────
    publisher = Column(String, nullable=True)

    # ── description (0..1 markdown) ───────────────────────────────────────
    description = Column(Text, nullable=True)

    # ── purpose (0..1 markdown) ───────────────────────────────────────────
    purpose = Column(Text, nullable=True)

    # ── copyright (0..1 markdown) ─────────────────────────────────────────
    copyright = Column(Text, nullable=True)

    # ── approvalDate (0..1 date) ──────────────────────────────────────────
    approval_date = Column(Date, nullable=True)

    # ── lastReviewDate (0..1 date) ────────────────────────────────────────
    last_review_date = Column(Date, nullable=True)

    # ── effectivePeriod (0..1 Period) ─────────────────────────────────────
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not Questionnaire-specific). Same shape as
    # every other resource's extension column.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above.

    # ── Relationships ─────────────────────────────────────────────────────

    identifiers = relationship(
        "QuestionnaireIdentifier",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "QuestionnaireContact",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    use_contexts = relationship(
        "QuestionnaireUseContext",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    jurisdictions = relationship(
        "QuestionnaireJurisdiction",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    codings = relationship(
        "QuestionnaireCoding",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    # Flat collection of EVERY item row for this questionnaire, at every
    # nesting depth (see class docstring) — not just top-level items.
    items = relationship(
        "QuestionnaireItem",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )

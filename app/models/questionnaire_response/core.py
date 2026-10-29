from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Sequence, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import EncounterReferenceType, IdentifierUse, OrganizationReferenceType
from app.models.questionnaire_response.enums import (
    QuestionnaireResponseAuthorReferenceType,
    QuestionnaireResponseSourceReferenceType,
    QuestionnaireResponseStatus,
)
from app.models.shared import TenantAuditMixin

questionnaire_response_id_seq = Sequence(
    "questionnaire_response_pub_seq", start=60000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class QuestionnaireResponseModel(TenantAuditMixin, Base):
    """FHIR R4 QuestionnaireResponse — https://www.hl7.org/fhir/R4/questionnaireresponse.html

    A set of answers to a set of questions, generally the result of
    completing a Questionnaire.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout
    (see CLAUDE.md's Multi-Tenancy & Ownership section): `tenant_id`/
    `created_by`/`updated_by` are plain, gateway-forwarded request fields,
    same as every resource that hasn't been explicitly asked to get the
    auth-rollout treatment (`/resource-auth-rollout`). Keeps a plain
    `user_id` column, same shape as Questionnaire's own — this is the
    first NEW resource built since every other currently-built resource
    was individually rolled into auth, so it's also the first live example
    of the plain default pattern this codebase's docs always described but
    had no current example of.

    `identifier` (0..1 Identifier — unlike Questionnaire's own 0..*
    identifier[]) is flattened directly onto this row rather than getting
    its own child table (nothing to list — there's only ever one). Its own
    `.type` CodeableConcept still gets a real child coding table
    (QuestionnaireResponseIdentifierTypeCoding, in identifier_type_coding.py)
    regardless of the parent field's 0..1 cardinality, same reasoning as
    Appointment's cancelationReason/appointmentType (a CodeableConcept's
    own coding[] is always 0..* regardless of the containing field's
    cardinality).

    `subject`/`author`/`source`/`encounter` are all flattened Reference
    fields with the standard `{prefix}_reference`/`_type`/`_id`/`_display`
    + `{prefix}_identifier_*` logical-reference fallback shape.
    `subject` is genuinely `Reference(Any)` (free-text `subject_type`, no
    enum, no existence check — see CLAUDE.md's Reference(Any) invariant).
    `author`/`source` are each a small, finite, enumerable target-type set
    (own enums below) with existence checks enforced only for the subset
    that are actually modeled resources here (Practitioner/
    PractitionerRole/Organization for author; Practitioner/
    PractitionerRole for source — see
    app.repository.questionnaire_response._shared's _MODELED_AUTHOR_TYPES/
    _MODELED_SOURCE_TYPES). `encounter` targets only Encounter, which IS a
    modeled resource, so it reuses the shared, already-created
    `encounter_reference_type` enum (create_type=False) and its existence
    check is always enforced.

    `questionnaire` (0..1 canonical(Questionnaire)) is a plain String
    column holding the raw canonical URL — never resolved to a local
    Questionnaire row, same convention as Questionnaire.derivedFrom's own
    canonical references (a canonical reference is a url/version string,
    not a Reference, so it never gets `_type`/`_id`/`_display` columns).

    `item` (0..*, recursive — see QuestionnaireResponseItem's own
    docstring) and `item.answer` (0..*, see QuestionnaireResponseAnswer's
    own docstring) are mutually recursive: a specific item's own children
    live either directly under `item.item` OR under one of its answers'
    `item[]` — never both, per the FHIR invariant "Nested item can't be
    beneath both item and answer" (enforced by the validator layer, not a
    DB constraint, same as every other structural R4 rule in this
    codebase). Every row of both tables carries `questionnaire_response_pk`
    denormalized straight back to this row, so a single eager-loaded flat
    `items`/`answers` pair of collections fetches the entire tree
    regardless of nesting depth — same trick as Questionnaire.item's own
    `questionnaire_pk`, just needed on two tables instead of one here.
    """

    __tablename__ = "questionnaire_response"

    # Internal PK — never exposed. BigInteger so every child table's FK shares
    # the type.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    questionnaire_response_id = Column(
        BigInteger,
        questionnaire_response_id_seq,
        server_default=questionnaire_response_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Plain, gateway-forwarded user_id — default pattern, not derived from
    # any JWT.
    user_id = Column(String, nullable=True, index=True)

    # ── identifier (0..1 Identifier) — flattened ──────────────────────────

    identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    identifier_type_text = Column(String, nullable=True)
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    identifier_assigner_reference = Column(String, nullable=True)
    identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    identifier_assigner_type = Column(
        Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
        nullable=True,
    )
    identifier_assigner_display = Column(String, nullable=True)

    identifier_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_assigner_identifier_type_system = Column(String, nullable=True)
    identifier_assigner_identifier_type_version = Column(String, nullable=True)
    identifier_assigner_identifier_type_code = Column(String, nullable=True)
    identifier_assigner_identifier_type_display = Column(String, nullable=True)
    identifier_assigner_identifier_type_text = Column(String, nullable=True)
    identifier_assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    identifier_assigner_identifier_system = Column(String, nullable=True)
    identifier_assigner_identifier_value = Column(String, nullable=True)
    identifier_assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    identifier_assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── questionnaire (0..1 canonical(Questionnaire)) ─────────────────────

    questionnaire = Column(String, nullable=True)

    # ── status (1..1 code) — required ─────────────────────────────────────

    status = Column(
        Enum(QuestionnaireResponseStatus, name="questionnaire_response_status"), nullable=False
    )

    # ── subject (0..1 Reference(Any)) ─────────────────────────────────────

    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── encounter (0..1 Reference(Encounter)) ─────────────────────────────

    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False), nullable=True
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    encounter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    encounter_identifier_type_system = Column(String, nullable=True)
    encounter_identifier_type_version = Column(String, nullable=True)
    encounter_identifier_type_code = Column(String, nullable=True)
    encounter_identifier_type_display = Column(String, nullable=True)
    encounter_identifier_type_text = Column(String, nullable=True)
    encounter_identifier_type_user_selected = Column(Boolean, nullable=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)
    encounter_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    encounter_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── authored (0..1 dateTime) ───────────────────────────────────────────

    authored = Column(DateTime(timezone=True), nullable=True)

    # ── author (0..1 Reference, polymorphic across 6 types) ───────────────

    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            QuestionnaireResponseAuthorReferenceType,
            name="questionnaire_response_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    author_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_identifier_type_system = Column(String, nullable=True)
    author_identifier_type_version = Column(String, nullable=True)
    author_identifier_type_code = Column(String, nullable=True)
    author_identifier_type_display = Column(String, nullable=True)
    author_identifier_type_text = Column(String, nullable=True)
    author_identifier_type_user_selected = Column(Boolean, nullable=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)
    author_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    author_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── source (0..1 Reference, polymorphic across 4 types) ───────────────

    source_reference = Column(String, nullable=True)
    source_type = Column(
        Enum(
            QuestionnaireResponseSourceReferenceType,
            name="questionnaire_response_source_reference_type",
        ),
        nullable=True,
    )
    source_id = Column(BigInteger, nullable=True, index=True)
    source_display = Column(String, nullable=True)

    source_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    source_identifier_type_system = Column(String, nullable=True)
    source_identifier_type_version = Column(String, nullable=True)
    source_identifier_type_code = Column(String, nullable=True)
    source_identifier_type_display = Column(String, nullable=True)
    source_identifier_type_text = Column(String, nullable=True)
    source_identifier_type_user_selected = Column(Boolean, nullable=True)
    source_identifier_system = Column(String, nullable=True)
    source_identifier_value = Column(String, nullable=True)
    source_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    source_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # Resource-level extension support (0..* Extension, inherited from the
    # base DomainResource type — not resource-specific). Same shape as
    # every other resource's extension column.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    # come from TenantAuditMixin above.

    # ── Relationships ─────────────────────────────────────────────────────

    identifier_type_codings = relationship(
        "QuestionnaireResponseIdentifierTypeCoding",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )
    based_ons = relationship(
        "QuestionnaireResponseBasedOn",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )
    part_ofs = relationship(
        "QuestionnaireResponsePartOf",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )
    # Flat collections of EVERY item/answer row for this response, at every
    # nesting depth (see QuestionnaireResponseItem's/
    # QuestionnaireResponseAnswer's own docstrings) — not just top-level.
    items = relationship(
        "QuestionnaireResponseItem",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )
    answers = relationship(
        "QuestionnaireResponseAnswer",
        back_populates="questionnaire_response",
        cascade="all, delete-orphan",
    )

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Plain (snake_case) row shapes for every bare-Reference field on
# QuestionnaireResponse. FHIR (camelCase) rendering reuses
# app.schemas.datatypes.FHIRReference directly — no custom FHIR class
# needed, these fields are plain Reference with nothing extra.
# ---------------------------------------------------------------------------


class _PlainReferenceRow(BaseModel):
    """basedOn[]/partOf[] — real 0..* child-table rows, so each carries its
    own `id`. Mirrors app.schemas.appointment.response._PlainReferenceRow."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainQuestionnaireResponseBasedOn(_PlainReferenceRow):
    pass


class PlainQuestionnaireResponsePartOf(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    """subject/encounter/author/source — each flattened directly onto the
    main row (0..1, not a child table), so no `id` here."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainQuestionnaireResponseSubject(_PlainSingleReferenceRow):
    pass


class PlainQuestionnaireResponseEncounter(_PlainSingleReferenceRow):
    pass


class PlainQuestionnaireResponseAuthor(_PlainSingleReferenceRow):
    pass


class PlainQuestionnaireResponseSource(_PlainSingleReferenceRow):
    pass

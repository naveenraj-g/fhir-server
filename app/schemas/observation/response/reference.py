from pydantic import BaseModel, ConfigDict


class _PlainReferenceRow(BaseModel):
    """List-item Reference rows — real 0..* child-table rows, so each
    carries its own `id`."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainObservationBasedOn(_PlainReferenceRow):
    pass


class PlainObservationPartOf(_PlainReferenceRow):
    pass


class PlainObservationFocus(_PlainReferenceRow):
    pass


class PlainObservationPerformer(_PlainReferenceRow):
    pass


class PlainObservationHasMember(_PlainReferenceRow):
    pass


class PlainObservationDerivedFrom(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    """Single 0..1 Reference fields — flattened directly onto the owning
    row, so no `id` here."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainObservationSubject(_PlainSingleReferenceRow):
    pass


class PlainObservationEncounter(_PlainSingleReferenceRow):
    pass


class PlainObservationSpecimen(_PlainSingleReferenceRow):
    pass


class PlainObservationDevice(_PlainSingleReferenceRow):
    pass

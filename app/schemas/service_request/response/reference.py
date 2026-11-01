from pydantic import BaseModel, ConfigDict


class _PlainReferenceRow(BaseModel):
    """List-item Reference rows (basedOn/replaces/locationReference/
    reasonReference/insurance/specimen/relevantHistory/performer) — real
    0..* child-table rows, so each carries its own `id`."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None
    reference_identifier_use: str | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: str | None = None
    reference_identifier_period_end: str | None = None


class PlainServiceRequestBasedOn(_PlainReferenceRow):
    pass


class PlainServiceRequestReplaces(_PlainReferenceRow):
    pass


class PlainServiceRequestLocationReference(_PlainReferenceRow):
    pass


class PlainServiceRequestReasonReference(_PlainReferenceRow):
    pass


class PlainServiceRequestInsurance(_PlainReferenceRow):
    pass


class PlainServiceRequestSpecimen(_PlainReferenceRow):
    pass


class PlainServiceRequestSupportingInfo(_PlainReferenceRow):
    pass


class PlainServiceRequestRelevantHistory(_PlainReferenceRow):
    pass


class PlainServiceRequestPerformer(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    """subject/encounter/requester — flattened directly onto the main row
    (0..1 or 1..1, not a child table), so no `id` here."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None
    reference_identifier_use: str | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: str | None = None
    reference_identifier_period_end: str | None = None


class PlainServiceRequestSubject(_PlainSingleReferenceRow):
    pass


class PlainServiceRequestEncounter(_PlainSingleReferenceRow):
    pass


class PlainServiceRequestRequester(_PlainSingleReferenceRow):
    pass

from pydantic import Field

from ._shared import PlainLocationCoding, _AuditFields


class PlainLocationType(_AuditFields):
    """Location.type (CodeableConcept) — `codings` is a real 0..* child
    table rather than a single flattened coding, mirroring
    app.schemas.organization.response.type.PlainOrganizationType."""

    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainLocationCoding] | None = Field(
        None, description="Coding(s) for this location type."
    )
    text: str | None = Field(
        None, description="A human language representation of the location type."
    )

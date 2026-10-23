from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainLocationType(AuditFields):
    """Location.type (CodeableConcept) — `codings` is a real 0..* child
    table rather than a single flattened coding, mirroring
    app.schemas.organization.response.type.PlainOrganizationType."""

    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this location type."
    )
    text: str | None = Field(
        None, description="A human language representation of the location type."
    )

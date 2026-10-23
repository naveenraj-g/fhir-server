from pydantic import Field

from app.schemas.datatypes import ContactPointInput
from app.schemas.enums import ContactPointSystem


class LocationTelecomInput(ContactPointInput):
    """Location.telecom — contact detail (phone, fax, email, website) for the
    location (ContactPoint). Unlike the base ContactPointInput (FHIR's own
    0..1 cardinality for system/value), this resource requires both."""

    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for the contact point — what communications system is required to make use of it: phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ...,
        description="The actual contact point details, in a form meaningful to the designated communication system (e.g. a phone number or email address).",
    )

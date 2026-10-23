from pydantic import Field

from app.schemas.datatypes import ContactPointInput
from app.schemas.enums import ContactPointSystem


class HealthcareServiceTelecomInput(ContactPointInput):
    """HealthcareService.telecom — contact details for the healthcare service
    (ContactPoint). Unlike the base ContactPointInput (FHIR's own 0..1
    cardinality for system/value), this resource requires both."""

    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for the contact point — phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ...,
        description="The actual contact point details, in a form meaningful to the designated communication system.",
    )

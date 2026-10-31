from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.consent.response.codeable_concept import (
    PlainConsentCodeableConcept,
    PlainConsentCoding,
)
from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRPeriod,
    FHIRReference,
)


class FHIRConsentProvisionActor(BaseModel):
    """FHIR response schema for Consent.provision.actor."""

    model_config = ConfigDict(extra="allow")

    role: FHIRCodeableConcept
    reference: FHIRReference


class PlainConsentProvisionActor(BaseModel):
    """Plain response schema for Consent provision actor."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    role: PlainConsentCodeableConcept
    reference: str
    reference_display: str | None = None


class FHIRConsentProvisionData(BaseModel):
    """FHIR response schema for Consent.provision.data."""

    model_config = ConfigDict(extra="allow")

    meaning: str
    reference: FHIRReference


class PlainConsentProvisionData(BaseModel):
    """Plain response schema for Consent provision data."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    meaning: str
    reference: str
    reference_display: str | None = None


class FHIRConsentProvision(BaseModel):
    """FHIR response schema for Consent.provision."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str | None = None
    period: FHIRPeriod | None = None
    actor: list[FHIRConsentProvisionActor] | None = None
    action: list[FHIRCodeableConcept] | None = None
    securityLabel: list[FHIRCoding] | None = None
    purpose: list[FHIRCoding] | None = None
    class_: list[FHIRCoding] | None = Field(None, alias="class")
    code: list[FHIRCodeableConcept] | None = None
    dataPeriod: FHIRPeriod | None = None
    data: list[FHIRConsentProvisionData] | None = None
    provision: list["FHIRConsentProvision"] | None = None


FHIRConsentProvision.model_rebuild()


class PlainConsentProvision(BaseModel):
    """Plain response schema for Consent provision."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int | None = Field(None, description="Internal DB ID.")
    type: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    actor: list[PlainConsentProvisionActor] | None = None
    action: list[PlainConsentCodeableConcept] | None = None
    security_label: list[PlainConsentCoding] | None = None
    purpose: list[PlainConsentCoding] | None = None
    class_: list[PlainConsentCoding] | None = Field(None, alias="class")
    code: list[PlainConsentCodeableConcept] | None = None
    data_period_start: datetime | None = None
    data_period_end: datetime | None = None
    data: list[PlainConsentProvisionData] | None = None
    provision: list["PlainConsentProvision"] | None = None


PlainConsentProvision.model_rebuild()

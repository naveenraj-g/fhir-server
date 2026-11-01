from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.episode_of_care.response.diagnosis import (
    FHIRDiagnosis,
    PlainEpisodeOfCareDiagnosis,
)
from app.schemas.episode_of_care.response.identifier import (
    PlainEpisodeOfCareIdentifier,
)
from app.schemas.episode_of_care.response.status_history import (
    FHIRStatusHistory,
    PlainEpisodeOfCareStatusHistory,
)


class PlainEpisodeOfCareType(AuditFields, BaseModel):
    """Plain response representation of EpisodeOfCare.type."""

    model_config = ConfigDict(extra="forbid")

    id: int
    text: str | None = None
    codings: list[PlainCodingRow] = []


class PlainEpisodeOfCareReference(AuditFields, BaseModel):
    """Plain response representation of a 0..* reference."""

    model_config = ConfigDict(extra="forbid")

    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    display: str | None = None
    identifier_use: str | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: datetime | None = None
    identifier_period_end: datetime | None = None


# ── FHIR Schema ───────────────────────────────────────────────────────────────


class FHIREpisodeOfCareSchema(BaseModel):
    """Full FHIR R4 EpisodeOfCare representation."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["EpisodeOfCare"] = "EpisodeOfCare"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    status: str
    statusHistory: list[FHIRStatusHistory] | None = None
    type: list[FHIRCodeableConcept] | None = None
    diagnosis: list[FHIRDiagnosis] | None = None
    patient: FHIRReference
    managingOrganization: FHIRReference | None = None
    period: FHIRPeriod | None = None
    referralRequest: list[FHIRReference] | None = None
    careManager: FHIRReference | None = None
    team: list[FHIRReference] | None = None
    account: list[FHIRReference] | None = None


# ── Plain Response ─────────────────────────────────────────────────────────────


class PlainEpisodeOfCareResponse(AuditFields, BaseModel):
    """Simplified snake_case representation of EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    id: int
    status: str
    patient: str | None = None
    patient_id: int | None = None
    patient_type: str | None = None
    patient_display: str | None = None
    patient_identifier_use: str | None = None
    patient_identifier_type_system: str | None = None
    patient_identifier_type_version: str | None = None
    patient_identifier_type_code: str | None = None
    patient_identifier_type_display: str | None = None
    patient_identifier_type_user_selected: bool | None = None
    patient_identifier_type_text: str | None = None
    patient_identifier_system: str | None = None
    patient_identifier_value: str | None = None
    patient_identifier_period_start: datetime | None = None
    patient_identifier_period_end: datetime | None = None

    managing_organization: str | None = None
    managing_organization_id: int | None = None
    managing_organization_type: str | None = None
    managing_organization_display: str | None = None
    managing_organization_identifier_use: str | None = None
    managing_organization_identifier_type_system: str | None = None
    managing_organization_identifier_type_version: str | None = None
    managing_organization_identifier_type_code: str | None = None
    managing_organization_identifier_type_display: str | None = None
    managing_organization_identifier_type_user_selected: bool | None = None
    managing_organization_identifier_type_text: str | None = None
    managing_organization_identifier_system: str | None = None
    managing_organization_identifier_value: str | None = None
    managing_organization_identifier_period_start: datetime | None = None
    managing_organization_identifier_period_end: datetime | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    care_manager: str | None = None
    care_manager_id: int | None = None
    care_manager_type: str | None = None
    care_manager_display: str | None = None
    care_manager_identifier_use: str | None = None
    care_manager_identifier_type_system: str | None = None
    care_manager_identifier_type_version: str | None = None
    care_manager_identifier_type_code: str | None = None
    care_manager_identifier_type_display: str | None = None
    care_manager_identifier_type_user_selected: bool | None = None
    care_manager_identifier_type_text: str | None = None
    care_manager_identifier_system: str | None = None
    care_manager_identifier_value: str | None = None
    care_manager_identifier_period_start: datetime | None = None
    care_manager_identifier_period_end: datetime | None = None

    identifiers: list[PlainEpisodeOfCareIdentifier] = []
    status_history: list[PlainEpisodeOfCareStatusHistory] = []
    types: list[PlainEpisodeOfCareType] = []
    diagnoses: list[PlainEpisodeOfCareDiagnosis] = []
    referral_requests: list[PlainEpisodeOfCareReference] = []
    teams: list[PlainEpisodeOfCareReference] = []
    accounts: list[PlainEpisodeOfCareReference] = []


# ── Paginated / Bundle ─────────────────────────────────────────────────────────


class PaginatedEpisodeOfCareResponse(BaseModel):
    """Paginated plain responses."""

    model_config = ConfigDict(extra="forbid")

    total: int | None = None
    limit: int
    offset: int
    data: list[PlainEpisodeOfCareResponse]


class FHIREpisodeOfCareBundleEntry(BaseModel):
    """One entry in a FHIR EpisodeOfCare bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str | None = None
    resource: FHIREpisodeOfCareSchema


class FHIREpisodeOfCareBundle(BaseModel):
    """FHIR R4 Bundle of EpisodeOfCare resources."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int | None = None
    entry: list[FHIREpisodeOfCareBundleEntry] = Field(default_factory=list)

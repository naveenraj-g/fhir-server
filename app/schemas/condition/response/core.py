from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.questionnaire.response import FHIRQuantity, FHIRRange
from app.schemas.service_request.response.core import FHIRAnnotation

from .codeable_concept import PlainConditionBodySite, PlainConditionCategory
from .evidence import FHIRConditionEvidence, PlainConditionEvidence
from .identifier import PlainConditionIdentifier
from .note import PlainConditionNote
from .reference import (
    PlainConditionAsserter,
    PlainConditionEncounter,
    PlainConditionRecorder,
    PlainConditionSubject,
)
from .stage import FHIRConditionStage, PlainConditionStage

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRConditionSchema(BaseModel):
    """FHIR R4 Condition resource representation."""

    resourceType: str = Field("Condition", description="Always 'Condition'.")
    id: str = Field(..., description="Public condition_id as a string.")
    meta: FHIRMeta | None = Field(
        None, description="Infrastructure-maintained resource metadata. Response-only."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External ids for this condition."
    )
    clinicalStatus: FHIRCodeableConcept | None = Field(
        None, description="active | recurrence | relapse | inactive | remission | resolved."
    )
    verificationStatus: FHIRCodeableConcept | None = Field(
        None, description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="problem-list-item | encounter-diagnosis."
    )
    severity: FHIRCodeableConcept | None = Field(
        None, description="Subjective severity of condition."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Identification of the condition, problem or diagnosis."
    )
    bodySite: list[FHIRCodeableConcept] | None = Field(
        None, description="Anatomical location, if relevant."
    )
    subject: FHIRReference = Field(
        ..., description="Who has the condition (1..1 Reference(Patient | Group))."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    onsetDateTime: str | None = Field(
        None, description="onset[x]: dateTime."
    )
    onsetAge: FHIRQuantity | None = Field(
        None, description="onset[x]: Age (Quantity)."
    )
    onsetPeriod: FHIRPeriod | None = Field(
        None, description="onset[x]: Period."
    )
    onsetRange: FHIRRange | None = Field(
        None, description="onset[x]: Range."
    )
    onsetString: str | None = Field(
        None, description="onset[x]: string."
    )
    abatementDateTime: str | None = Field(
        None, description="abatement[x]: dateTime."
    )
    abatementAge: FHIRQuantity | None = Field(
        None, description="abatement[x]: Age (Quantity)."
    )
    abatementPeriod: FHIRPeriod | None = Field(
        None, description="abatement[x]: Period."
    )
    abatementRange: FHIRRange | None = Field(
        None, description="abatement[x]: Range."
    )
    abatementString: str | None = Field(
        None, description="abatement[x]: string."
    )
    recordedDate: str | None = Field(
        None, description="Date record was first recorded."
    )
    recorder: FHIRReference | None = Field(
        None, description="Who recorded the condition."
    )
    asserter: FHIRReference | None = Field(
        None, description="Person who asserts this condition."
    )
    stage: list[FHIRConditionStage] | None = Field(
        None, description="Stage/grade, usually assessed formally."
    )
    evidence: list[FHIRConditionEvidence] | None = Field(
        None, description="Supporting evidence."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Additional information about the condition."
    )


class FHIRConditionBundleEntry(BaseModel):
    resource: FHIRConditionSchema


class FHIRConditionBundle(FHIRBundle):
    entry: list[FHIRConditionBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainConditionResponse(BaseModel):
    """Plain snake_case response shape for Condition."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence condition_id.")
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    clinical_status_text: str | None = Field(
        None, description="clinicalStatus text representation."
    )
    clinical_status_codings: list[PlainCodingRow] | None = Field(
        None, description="clinicalStatus codings."
    )
    verification_status_text: str | None = Field(
        None, description="verificationStatus text representation."
    )
    verification_status_codings: list[PlainCodingRow] | None = Field(
        None, description="verificationStatus codings."
    )
    severity_text: str | None = Field(
        None, description="severity text representation."
    )
    severity_codings: list[PlainCodingRow] | None = Field(
        None, description="severity codings."
    )
    code_text: str | None = Field(
        None, description="code text representation."
    )
    code_codings: list[PlainCodingRow] | None = Field(
        None, description="code codings."
    )
    categories: list[PlainConditionCategory] | None = Field(
        None, description="Condition categories."
    )
    body_sites: list[PlainConditionBodySite] | None = Field(
        None, description="Condition bodySites."
    )
    subject: PlainConditionSubject | None = Field(
        None, description="Subject reference."
    )
    encounter: PlainConditionEncounter | None = Field(
        None, description="Encounter reference."
    )
    onset_date_time: str | None = None
    onset_age_value: float | None = None
    onset_age_comparator: str | None = None
    onset_age_unit: str | None = None
    onset_age_system: str | None = None
    onset_age_code: str | None = None
    onset_period_start: str | None = None
    onset_period_end: str | None = None
    onset_range_low_value: float | None = None
    onset_range_low_unit: str | None = None
    onset_range_low_system: str | None = None
    onset_range_low_code: str | None = None
    onset_range_high_value: float | None = None
    onset_range_high_unit: str | None = None
    onset_range_high_system: str | None = None
    onset_range_high_code: str | None = None
    onset_string: str | None = None

    abatement_date_time: str | None = None
    abatement_age_value: float | None = None
    abatement_age_comparator: str | None = None
    abatement_age_unit: str | None = None
    abatement_age_system: str | None = None
    abatement_age_code: str | None = None
    abatement_period_start: str | None = None
    abatement_period_end: str | None = None
    abatement_range_low_value: float | None = None
    abatement_range_low_unit: str | None = None
    abatement_range_low_system: str | None = None
    abatement_range_low_code: str | None = None
    abatement_range_high_value: float | None = None
    abatement_range_high_unit: str | None = None
    abatement_range_high_system: str | None = None
    abatement_range_high_code: str | None = None
    abatement_string: str | None = None

    recorded_date: str | None = None
    recorder: PlainConditionRecorder | None = None
    asserter: PlainConditionAsserter | None = None
    stages: list[PlainConditionStage] | None = Field(
        None, description="Condition stages."
    )
    evidence: list[PlainConditionEvidence] | None = Field(
        None, description="Condition evidence."
    )
    notes: list[PlainConditionNote] | None = Field(
        None, description="Condition notes."
    )
    identifiers: list[PlainConditionIdentifier] | None = Field(
        None, description="Condition identifiers."
    )


class PaginatedConditionResponse(BaseModel):
    """Paginated plain snake_case response for Conditions."""

    total: int = Field(..., description="Total count matching filter.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainConditionResponse] = Field(..., description="List of Conditions.")

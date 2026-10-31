from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_team.response.identifier import PlainCareTeamIdentifier
from app.schemas.care_team.response.note import PlainCareTeamNote
from app.schemas.care_team.response.participant import (
    FHIRCareTeamParticipant,
    PlainCareTeamParticipant,
)
from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
    PlainContactPointRow,
)
from app.schemas.service_request.response.core import FHIRAnnotation


class FHIRCareTeamSchema(BaseModel):
    """FHIR R4 CareTeam resource representation."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["CareTeam"] = Field(
        "CareTeam", description="Always 'CareTeam'."
    )
    id: str = Field(..., description="Public care_team_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Resource metadata.")
    extension: list[dict] | None = Field(None, description="Resource extensions.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Ids for this team."
    )
    status: str | None = Field(
        None,
        description="proposed | active | suspended | inactive | entered-in-error.",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of team."
    )
    name: str | None = Field(
        None, description="Name of the team, such as crisis assessment team."
    )
    subject: FHIRReference | None = Field(
        None, description="Who care team is for (Patient | Group)."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    period: FHIRPeriod | None = Field(
        None, description="Time period team covers."
    )
    participant: list[FHIRCareTeamParticipant] | None = Field(
        None, description="Members of the team."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why the care team exists."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why the care team exists (Reference(Condition))."
    )
    managingOrganization: list[FHIRReference] | None = Field(
        None, description="Organization responsible for the care team."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the care team."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments about the care team."
    )


class PlainCareTeamCategory(BaseModel):
    """Plain response shape for CareTeam.category."""

    model_config = ConfigDict(extra="allow")
    id: int | None = None
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainCareTeamReasonCode(BaseModel):
    """Plain response shape for CareTeam.reasonCode."""

    model_config = ConfigDict(extra="allow")
    id: int | None = None
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainCareTeamReference(BaseModel):
    """Plain response shape for a Reference child row."""

    model_config = ConfigDict(extra="allow")
    id: int | None = None
    reference: str | None = None
    type: str | None = None
    reference_id: int | None = None
    display: str | None = None


class PlainCareTeamResponse(AuditFields):
    """Snake_case plain JSON response representing a CareTeam."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public care_team_id as an integer.")
    status: str | None = None
    name: str | None = None
    subject: str | None = None
    subject_id: int | None = None
    subject_type: str | None = None
    subject_display: str | None = None
    encounter: str | None = None
    encounter_id: int | None = None
    encounter_type: str | None = None
    encounter_display: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None

    identifiers: list[PlainCareTeamIdentifier] = Field(default_factory=list)
    categories: list[PlainCareTeamCategory] = Field(default_factory=list)
    participants: list[PlainCareTeamParticipant] = Field(default_factory=list)
    reason_codes: list[PlainCareTeamReasonCode] = Field(default_factory=list)
    reason_references: list[PlainCareTeamReference] = Field(default_factory=list)
    managing_organizations: list[PlainCareTeamReference] = Field(default_factory=list)
    telecoms: list[PlainContactPointRow] = Field(default_factory=list)
    notes: list[PlainCareTeamNote] = Field(default_factory=list)


class PaginatedCareTeamResponse(BaseModel):
    """Paginated plain envelope for CareTeam listings."""

    total: int | None = None
    limit: int
    offset: int
    data: list[PlainCareTeamResponse]


class FHIRCareTeamBundleEntry(FHIRBundleEntry):
    resource: FHIRCareTeamSchema = Field(..., description="CareTeam resource.")


class FHIRCareTeamBundle(FHIRBundle):
    entry: list[FHIRCareTeamBundleEntry] = Field(
        default_factory=list, description="CareTeam searchset entries."
    )

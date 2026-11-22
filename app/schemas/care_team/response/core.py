from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRCareTeamParticipant(BaseModel):
    role: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of involvement."
    )
    member: FHIRReference | None = Field(None, description="Who is involved.")
    onBehalfOf: FHIRReference | None = Field(
        None, description="Organization of the practitioner."
    )
    period: FHIRPeriod | None = Field(
        None, description="Time period of the participant."
    )


class FHIRCareTeamSchema(BaseModel):
    resourceType: str = Field("CareTeam", description="Always 'CareTeam'.")
    id: str = Field(..., description="Public care_team_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
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
    name: str | None = Field(None, description="Name of the team.")
    subject: FHIRReference | None = Field(None, description="Who care team is for.")
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    period: FHIRPeriod | None = Field(None, description="Time period team covers.")
    participant: list[FHIRCareTeamParticipant] | None = Field(
        None, description="Members of the team."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why the care team exists."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why the care team exists."
    )
    managingOrganization: list[FHIRReference] | None = Field(
        None, description="Organization responsible for the care team."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the care team."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the CareTeam."
    )


class FHIRCareTeamBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRCareTeamSchema | dict = Field(
        ...,
        description="A CareTeam (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Encounter / Practitioner / PractitionerRole / RelatedPerson / Organization / CareTeam (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRCareTeamBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRCareTeamBundleEntry] | None = None

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationRatio(BaseModel):
    numerator: FHIRQuantity | None = Field(None, description="Numerator value.")
    denominator: FHIRQuantity | None = Field(None, description="Denominator value.")


class FHIRMedicationIngredient(BaseModel):
    itemCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="The actual ingredient (CodeableConcept)."
    )
    itemReference: FHIRReference | None = Field(
        None, description="The actual ingredient (Substance or Medication)."
    )
    isActive: bool | None = Field(None, description="Active ingredient indicator.")
    strength: FHIRMedicationRatio | None = Field(
        None, description="Quantity of ingredient present."
    )


class FHIRMedicationBatch(BaseModel):
    lotNumber: str | None = Field(None, description="Identifier assigned to batch.")
    expirationDate: str | None = Field(None, description="When batch will expire.")


class FHIRMedicationSchema(BaseModel):
    resourceType: str = Field("Medication", description="Always 'Medication'.")
    id: str = Field(..., description="Public medication_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for this medication."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Codes that identify this medication."
    )
    status: str | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    manufacturer: FHIRReference | None = Field(
        None, description="Manufacturer of the item."
    )
    form: FHIRCodeableConcept | None = Field(
        None, description="powder | tablets | capsule ..."
    )
    amount: FHIRMedicationRatio | None = Field(
        None, description="Amount of drug in package."
    )
    ingredient: list[FHIRMedicationIngredient] | None = Field(
        None, description="Active or inactive ingredient."
    )
    batch: FHIRMedicationBatch | None = Field(
        None, description="Details about packaged medications."
    )


class FHIRMedicationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationSchema | dict = Field(
        ...,
        description="A Medication (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Organization / Medication (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationBundleEntry] | None = None

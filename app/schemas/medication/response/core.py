from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.medication.response.batch import (
    FHIRMedicationBatch,
    PlainMedicationBatch,
)
from app.schemas.medication.response.codeable_concept import (
    PlainMedicationCodeableConcept,
)
from app.schemas.medication.response.identifier import (
    PlainMedicationIdentifier,
)
from app.schemas.medication.response.ingredient import (
    FHIRMedicationIngredient,
    PlainMedicationIngredient,
)
from app.schemas.medication.response.quantity import (
    FHIRRatio,
    PlainMedicationRatio,
)
from app.schemas.medication.response.reference import (
    PlainMedicationReference,
)


class FHIRMedicationSchema(BaseModel):
    """FHIR R4 Medication resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Medication"] = "Medication"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier for this medication.")
    code: FHIRCodeableConcept | None = Field(None, description="Codes that identify this medication.")
    status: str | None = Field(None, description="active | inactive | entered-in-error.")
    manufacturer: FHIRReference | None = Field(None, description="Manufacturer of the item (Reference(Organization)).")
    form: FHIRCodeableConcept | None = Field(None, description="powder | tablets | capsule +")
    amount: FHIRRatio | None = Field(None, description="Amount of drug in package.")
    ingredient: list[FHIRMedicationIngredient] | None = Field(None, description="Active or inactive ingredient.")
    batch: FHIRMedicationBatch | None = Field(None, description="Details about packaged medications.")


class PlainMedicationResponse(BaseModel):
    """Plain (snake_case) Medication response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public medication ID (medication_id).")
    extension: list[dict] | None = None
    identifier: list[PlainMedicationIdentifier] | None = None
    code: PlainMedicationCodeableConcept | None = None
    status: str | None = None
    manufacturer: PlainMedicationReference | None = None
    form: PlainMedicationCodeableConcept | None = None
    amount: PlainMedicationRatio | None = None
    ingredient: list[PlainMedicationIngredient] | None = None
    batch: PlainMedicationBatch | None = None


class PaginatedMedicationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    data: list[PlainMedicationResponse]


class FHIRMedicationBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRMedicationSchema


class FHIRMedicationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRMedicationBundleEntry] = []

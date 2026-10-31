from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class FHIRActivityDefinitionDosage(BaseModel):
    """FHIR R4 Dosage."""

    model_config = ConfigDict(extra="allow")

    sequence: int | None = None
    text: str | None = None
    patientInstruction: str | None = None
    timing: dict | None = None
    asNeededBoolean: bool | None = None
    asNeededCodeableConcept: dict | None = None
    site: dict | None = None
    route: dict | None = None
    method: dict | None = None
    doseAndRate: list[dict] | None = None
    maxDosePerPeriod: dict | None = None
    maxDosePerAdministration: dict | None = None
    maxDosePerLifetime: dict | None = None


class PlainActivityDefinitionDosage(BaseModel):
    """Plain Dosage representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    sequence: int | None = None
    text: str | None = None
    patient_instruction: str | None = None
    timing: dict | None = None
    as_needed_boolean: bool | None = None
    as_needed_codeable_concept_text: str | None = None
    as_needed_codings: list[PlainCodingRow] | None = None
    site_text: str | None = None
    site_codings: list[PlainCodingRow] | None = None
    route_text: str | None = None
    route_codings: list[PlainCodingRow] | None = None
    method_text: str | None = None
    method_codings: list[PlainCodingRow] | None = None
    dose_and_rate: list[dict] | None = None
    max_dose_per_period: dict | None = None
    max_dose_per_administration_value: float | None = None
    max_dose_per_administration_unit: str | None = None
    max_dose_per_administration_system: str | None = None
    max_dose_per_administration_code: str | None = None
    max_dose_per_lifetime_value: float | None = None
    max_dose_per_lifetime_unit: str | None = None
    max_dose_per_lifetime_system: str | None = None
    max_dose_per_lifetime_code: str | None = None

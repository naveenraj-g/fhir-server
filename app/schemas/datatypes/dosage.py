from pydantic import BaseModel

from app.schemas.datatypes.codeable_concept import FHIRCodeableConcept
from app.schemas.datatypes.quantity import FHIRQuantity


class FHIRDosage(BaseModel):
    """FHIR R4 Dosage - https://www.hl7.org/fhir/R4/datatypes.html#Dosage
    `timing`, `doseAndRate` and `maxDosePerPeriod` are raw dicts."""

    sequence: int | None = None
    text: str | None = None
    additionalInstruction: list[FHIRCodeableConcept] | None = None
    patientInstruction: str | None = None
    timing: dict | None = None
    asNeededBoolean: bool | None = None
    asNeededCodeableConcept: FHIRCodeableConcept | None = None
    site: FHIRCodeableConcept | None = None
    route: FHIRCodeableConcept | None = None
    method: FHIRCodeableConcept | None = None
    doseAndRate: list[dict] | None = None
    maxDosePerPeriod: dict | None = None
    maxDosePerAdministration: FHIRQuantity | None = None
    maxDosePerLifetime: FHIRQuantity | None = None

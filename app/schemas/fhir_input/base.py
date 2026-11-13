from pydantic import BaseModel, ConfigDict


class FhirInputModel(BaseModel):
    """Base for every FHIR-shaped input model.

    Keys a model doesn't declare are not rejected here: a client may send
    any valid FHIR R4 element, and the full validated body is what gets
    stored. Whether the body is valid FHIR at all is decided by base R4
    validation of the raw request body — see app.fhir.input_payload."""

    model_config = ConfigDict(extra="ignore")

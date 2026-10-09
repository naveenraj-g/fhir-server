from app.core.schema_utils import inline_schema
from app.schemas.fhir_validate import OperationOutcomeSchema

_VALIDATE_200 = {
    200: {
        "content": {
            "application/fhir+json": {
                "schema": inline_schema(OperationOutcomeSchema.model_json_schema())
            }
        }
    }
}

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.errors.fhir_codes import IssueType
from app.fhir.validation.dispatch import validate_resource

from ._responses import _VALIDATE_200

router = APIRouter()


def _build_operation_outcome(errors: list[dict]) -> dict:
    if not errors:
        return {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "information",
                    "code": IssueType.INFORMATIONAL.value,
                    "diagnostics": "No issues detected. Resource is valid against the most specific applicable profile.",
                }
            ],
        }

    issues = []
    for error in errors:
        issue_type = error.get("issue_type", IssueType.INVALID)
        code = issue_type.value if hasattr(issue_type, "value") else str(issue_type)
        issue = {
            "severity": "error",
            "code": code,
            "diagnostics": error.get("message", ""),
            "expression": [error["field"]] if error.get("field") else None,
        }
        if error.get("details"):
            issue["details"] = error["details"]
        issues.append({k: v for k, v in issue.items() if v is not None})
    return {"resourceType": "OperationOutcome", "issue": issues}


@router.post(
    "/",
    operation_id="validate_fhir_resource",
    summary="Validate any FHIR resource against the most specific applicable profile",
    description=(
        "Accepts any FHIR R4 resource JSON body (resourceType is read directly "
        "from it — this isn't scoped to one resource type) and runs it through "
        "the exact same validate_resource() dispatch every resource's own "
        "create/patch path uses internally: base, narrowed by a country profile "
        "if settings.fhir_validation.country has one active for this resource "
        "type, narrowed further by org_id's own active profile if one exists "
        "and org_id is passed. Always returns 200 with a FHIR OperationOutcome "
        "— this is a diagnostic tool for exploring what a payload would fail "
        "on, not a gate, so an invalid resource is a normal, successful "
        "response (one OperationOutcome.issue per problem found), not an "
        "error. Useful for a team or a partner hospital to check a payload "
        "before wiring up a real integration against this server."
    ),
    responses=_VALIDATE_200,
)
async def validate_fhir_resource(
    body: dict,
    org_id: str | None = Query(
        None,
        description="Optional org_id — also checks that organization's own active profile layer, if one exists",
    ),
):
    resource_type = body.get("resourceType")
    if not resource_type:
        raise HTTPException(
            status_code=400, detail="Body must include a 'resourceType' field."
        )
    errors = await validate_resource(resource_type, body, org_id=org_id)
    return JSONResponse(content=jsonable_encoder(_build_operation_outcome(errors)))

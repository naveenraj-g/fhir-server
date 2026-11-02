from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.detected_issue import (
    patch_fragment_to_fhir_detected_issue,
    payload_to_fhir_detected_issue,
    to_fhir_detected_issue,
    to_plain_detected_issue,
)
from app.fhir.validation import validate_resource
from app.models.detected_issue import DetectedIssueModel
from app.repository.detected_issue import DetectedIssueRepository
from app.schemas.detected_issue import (
    DetectedIssueCreateSchema,
    DetectedIssuePatchSchema,
)

logger = get_logger(__name__)


class DetectedIssueService:
    """All DetectedIssue business logic."""

    def __init__(self, repository: DetectedIssueRepository):
        self.repository = repository

    def _to_fhir(self, model: DetectedIssueModel) -> dict:
        return to_fhir_detected_issue(model)

    def _to_plain(self, model: DetectedIssueModel) -> dict:
        return to_plain_detected_issue(model)

    async def get_detected_issue_scoped(
        self, detected_issue_id: int, org_id: str | None
    ) -> DetectedIssueModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "DetectedIssue operation requires an org-scoped token"
            )
        model = await self.repository.get_by_detected_issue_id_in_org(
            detected_issue_id, org_id
        )
        if not model:
            raise NotFoundError("DetectedIssue not found")
        return model

    async def list_detected_issues(
        self,
        org_id: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        author: str | None = None,
        identified: date | datetime | str | None = None,
        identifier: str | None = None,
        code: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[DetectedIssueModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "DetectedIssue operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            patient=patient,
            author=author,
            identified=identified,
            identifier=identifier,
            code=code,
        )

    async def create_detected_issue(
        self,
        payload: DetectedIssueCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> DetectedIssueModel:
        if not org_id:
            raise PermissionDeniedError(
                "DetectedIssue creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "DetectedIssue creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_detected_issue(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "DetectedIssue created",
            extra={
                "event": "detected_issue.created",
                "detected_issue_id": model.detected_issue_id,
            },
        )
        return model

    async def patch_detected_issue(
        self,
        detected_issue_id: int,
        payload: DetectedIssuePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> DetectedIssueModel:
        if not org_id:
            self._log_org_scope_miss("patch", detected_issue_id, org_id)
            raise NotFoundError("DetectedIssue not found")
        existing = await self.repository.get_by_detected_issue_id_in_org(
            detected_issue_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", detected_issue_id, org_id)
            raise NotFoundError("DetectedIssue not found")

        fragment, touched = patch_fragment_to_fhir_detected_issue(payload)
        merged = merge_patch_fragment(
            to_fhir_detected_issue(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            detected_issue_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("DetectedIssue not found")
        logger.info(
            "DetectedIssue updated",
            extra={
                "event": "detected_issue.updated",
                "detected_issue_id": detected_issue_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_detected_issue(
        self, detected_issue_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.detected_issue_belongs_to_org(
            detected_issue_id, org_id
        ):
            self._log_org_scope_miss("delete", detected_issue_id, org_id)
            raise NotFoundError("DetectedIssue not found")
        deleted = await self.repository.delete(detected_issue_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("DetectedIssue not found")
        logger.info(
            "DetectedIssue deleted",
            extra={
                "event": "detected_issue.deleted",
                "detected_issue_id": detected_issue_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "DetectedIssue", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "DetectedIssue failed base R4 validation",
                extra={
                    "event": "detected_issue.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, detected_issue_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "DetectedIssue write rejected by org scope",
            extra={
                "event": "detected_issue.org_scope_miss",
                "operation": operation,
                "detected_issue_id": detected_issue_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

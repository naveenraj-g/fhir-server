from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.risk_assessment import (
    patch_fragment_to_fhir_risk_assessment,
    payload_to_fhir_risk_assessment,
    to_fhir_risk_assessment,
    to_plain_risk_assessment,
)
from app.fhir.validation import validate_resource
from app.models.risk_assessment import RiskAssessmentModel
from app.repository.risk_assessment import RiskAssessmentRepository
from app.schemas.risk_assessment import (
    RiskAssessmentCreateSchema,
    RiskAssessmentPatchSchema,
)

logger = get_logger(__name__)


class RiskAssessmentService:
    """All RiskAssessment business logic."""

    def __init__(self, repository: RiskAssessmentRepository):
        self.repository = repository

    def _to_fhir(self, model: RiskAssessmentModel) -> dict:
        return to_fhir_risk_assessment(model)

    def _to_plain(self, model: RiskAssessmentModel) -> dict:
        return to_plain_risk_assessment(model)

    async def get_risk_assessment_scoped(
        self, risk_assessment_id: int, org_id: str | None
    ) -> RiskAssessmentModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "RiskAssessment operation requires an org-scoped token"
            )
        model = await self.repository.get_by_risk_assessment_id_in_org(
            risk_assessment_id, org_id
        )
        if not model:
            raise NotFoundError("RiskAssessment not found")
        return model

    async def list_risk_assessments(
        self,
        org_id: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        condition: str | None = None,
        performer: str | None = None,
        occurrence: date | datetime | str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[RiskAssessmentModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "RiskAssessment operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            subject=subject,
            condition=condition,
            performer=performer,
            occurrence=occurrence,
            identifier=identifier,
        )

    async def create_risk_assessment(
        self,
        payload: RiskAssessmentCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> RiskAssessmentModel:
        if not org_id:
            raise PermissionDeniedError(
                "RiskAssessment creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "RiskAssessment creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_risk_assessment(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "RiskAssessment created",
            extra={
                "event": "risk_assessment.created",
                "risk_assessment_id": model.risk_assessment_id,
            },
        )
        return model

    async def patch_risk_assessment(
        self,
        risk_assessment_id: int,
        payload: RiskAssessmentPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> RiskAssessmentModel:
        if not org_id:
            self._log_org_scope_miss("patch", risk_assessment_id, org_id)
            raise NotFoundError("RiskAssessment not found")
        existing = await self.repository.get_by_risk_assessment_id_in_org(
            risk_assessment_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", risk_assessment_id, org_id)
            raise NotFoundError("RiskAssessment not found")

        fragment, touched = patch_fragment_to_fhir_risk_assessment(payload)
        merged = merge_patch_fragment(
            to_fhir_risk_assessment(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            risk_assessment_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("RiskAssessment not found")
        logger.info(
            "RiskAssessment updated",
            extra={
                "event": "risk_assessment.updated",
                "risk_assessment_id": risk_assessment_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_risk_assessment(
        self, risk_assessment_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.risk_assessment_belongs_to_org(
            risk_assessment_id, org_id
        ):
            self._log_org_scope_miss("delete", risk_assessment_id, org_id)
            raise NotFoundError("RiskAssessment not found")
        deleted = await self.repository.delete(risk_assessment_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("RiskAssessment not found")
        logger.info(
            "RiskAssessment deleted",
            extra={
                "event": "risk_assessment.deleted",
                "risk_assessment_id": risk_assessment_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "RiskAssessment", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "RiskAssessment failed base R4 validation",
                extra={
                    "event": "risk_assessment.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, risk_assessment_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "RiskAssessment write rejected by org scope",
            extra={
                "event": "risk_assessment.org_scope_miss",
                "operation": operation,
                "risk_assessment_id": risk_assessment_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

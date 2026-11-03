from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.immunization_evaluation import (
    patch_fragment_to_fhir_immunization_evaluation,
    payload_to_fhir_immunization_evaluation,
    to_fhir_immunization_evaluation,
    to_plain_immunization_evaluation,
)
from app.fhir.validation import validate_resource
from app.models.immunization_evaluation import ImmunizationEvaluationModel
from app.repository.immunization_evaluation import ImmunizationEvaluationRepository
from app.schemas.immunization_evaluation import (
    ImmunizationEvaluationCreateSchema,
    ImmunizationEvaluationPatchSchema,
)

logger = get_logger(__name__)


class ImmunizationEvaluationService:
    """All ImmunizationEvaluation business logic."""

    def __init__(self, repository: ImmunizationEvaluationRepository):
        self.repository = repository

    def _to_fhir(self, model: ImmunizationEvaluationModel) -> dict:
        return to_fhir_immunization_evaluation(model)

    def _to_plain(self, model: ImmunizationEvaluationModel) -> dict:
        return to_plain_immunization_evaluation(model)

    async def get_immunization_evaluation_scoped(
        self, immunization_evaluation_id: int, org_id: str | None
    ) -> ImmunizationEvaluationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationEvaluation operation requires an org-scoped token"
            )
        model = await self.repository.get_by_immunization_evaluation_id_in_org(
            immunization_evaluation_id, org_id
        )
        if not model:
            raise NotFoundError("ImmunizationEvaluation not found")
        return model

    async def list_immunization_evaluations(
        self,
        org_id: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | str | None = None,
        authority: str | None = None,
        immunization_event: str | None = None,
        identifier: str | None = None,
        target_disease: str | None = None,
        dose_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[ImmunizationEvaluationModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationEvaluation operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            patient=patient,
            date_val=date_val,
            authority=authority,
            immunization_event=immunization_event,
            identifier=identifier,
            target_disease=target_disease,
            dose_status=dose_status,
        )

    async def create_immunization_evaluation(
        self,
        payload: ImmunizationEvaluationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ImmunizationEvaluationModel:
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationEvaluation creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "ImmunizationEvaluation creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_immunization_evaluation(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "ImmunizationEvaluation created",
            extra={
                "event": "immunization_evaluation.created",
                "immunization_evaluation_id": model.immunization_evaluation_id,
            },
        )
        return model

    async def patch_immunization_evaluation(
        self,
        immunization_evaluation_id: int,
        payload: ImmunizationEvaluationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ImmunizationEvaluationModel:
        if not org_id:
            self._log_org_scope_miss("patch", immunization_evaluation_id, org_id)
            raise NotFoundError("ImmunizationEvaluation not found")
        existing = await self.repository.get_by_immunization_evaluation_id_in_org(
            immunization_evaluation_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", immunization_evaluation_id, org_id)
            raise NotFoundError("ImmunizationEvaluation not found")

        fragment, touched = patch_fragment_to_fhir_immunization_evaluation(payload)
        merged = merge_patch_fragment(
            to_fhir_immunization_evaluation(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            immunization_evaluation_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("ImmunizationEvaluation not found")
        logger.info(
            "ImmunizationEvaluation updated",
            extra={
                "event": "immunization_evaluation.updated",
                "immunization_evaluation_id": immunization_evaluation_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_immunization_evaluation(
        self, immunization_evaluation_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.immunization_evaluation_belongs_to_org(
            immunization_evaluation_id, org_id
        ):
            self._log_org_scope_miss("delete", immunization_evaluation_id, org_id)
            raise NotFoundError("ImmunizationEvaluation not found")

        deleted = await self.repository.delete(immunization_evaluation_id, org_id)
        if not deleted:
            raise NotFoundError("ImmunizationEvaluation not found")
        logger.info(
            "ImmunizationEvaluation deleted",
            extra={
                "event": "immunization_evaluation.deleted",
                "immunization_evaluation_id": immunization_evaluation_id,
            },
        )

    def _log_org_scope_miss(
        self, action: str, immunization_evaluation_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "ImmunizationEvaluation org scope mismatch",
            extra={
                "event": "immunization_evaluation.org_scope_mismatch",
                "action": action,
                "immunization_evaluation_id": immunization_evaluation_id,
                "token_org_id": org_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "ImmunizationEvaluation", fhir_resource, org_id=org_id
        )
        if errors:
            raise FhirValidationError(errors)

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication_knowledge import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication_knowledge,
    payload_to_fhir_medication_knowledge,
    to_fhir_medication_knowledge,
    to_plain_medication_knowledge,
)
from app.fhir.validation import validate_resource
from app.models.medication_knowledge import (
    MedicationKnowledgeModel,
    MedicationKnowledgeStatus,
)
from app.repository.medication_knowledge import MedicationKnowledgeRepository
from app.schemas.medication_knowledge import (
    MedicationKnowledgeCreateSchema,
    MedicationKnowledgePatchSchema,
)

logger = get_logger(__name__)


class MedicationKnowledgeService:
    """All MedicationKnowledge business logic."""

    def __init__(self, repository: MedicationKnowledgeRepository):
        self.repository = repository

    def _to_fhir(self, model: MedicationKnowledgeModel) -> dict:
        return to_fhir_medication_knowledge(model)

    def _to_plain(self, model: MedicationKnowledgeModel) -> dict:
        return to_plain_medication_knowledge(model)

    async def get_medication_knowledge_scoped(
        self, medication_knowledge_id: int, org_id: str | None
    ) -> MedicationKnowledgeModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationKnowledge operation requires an org-scoped token"
            )
        model = await self.repository.get_by_medication_knowledge_id_in_org(
            medication_knowledge_id, org_id
        )
        if not model:
            raise NotFoundError("MedicationKnowledge not found")
        return model

    async def list_medication_knowledge(
        self,
        org_id: str | None = None,
        code: str | None = None,
        status: str | MedicationKnowledgeStatus | None = None,
        manufacturer: str | None = None,
        dose_form: str | None = None,
        monitoring_program: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MedicationKnowledgeModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationKnowledge operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            code=code,
            status=status,
            manufacturer=manufacturer,
            dose_form=dose_form,
            monitoring_program=monitoring_program,
            ingredient=ingredient,
            ingredient_code=ingredient_code,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_medication_knowledge(
        self,
        payload: MedicationKnowledgeCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationKnowledgeModel:
        if not org_id:
            raise PermissionDeniedError(
                "MedicationKnowledge creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "MedicationKnowledge creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_medication_knowledge(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "MedicationKnowledge created",
            extra={
                "event": "medication_knowledge.created",
                "medication_knowledge_id": model.medication_knowledge_id,
            },
        )
        return model

    async def patch_medication_knowledge(
        self,
        medication_knowledge_id: int,
        payload: MedicationKnowledgePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationKnowledgeModel:
        if not org_id:
            self._log_org_scope_miss("patch", medication_knowledge_id, org_id)
            raise NotFoundError("MedicationKnowledge not found")
        existing = await self.repository.get_by_medication_knowledge_id_in_org(
            medication_knowledge_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", medication_knowledge_id, org_id)
            raise NotFoundError("MedicationKnowledge not found")

        fragment, touched = patch_fragment_to_fhir_medication_knowledge(payload)
        merged = merge_patch_fragment(
            to_fhir_medication_knowledge(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            medication_knowledge_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("MedicationKnowledge not found")
        logger.info(
            "MedicationKnowledge updated",
            extra={
                "event": "medication_knowledge.updated",
                "medication_knowledge_id": medication_knowledge_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication_knowledge(
        self, medication_knowledge_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.medication_knowledge_belongs_to_org(
            medication_knowledge_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_knowledge_id, org_id)
            raise NotFoundError("MedicationKnowledge not found")
        deleted = await self.repository.delete(medication_knowledge_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("MedicationKnowledge not found")
        logger.info(
            "MedicationKnowledge deleted",
            extra={
                "event": "medication_knowledge.deleted",
                "medication_knowledge_id": medication_knowledge_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "MedicationKnowledge", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "MedicationKnowledge failed base R4 validation",
                extra={
                    "event": "medication_knowledge.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, medication_knowledge_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "MedicationKnowledge write rejected by org scope",
            extra={
                "event": "medication_knowledge.org_scope_miss",
                "operation": operation,
                "medication_knowledge_id": medication_knowledge_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

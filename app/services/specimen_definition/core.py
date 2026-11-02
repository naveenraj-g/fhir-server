from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.specimen_definition import (
    patch_fragment_to_fhir_specimen_definition,
    payload_to_fhir_specimen_definition,
    to_fhir_specimen_definition,
    to_plain_specimen_definition,
)
from app.fhir.validation import validate_resource
from app.models.specimen_definition import SpecimenDefinitionModel
from app.repository.specimen_definition import SpecimenDefinitionRepository
from app.schemas.specimen_definition import (
    SpecimenDefinitionCreateSchema,
    SpecimenDefinitionPatchSchema,
)

logger = get_logger(__name__)


class SpecimenDefinitionService:
    """All SpecimenDefinition business logic."""

    def __init__(self, repository: SpecimenDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, model: SpecimenDefinitionModel) -> dict:
        return to_fhir_specimen_definition(model)

    def _to_plain(self, model: SpecimenDefinitionModel) -> dict:
        return to_plain_specimen_definition(model)

    async def get_specimen_definition_scoped(
        self, specimen_definition_id: int, org_id: str | None
    ) -> SpecimenDefinitionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "SpecimenDefinition operation requires an org-scoped token"
            )
        model = await self.repository.get_by_specimen_definition_id_in_org(
            specimen_definition_id, org_id
        )
        if not model:
            raise NotFoundError("SpecimenDefinition not found")
        return model

    async def list_specimen_definitions(
        self,
        org_id: str | None = None,
        identifier: str | None = None,
        type_collected: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[SpecimenDefinitionModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "SpecimenDefinition operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            limit=limit,
            offset=offset,
            sort=sort,
            identifier=identifier,
            type_collected=type_collected,
        )

    async def create_specimen_definition(
        self,
        payload: SpecimenDefinitionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> SpecimenDefinitionModel:
        if not org_id:
            raise PermissionDeniedError(
                "SpecimenDefinition creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "SpecimenDefinition creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_specimen_definition(payload), org_id
        )
        model = await self.repository.create(
            payload, org_id, created_by
        )
        logger.info(
            "SpecimenDefinition created",
            extra={
                "event": "specimen_definition.created",
                "specimen_definition_id": model.specimen_definition_id,
            },
        )
        return model

    async def patch_specimen_definition(
        self,
        specimen_definition_id: int,
        payload: SpecimenDefinitionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> SpecimenDefinitionModel:
        if not org_id:
            self._log_org_scope_miss("patch", specimen_definition_id, org_id)
            raise NotFoundError("SpecimenDefinition not found")
        existing = await self.repository.get_by_specimen_definition_id_in_org(
            specimen_definition_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", specimen_definition_id, org_id)
            raise NotFoundError("SpecimenDefinition not found")

        fragment, touched = patch_fragment_to_fhir_specimen_definition(payload)
        merged = merge_patch_fragment(
            to_fhir_specimen_definition(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch(
            specimen_definition_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("SpecimenDefinition not found")
        logger.info(
            "SpecimenDefinition updated",
            extra={
                "event": "specimen_definition.updated",
                "specimen_definition_id": specimen_definition_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_specimen_definition(
        self, specimen_definition_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.specimen_definition_belongs_to_org(
            specimen_definition_id, org_id
        ):
            self._log_org_scope_miss("delete", specimen_definition_id, org_id)
            raise NotFoundError("SpecimenDefinition not found")
        deleted = await self.repository.delete(specimen_definition_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("SpecimenDefinition not found")
        logger.info(
            "SpecimenDefinition deleted",
            extra={
                "event": "specimen_definition.deleted",
                "specimen_definition_id": specimen_definition_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "SpecimenDefinition", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "SpecimenDefinition failed base R4 validation",
                extra={
                    "event": "specimen_definition.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, specimen_definition_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "SpecimenDefinition write rejected by org scope",
            extra={
                "event": "specimen_definition.org_scope_miss",
                "operation": operation,
                "specimen_definition_id": specimen_definition_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

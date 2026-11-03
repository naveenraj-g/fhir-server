from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.measure import (
    patch_fragment_to_fhir_measure,
    payload_to_fhir_measure,
    to_fhir_measure,
    to_plain_measure,
)
from app.fhir.validation import validate_resource
from app.models.measure import MeasureModel
from app.repository.measure import MeasureRepository
from app.schemas.measure import (
    MeasureCreateSchema,
    MeasurePatchSchema,
)

logger = get_logger(__name__)


class MeasureService:
    """All Measure business logic."""

    def __init__(self, repository: MeasureRepository):
        self.repository = repository

    def _to_fhir(self, model: MeasureModel) -> dict:
        return to_fhir_measure(model)

    def _to_plain(self, model: MeasureModel) -> dict:
        return to_plain_measure(model)

    async def get_measure_scoped(
        self, measure_id: int, org_id: str | None
    ) -> MeasureModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "Measure operation requires an org-scoped token"
            )
        model = await self.repository.get_by_measure_id_in_org(measure_id, org_id)
        if not model:
            raise NotFoundError("Measure not found")
        return model

    async def list_measures(
        self,
        org_id: str | None = None,
        url: str | None = None,
        identifier: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        publisher: str | None = None,
        description: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MeasureModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Measure operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            url=url,
            identifier=identifier,
            name=name,
            title=title,
            status=status,
            publisher=publisher,
            description=description,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_measure(
        self,
        payload: MeasureCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MeasureModel:
        if not org_id:
            raise PermissionDeniedError(
                "Measure creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Measure creation requires an authenticated actor"
            )

        await self._validate_base_r4(payload_to_fhir_measure(payload), org_id)
        model = await self.repository.create(payload, org_id, created_by)
        logger.info(
            "Measure created",
            extra={
                "event": "measure.created",
                "measure_id": model.measure_id,
            },
        )
        return model

    async def patch_measure(
        self,
        measure_id: int,
        payload: MeasurePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MeasureModel:
        if not org_id:
            self._log_org_scope_miss("patch", measure_id, org_id)
            raise NotFoundError("Measure not found")
        existing = await self.repository.get_by_measure_id_in_org(
            measure_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", measure_id, org_id)
            raise NotFoundError("Measure not found")

        fragment, touched = patch_fragment_to_fhir_measure(payload)
        merged = merge_patch_fragment(
            to_fhir_measure(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch(
            measure_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Measure not found")
        logger.info(
            "Measure updated",
            extra={
                "event": "measure.updated",
                "measure_id": measure_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_measure(
        self, measure_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.measure_belongs_to_org(
            measure_id, org_id
        ):
            self._log_org_scope_miss("delete", measure_id, org_id)
            raise NotFoundError("Measure not found")
        deleted = await self.repository.delete(measure_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Measure not found")
        logger.info(
            "Measure deleted",
            extra={
                "event": "measure.deleted",
                "measure_id": measure_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource("Measure", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Measure failed base R4 validation",
                extra={
                    "event": "measure.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, measure_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Measure write rejected by org scope",
            extra={
                "event": "measure.org_scope_miss",
                "operation": operation,
                "measure_id": measure_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

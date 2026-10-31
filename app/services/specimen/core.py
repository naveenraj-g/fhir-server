from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.specimen import (
    merge_patch_fragment,
    patch_fragment_to_fhir_specimen,
    payload_to_fhir_specimen,
    to_fhir_specimen,
    to_plain_specimen,
)
from app.fhir.validation import validate_resource
from app.models.specimen import SpecimenModel
from app.repository.specimen import SpecimenRepository
from app.schemas.specimen import SpecimenCreateSchema, SpecimenPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Specimen business logic."""

    def __init__(self, repository: SpecimenRepository):
        self.repository = repository

    def _to_fhir(self, specimen: SpecimenModel) -> dict:
        return to_fhir_specimen(specimen)

    def _to_plain(self, specimen: SpecimenModel) -> dict:
        return to_plain_specimen(specimen)

    async def get_specimen_scoped(
        self, specimen_id: int, org_id: str | None
    ) -> SpecimenModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Specimen operation requires an org-scoped token")
        specimen = await self.repository.get_by_specimen_id_in_org(specimen_id, org_id)
        if not specimen:
            raise NotFoundError("Specimen not found")
        return specimen

    async def list_specimens(
        self,
        org_id: str | None = None,
        status: str | None = None,
        type: str | None = None,
        subject: str | None = None,
        accession_identifier: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[SpecimenModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("Specimen operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            type=type,
            subject=subject,
            accession_identifier=accession_identifier,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_specimen(
        self,
        payload: SpecimenCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> SpecimenModel:
        if not org_id:
            raise PermissionDeniedError("Specimen creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("Specimen creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_specimen(payload), org_id)
        specimen = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Specimen created",
            extra={"event": "specimen.created", "specimen_id": specimen.specimen_id},
        )
        return specimen

    async def patch_specimen(
        self,
        specimen_id: int,
        payload: SpecimenPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> SpecimenModel:
        if not org_id:
            self._log_org_scope_miss("patch", specimen_id, org_id)
            raise NotFoundError("Specimen not found")
        existing = await self.repository.get_by_specimen_id_in_org(specimen_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", specimen_id, org_id)
            raise NotFoundError("Specimen not found")

        fragment, touched = patch_fragment_to_fhir_specimen(payload)
        merged = merge_patch_fragment(to_fhir_specimen(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            specimen_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Specimen not found")
        logger.info(
            "Specimen updated",
            extra={
                "event": "specimen.updated",
                "specimen_id": specimen_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_specimen(self, specimen_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.specimen_belongs_to_org(specimen_id, org_id):
            self._log_org_scope_miss("delete", specimen_id, org_id)
            raise NotFoundError("Specimen not found")
        deleted = await self.repository.delete(specimen_id)
        if not deleted:
            raise NotFoundError("Specimen not found")
        logger.info(
            "Specimen deleted",
            extra={"event": "specimen.deleted", "specimen_id": specimen_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Specimen", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Specimen failed base R4 validation",
                extra={"event": "specimen.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, specimen_id: int, org_id: str | None) -> None:
        logger.warning(
            "Specimen write rejected by org scope",
            extra={
                "event": "specimen.org_scope_miss",
                "operation": operation,
                "specimen_id": specimen_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.encounter import (
    merge_patch_fragment,
    patch_fragment_to_fhir_encounter,
    payload_to_fhir_encounter,
    to_fhir_encounter,
    to_plain_encounter,
)
from app.fhir.validation import validate_resource
from app.models.encounter import EncounterModel, EncounterStatus as EncounterStatusModel
from app.repository.encounter import EncounterRepository
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema
from app.schemas.enums import EncounterStatus

logger = get_logger(__name__)


class _CoreMixin:
    """All Encounter business logic. Like every other auth-rollout
    resource, Encounter has no standalone sub-resource endpoints and no
    separate scalar-only vs. full create/patch split — see
    EncounterCreateSchema's docstring. Auth is identical to every other
    auth-rollout resource: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass."""

    def __init__(self, repository: EncounterRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, encounter: EncounterModel) -> dict:
        return to_fhir_encounter(encounter)

    def _to_plain(self, encounter: EncounterModel) -> dict:
        return to_plain_encounter(encounter)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_encounter_scoped(self, encounter_id: int, org_id: str | None) -> EncounterModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it
        belongs to a different org."""
        if not org_id:
            raise PermissionDeniedError("Encounter operation requires an org-scoped token")
        row = await self.repository.get_by_encounter_id_in_org(encounter_id, org_id)
        if not row:
            raise NotFoundError("Encounter not found")
        return row

    async def list_encounters(
        self,
        org_id: str | None = None,
        status: EncounterStatus | None = None,
        identifier: str | None = None,
        subject: str | None = None,
        class_code: str | None = None,
        type_code: str | None = None,
        service_provider: str | None = None,
        part_of: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[EncounterModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("Encounter operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=EncounterStatusModel[status.name] if status else None,
            identifier=identifier,
            subject=subject,
            class_code=class_code,
            type_code=type_code,
            service_provider=service_provider,
            part_of=part_of,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_encounter(
        self,
        payload: EncounterCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> EncounterModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass."""
        if not org_id:
            raise PermissionDeniedError("Encounter creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_encounter(payload), org_id)
        encounter = await self.repository.create_full(payload, org_id, created_by)
        logger.info("Encounter created", extra={"event": "encounter.created", "encounter_id": encounter.encounter_id})
        return encounter

    async def patch_encounter(
        self,
        encounter_id: int,
        payload: EncounterPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> EncounterModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass:
        a missing org_id or an encounter belonging to a different org
        both raise NotFoundError (404), never 403."""
        if not org_id:
            self._log_org_scope_miss("patch", encounter_id, org_id)
            raise NotFoundError("Encounter not found")
        existing = await self.repository.get_by_encounter_id_in_org(encounter_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", encounter_id, org_id)
            raise NotFoundError("Encounter not found")

        fragment, touched = patch_fragment_to_fhir_encounter(payload)
        merged = merge_patch_fragment(to_fhir_encounter(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(encounter_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Encounter not found")
        logger.info(
            "Encounter updated",
            extra={
                "event": "encounter.updated",
                "encounter_id": encounter_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_encounter(self, encounter_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_encounter."""
        if not org_id or not await self.repository.encounter_belongs_to_org(encounter_id, org_id):
            self._log_org_scope_miss("delete", encounter_id, org_id)
            raise NotFoundError("Encounter not found")
        deleted = await self.repository.delete(encounter_id)
        if not deleted:
            raise NotFoundError("Encounter not found")
        logger.info("Encounter deleted", extra={"event": "encounter.deleted", "encounter_id": encounter_id})

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Encounter", fhir_resource, org_id=org_id)
        if errors:
            logger.warning("Encounter failed base R4 validation", extra={"event": "encounter.base_r4_invalid", "errors": errors})
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(operation: str, encounter_id: int, org_id: str | None) -> None:
        logger.warning(
            "Encounter write rejected by org scope",
            extra={
                "event": "encounter.org_scope_miss",
                "operation": operation,
                "encounter_id": encounter_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

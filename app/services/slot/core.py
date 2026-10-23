from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.slot import (
    merge_patch_fragment,
    patch_fragment_to_fhir_slot,
    payload_to_fhir_slot,
    to_fhir_slot,
    to_plain_slot,
)
from app.fhir.validation import validate_resource
from app.models.slot import SlotModel, SlotStatus as SlotStatusModel
from app.repository.slot import SlotRepository
from app.schemas.enums import SlotStatus
from app.schemas.slot import SlotCreateSchema, SlotPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Slot business logic. Like Schedule, Slot has no standalone
    sub-resource endpoints and no separate scalar-only vs. full
    create/patch split — see SlotCreateSchema's docstring. Auth is
    identical to Schedule's: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: SlotRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, slot: SlotModel) -> dict:
        return to_fhir_slot(slot)

    def _to_plain(self, slot: SlotModel) -> dict:
        return to_plain_slot(slot)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_slot_scoped(self, slot_id: int, org_id: str | None) -> SlotModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Slot operation requires an org-scoped token")
        slot = await self.repository.get_by_slot_id_in_org(slot_id, org_id)
        if not slot:
            raise NotFoundError("Slot not found")
        return slot

    async def list_slots(
        self,
        org_id: str | None = None,
        status: SlotStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        schedule: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[SlotModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_slot_scoped(). `status`, if given, is the
        Pydantic (hyphenated) enum — converted to the model-layer
        (underscore) enum by member name before reaching the repository,
        same conversion app.repository.slot.full._model_status() does on
        write."""
        if not org_id:
            raise PermissionDeniedError("Slot operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=SlotStatusModel[status.name] if status else None,
            identifier=identifier,
            service_category=service_category,
            service_type=service_type,
            specialty=specialty,
            schedule=schedule,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_slot(
        self,
        payload: SlotCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> SlotModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Slot at all."""
        if not org_id:
            raise PermissionDeniedError("Slot creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_slot(payload), org_id)
        slot = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Slot created", extra={"event": "slot.created", "slot_id": slot.slot_id}
        )
        return slot

    async def patch_slot(
        self,
        slot_id: int,
        payload: SlotPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> SlotModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a slot belonging to a different org both raise
        NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        patch_fragment_to_fhir_slot()'s docstring."""
        if not org_id:
            self._log_org_scope_miss("patch", slot_id, org_id)
            raise NotFoundError("Slot not found")
        existing = await self.repository.get_by_slot_id_in_org(slot_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", slot_id, org_id)
            raise NotFoundError("Slot not found")

        fragment, touched = patch_fragment_to_fhir_slot(payload)
        merged = merge_patch_fragment(to_fhir_slot(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(slot_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Slot not found")
        logger.info(
            "Slot updated",
            extra={
                "event": "slot.updated",
                "slot_id": slot_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_slot(self, slot_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_slot."""
        if not org_id or not await self.repository.slot_belongs_to_org(
            slot_id, org_id
        ):
            self._log_org_scope_miss("delete", slot_id, org_id)
            raise NotFoundError("Slot not found")
        deleted = await self.repository.delete(slot_id)
        if not deleted:
            raise NotFoundError("Slot not found")
        logger.info(
            "Slot deleted", extra={"event": "slot.deleted", "slot_id": slot_id}
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails
        validation against the most specific applicable layer of the
        base -> country -> organization profile chain — see
        app.services.organization.core._CoreMixin._validate_base_r4's
        docstring for the full reasoning (identical here; validate_resource()
        is already resource-agnostic)."""
        errors = await validate_resource("Slot", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Slot failed base R4 validation",
                extra={"event": "slot.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(operation: str, slot_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such slot" — so this log
        line is the only place the distinction is recorded."""
        logger.warning(
            "Slot write rejected by org scope",
            extra={
                "event": "slot.org_scope_miss",
                "operation": operation,
                "slot_id": slot_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

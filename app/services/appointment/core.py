from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.appointment import (
    merge_patch_fragment,
    patch_fragment_to_fhir_appointment,
    payload_to_fhir_appointment,
    to_fhir_appointment,
    to_plain_appointment,
)
from app.fhir.validation import validate_resource
from app.models.appointment import AppointmentModel, AppointmentStatus as AppointmentStatusModel
from app.repository.appointment import AppointmentRepository
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema
from app.schemas.enums import AppointmentStatus

logger = get_logger(__name__)


class _CoreMixin:
    """All Appointment business logic. Like Schedule/Slot, Appointment has
    no standalone sub-resource endpoints and no separate scalar-only vs.
    full create/patch split — see AppointmentCreateSchema's docstring. Auth
    is identical to Slot's: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: AppointmentRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, appointment: AppointmentModel) -> dict:
        return to_fhir_appointment(appointment)

    def _to_plain(self, appointment: AppointmentModel) -> dict:
        return to_plain_appointment(appointment)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_appointment_scoped(
        self, appointment_id: int, org_id: str | None
    ) -> AppointmentModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Appointment operation requires an org-scoped token")
        appointment = await self.repository.get_by_appointment_id_in_org(appointment_id, org_id)
        if not appointment:
            raise NotFoundError("Appointment not found")
        return appointment

    async def list_appointments(
        self,
        org_id: str | None = None,
        status: AppointmentStatus | None = None,
        identifier: str | None = None,
        service_category: str | None = None,
        service_type: str | None = None,
        specialty: str | None = None,
        actor: str | None = None,
        slot: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AppointmentModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_appointment_scoped(). `status`, if given, is the
        Pydantic (hyphenated) enum — converted to the model-layer
        (underscore) enum by member name before reaching the repository,
        same conversion app.repository.appointment.full._model_status()
        does on write."""
        if not org_id:
            raise PermissionDeniedError("Appointment operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=AppointmentStatusModel[status.name] if status else None,
            identifier=identifier,
            service_category=service_category,
            service_type=service_type,
            specialty=specialty,
            actor=actor,
            slot=slot,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_appointment(
        self,
        payload: AppointmentCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> AppointmentModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create an Appointment at all."""
        if not org_id:
            raise PermissionDeniedError("Appointment creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_appointment(payload), org_id)
        appointment = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Appointment created",
            extra={"event": "appointment.created", "appointment_id": appointment.appointment_id},
        )
        return appointment

    async def patch_appointment(
        self,
        appointment_id: int,
        payload: AppointmentPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> AppointmentModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or an appointment belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        patch_fragment_to_fhir_appointment()'s docstring."""
        if not org_id:
            self._log_org_scope_miss("patch", appointment_id, org_id)
            raise NotFoundError("Appointment not found")
        existing = await self.repository.get_by_appointment_id_in_org(appointment_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", appointment_id, org_id)
            raise NotFoundError("Appointment not found")

        fragment, touched = patch_fragment_to_fhir_appointment(payload)
        merged = merge_patch_fragment(to_fhir_appointment(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(appointment_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Appointment not found")
        logger.info(
            "Appointment updated",
            extra={
                "event": "appointment.updated",
                "appointment_id": appointment_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_appointment(self, appointment_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_appointment."""
        if not org_id or not await self.repository.appointment_belongs_to_org(
            appointment_id, org_id
        ):
            self._log_org_scope_miss("delete", appointment_id, org_id)
            raise NotFoundError("Appointment not found")
        deleted = await self.repository.delete(appointment_id)
        if not deleted:
            raise NotFoundError("Appointment not found")
        logger.info(
            "Appointment deleted",
            extra={"event": "appointment.deleted", "appointment_id": appointment_id},
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
        errors = await validate_resource("Appointment", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Appointment failed base R4 validation",
                extra={"event": "appointment.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(operation: str, appointment_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such appointment" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "Appointment write rejected by org scope",
            extra={
                "event": "appointment.org_scope_miss",
                "operation": operation,
                "appointment_id": appointment_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

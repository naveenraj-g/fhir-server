from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.appointment_response import (
    merge_patch_fragment,
    patch_fragment_to_fhir_appointment_response,
    payload_to_fhir_appointment_response,
    to_fhir_appointment_response,
    to_plain_appointment_response,
)
from app.fhir.validation import validate_resource
from app.models.appointment_response import (
    AppointmentResponseModel,
    AppointmentResponseParticipantStatus as AppointmentResponseParticipantStatusModel,
)
from app.repository.appointment_response import AppointmentResponseRepository
from app.schemas.appointment_response import (
    AppointmentResponseCreateSchema,
    AppointmentResponsePatchSchema,
)
from app.schemas.enums import AppointmentResponseParticipantStatus

logger = get_logger(__name__)


class _CoreMixin:
    """All AppointmentResponse business logic. Like Schedule/Slot/
    Appointment, AppointmentResponse has no standalone sub-resource
    endpoints and no separate scalar-only vs. full create/patch split —
    see AppointmentResponseCreateSchema's docstring. Auth is identical to
    Appointment's: org_id comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor."""

    def __init__(self, repository: AppointmentResponseRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, appointment_response: AppointmentResponseModel) -> dict:
        return to_fhir_appointment_response(appointment_response)

    def _to_plain(self, appointment_response: AppointmentResponseModel) -> dict:
        return to_plain_appointment_response(appointment_response)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_appointment_response_scoped(
        self, appointment_response_id: int, org_id: str | None
    ) -> AppointmentResponseModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "AppointmentResponse operation requires an org-scoped token"
            )
        row = await self.repository.get_by_appointment_response_id_in_org(
            appointment_response_id, org_id
        )
        if not row:
            raise NotFoundError("AppointmentResponse not found")
        return row

    async def list_appointment_responses(
        self,
        org_id: str | None = None,
        identifier: str | None = None,
        appointment: str | None = None,
        actor: str | None = None,
        part_status: AppointmentResponseParticipantStatus | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AppointmentResponseModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_appointment_response_scoped(). `part_status`, if
        given, is the Pydantic (hyphenated) enum — converted to the
        model-layer (underscore) enum by member name before reaching the
        repository, same conversion
        app.repository.appointment_response.full._model_participant_status()
        does on write."""
        if not org_id:
            raise PermissionDeniedError(
                "AppointmentResponse operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            identifier=identifier,
            appointment=appointment,
            actor=actor,
            part_status=(
                AppointmentResponseParticipantStatusModel[part_status.name]
                if part_status
                else None
            ),
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_appointment_response(
        self,
        payload: AppointmentResponseCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> AppointmentResponseModel:
        """org_id comes from the verified JWT's actor.org_id, not a
        client-supplied field — there is no bypass, so an org-less/
        platform token cannot create an AppointmentResponse at all."""
        if not org_id:
            raise PermissionDeniedError(
                "AppointmentResponse creation requires an org-scoped token"
            )
        await self._validate_base_r4(
            payload_to_fhir_appointment_response(payload), org_id
        )
        appointment_response = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "AppointmentResponse created",
            extra={
                "event": "appointment_response.created",
                "appointment_response_id": appointment_response.appointment_response_id,
            },
        )
        return appointment_response

    async def patch_appointment_response(
        self,
        appointment_response_id: int,
        payload: AppointmentResponsePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> AppointmentResponseModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a row belonging to a different org both raise
        NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        patch_fragment_to_fhir_appointment_response()'s docstring."""
        if not org_id:
            self._log_org_scope_miss("patch", appointment_response_id, org_id)
            raise NotFoundError("AppointmentResponse not found")
        existing = await self.repository.get_by_appointment_response_id_in_org(
            appointment_response_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", appointment_response_id, org_id)
            raise NotFoundError("AppointmentResponse not found")

        fragment, touched = patch_fragment_to_fhir_appointment_response(payload)
        merged = merge_patch_fragment(
            to_fhir_appointment_response(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            appointment_response_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("AppointmentResponse not found")
        logger.info(
            "AppointmentResponse updated",
            extra={
                "event": "appointment_response.updated",
                "appointment_response_id": appointment_response_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_appointment_response(
        self, appointment_response_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_appointment_response."""
        if not org_id or not await self.repository.appointment_response_belongs_to_org(
            appointment_response_id, org_id
        ):
            self._log_org_scope_miss("delete", appointment_response_id, org_id)
            raise NotFoundError("AppointmentResponse not found")
        deleted = await self.repository.delete(appointment_response_id)
        if not deleted:
            raise NotFoundError("AppointmentResponse not found")
        logger.info(
            "AppointmentResponse deleted",
            extra={
                "event": "appointment_response.deleted",
                "appointment_response_id": appointment_response_id,
            },
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
        errors = await validate_resource(
            "AppointmentResponse", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "AppointmentResponse failed base R4 validation",
                extra={"event": "appointment_response.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, appointment_response_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such appointment
        response" — so this log line is the only place the distinction is
        recorded."""
        logger.warning(
            "AppointmentResponse write rejected by org scope",
            extra={
                "event": "appointment_response.org_scope_miss",
                "operation": operation,
                "appointment_response_id": appointment_response_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication_request import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication_request,
    payload_to_fhir_medication_request,
    to_fhir_medication_request,
    to_plain_medication_request,
)
from app.fhir.validation import validate_resource
from app.models.medication_request import (
    MedicationRequestIntent as MedicationRequestIntentModel,
    MedicationRequestModel,
    MedicationRequestStatus as MedicationRequestStatusModel,
)
from app.repository.medication_request import MedicationRequestRepository
from app.schemas.enums import MedicationRequestIntent, MedicationRequestStatus
from app.schemas.medication_request import MedicationRequestCreateSchema, MedicationRequestPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All MedicationRequest business logic. Auth matches Questionnaire/
    QuestionnaireResponse/ServiceRequest: tenant scoping comes from the
    verified JWT's activeOrganizationId claim (actor.org_id), never a
    client-suppliable field, and there's no org-less/super-admin bypass —
    every operation requires an org-scoped actor. `user_id` is a
    plain, gateway-forwarded field."""

    def __init__(self, repository: MedicationRequestRepository):
        self.repository = repository

    def _to_fhir(self, medication_request: MedicationRequestModel) -> dict:
        return to_fhir_medication_request(medication_request)

    def _to_plain(self, medication_request: MedicationRequestModel) -> dict:
        return to_plain_medication_request(medication_request)

    async def get_medication_request_scoped(
        self, medication_request_id: int, org_id: str | None
    ) -> MedicationRequestModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("MedicationRequest operation requires an org-scoped token")
        medication_request = await self.repository.get_by_medication_request_id_in_org(
            medication_request_id, org_id
        )
        if not medication_request:
            raise NotFoundError("MedicationRequest not found")
        return medication_request

    async def list_medication_requests(
        self,
        org_id: str | None = None,
        status: MedicationRequestStatus | None = None,
        intent: MedicationRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[MedicationRequestModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_medication_request_scoped()."""
        if not org_id:
            raise PermissionDeniedError("MedicationRequest operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=MedicationRequestStatusModel[status.name] if status else None,
            intent=MedicationRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_medication_request(
        self,
        payload: MedicationRequestCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationRequestModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a MedicationRequest at all."""
        if not org_id:
            raise PermissionDeniedError("MedicationRequest creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_medication_request(payload), org_id)
        medication_request = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "MedicationRequest created",
            extra={"event": "medication_request.created", "medication_request_id": medication_request.medication_request_id},
        )
        return medication_request

    async def patch_medication_request(
        self,
        medication_request_id: int,
        payload: MedicationRequestPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationRequestModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a resource belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id:
            self._log_org_scope_miss("patch", medication_request_id, org_id)
            raise NotFoundError("MedicationRequest not found")
        existing = await self.repository.get_by_medication_request_id_in_org(medication_request_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", medication_request_id, org_id)
            raise NotFoundError("MedicationRequest not found")

        fragment, touched = patch_fragment_to_fhir_medication_request(payload)
        merged = merge_patch_fragment(to_fhir_medication_request(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(medication_request_id, payload, updated_by)
        if not updated:
            raise NotFoundError("MedicationRequest not found")
        logger.info(
            "MedicationRequest updated",
            extra={
                "event": "medication_request.updated",
                "medication_request_id": medication_request_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication_request(self, medication_request_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_medication_request."""
        if not org_id or not await self.repository.medication_request_belongs_to_org(
            medication_request_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_request_id, org_id)
            raise NotFoundError("MedicationRequest not found")
        deleted = await self.repository.delete(medication_request_id)
        if not deleted:
            raise NotFoundError("MedicationRequest not found")
        logger.info(
            "MedicationRequest deleted",
            extra={"event": "medication_request.deleted", "medication_request_id": medication_request_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("MedicationRequest", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "MedicationRequest failed base R4 validation",
                extra={"event": "medication_request.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, medication_request_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such resource" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "MedicationRequest write rejected by org scope",
            extra={
                "event": "medication_request.org_scope_miss",
                "operation": operation,
                "medication_request_id": medication_request_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

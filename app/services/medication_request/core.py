from app.core.logging import get_logger
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
    """All MedicationRequest business logic. Default (gateway-trusted)
    pattern — same as QuestionnaireResponse/ServiceRequest: no org-scoped
    existence check or ownership enforcement at all."""

    def __init__(self, repository: MedicationRequestRepository):
        self.repository = repository

    def _to_fhir(self, medication_request: MedicationRequestModel) -> dict:
        return to_fhir_medication_request(medication_request)

    def _to_plain(self, medication_request: MedicationRequestModel) -> dict:
        return to_plain_medication_request(medication_request)

    async def get_by_medication_request_id(self, medication_request_id: int) -> MedicationRequestModel:
        medication_request = await self.repository.get_by_medication_request_id(medication_request_id)
        if not medication_request:
            raise NotFoundError("MedicationRequest not found")
        return medication_request

    async def get_me(
        self,
        user_id: str,
        tenant_id: str | None = None,
        status: MedicationRequestStatus | None = None,
        intent: MedicationRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[MedicationRequestModel], int | None]:
        return await self.repository.get_me(
            user_id=user_id,
            tenant_id=tenant_id,
            status=MedicationRequestStatusModel[status.name] if status else None,
            intent=MedicationRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_medication_requests(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: MedicationRequestStatus | None = None,
        intent: MedicationRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[MedicationRequestModel], int | None]:
        return await self.repository.list(
            tenant_id=tenant_id,
            user_id=user_id,
            status=MedicationRequestStatusModel[status.name] if status else None,
            intent=MedicationRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_medication_request(self, payload: MedicationRequestCreateSchema) -> MedicationRequestModel:
        await self._validate_base_r4(payload_to_fhir_medication_request(payload), payload.tenant_id)
        medication_request = await self.repository.create_full(payload)
        logger.info(
            "MedicationRequest created",
            extra={"event": "medication_request.created", "medication_request_id": medication_request.medication_request_id},
        )
        return medication_request

    async def patch_medication_request(
        self, medication_request_id: int, payload: MedicationRequestPatchSchema
    ) -> MedicationRequestModel:
        existing = await self.repository.get_by_medication_request_id(medication_request_id)
        if not existing:
            raise NotFoundError("MedicationRequest not found")

        fragment, touched = patch_fragment_to_fhir_medication_request(payload)
        merged = merge_patch_fragment(to_fhir_medication_request(existing), fragment, touched)
        await self._validate_base_r4(merged, existing.tenant_id)

        updated = await self.repository.patch_full(medication_request_id, payload)
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

    async def delete_medication_request(self, medication_request_id: int) -> None:
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

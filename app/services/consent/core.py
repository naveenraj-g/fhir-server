from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.consent import (
    merge_patch_fragment,
    patch_fragment_to_fhir_consent,
    payload_to_fhir_consent,
    to_fhir_consent,
    to_plain_consent,
)
from app.fhir.validation import validate_resource
from app.models.consent import ConsentModel, ConsentStatus
from app.repository.consent import ConsentRepository
from app.schemas.consent import ConsentCreateSchema, ConsentPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Consent business logic."""

    def __init__(self, repository: ConsentRepository):
        self.repository = repository

    def _to_fhir(self, consent: ConsentModel) -> dict:
        return to_fhir_consent(consent)

    def _to_plain(self, consent: ConsentModel) -> dict:
        return to_plain_consent(consent)

    async def get_consent_scoped(
        self, consent_id: int, org_id: str | None
    ) -> ConsentModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Consent operation requires an org-scoped token"
            )
        consent = await self.repository.get_by_consent_id_in_org(
            consent_id, org_id
        )
        if not consent:
            raise NotFoundError("Consent not found")
        return consent

    async def list_consents(
        self,
        org_id: str | None = None,
        status: str | ConsentStatus | None = None,
        scope: str | None = None,
        category: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        period_from: date | datetime | None = None,
        period_to: date | datetime | None = None,
        actor: str | None = None,
        action: str | None = None,
        purpose: str | None = None,
        data: str | None = None,
        source_reference: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ConsentModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Consent operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=status,
            scope=scope,
            category=category,
            patient=patient,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            period_from=period_from,
            period_to=period_to,
            actor=actor,
            action=action,
            purpose=purpose,
            data=data,
            source_reference=source_reference,
            organization=organization,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_consent(
        self,
        payload: ConsentCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ConsentModel:
        if not org_id:
            raise PermissionDeniedError(
                "Consent creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Consent creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_consent(payload), org_id
        )
        consent = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Consent created",
            extra={"event": "consent.created", "consent_id": consent.consent_id},
        )
        return consent

    async def patch_consent(
        self,
        consent_id: int,
        payload: ConsentPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ConsentModel:
        if not org_id:
            self._log_org_scope_miss("patch", consent_id, org_id)
            raise NotFoundError("Consent not found")
        existing = await self.repository.get_by_consent_id_in_org(
            consent_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", consent_id, org_id)
            raise NotFoundError("Consent not found")

        fragment, touched = patch_fragment_to_fhir_consent(payload)
        merged = merge_patch_fragment(
            to_fhir_consent(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            consent_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Consent not found")
        logger.info(
            "Consent updated",
            extra={
                "event": "consent.updated",
                "consent_id": consent_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_consent(
        self, consent_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.consent_belongs_to_org(
            consent_id, org_id
        ):
            self._log_org_scope_miss("delete", consent_id, org_id)
            raise NotFoundError("Consent not found")
        deleted = await self.repository.delete(consent_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Consent not found")
        logger.info(
            "Consent deleted",
            extra={"event": "consent.deleted", "consent_id": consent_id},
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource("Consent", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Consent failed base R4 validation",
                extra={"event": "consent.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, consent_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Consent write rejected by org scope",
            extra={
                "event": "consent.org_scope_miss",
                "operation": operation,
                "consent_id": consent_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

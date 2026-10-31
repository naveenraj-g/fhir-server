from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.document_reference import (
    merge_patch_fragment,
    patch_fragment_to_fhir_document_reference,
    payload_to_fhir_document_reference,
    to_fhir_document_reference,
    to_plain_document_reference,
)
from app.fhir.validation import validate_resource
from app.models.document_reference import DocumentReferenceModel
from app.repository.document_reference import DocumentReferenceRepository
from app.schemas.document_reference import (
    DocumentReferenceCreateSchema,
    DocumentReferencePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All DocumentReference business logic."""

    def __init__(self, repository: DocumentReferenceRepository):
        self.repository = repository

    def _to_fhir(self, document_reference: DocumentReferenceModel) -> dict:
        return to_fhir_document_reference(document_reference)

    def _to_plain(self, document_reference: DocumentReferenceModel) -> dict:
        return to_plain_document_reference(document_reference)

    async def get_document_reference_scoped(
        self, document_reference_id: int, org_id: str | None
    ) -> DocumentReferenceModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("DocumentReference operation requires an org-scoped token")
        document_reference = await self.repository.get_by_document_reference_id_in_org(
            document_reference_id, org_id
        )
        if not document_reference:
            raise NotFoundError("DocumentReference not found")
        return document_reference

    async def list_document_references(
        self,
        org_id: str | None = None,
        status: str | None = None,
        doc_status: str | None = None,
        type: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        author: str | None = None,
        custodian: str | None = None,
        authenticator: str | None = None,
        relates_to: str | None = None,
        identifier: str | None = None,
        description: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DocumentReferenceModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("DocumentReference operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            doc_status=doc_status,
            type=type,
            category=category,
            subject=subject,
            author=author,
            custodian=custodian,
            authenticator=authenticator,
            relates_to=relates_to,
            identifier=identifier,
            description=description,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_document_reference(
        self,
        payload: DocumentReferenceCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> DocumentReferenceModel:
        if not org_id:
            raise PermissionDeniedError("DocumentReference creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("DocumentReference creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_document_reference(payload), org_id)
        doc = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "DocumentReference created",
            extra={"event": "document_reference.created", "document_reference_id": doc.document_reference_id},
        )
        return doc

    async def patch_document_reference(
        self,
        document_reference_id: int,
        payload: DocumentReferencePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> DocumentReferenceModel:
        if not org_id:
            self._log_org_scope_miss("patch", document_reference_id, org_id)
            raise NotFoundError("DocumentReference not found")
        existing = await self.repository.get_by_document_reference_id_in_org(document_reference_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", document_reference_id, org_id)
            raise NotFoundError("DocumentReference not found")

        fragment, touched = patch_fragment_to_fhir_document_reference(payload)
        merged = merge_patch_fragment(to_fhir_document_reference(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            document_reference_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("DocumentReference not found")
        logger.info(
            "DocumentReference updated",
            extra={
                "event": "document_reference.updated",
                "document_reference_id": document_reference_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_document_reference(self, document_reference_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.document_reference_belongs_to_org(document_reference_id, org_id):
            self._log_org_scope_miss("delete", document_reference_id, org_id)
            raise NotFoundError("DocumentReference not found")
        deleted = await self.repository.delete(document_reference_id)
        if not deleted:
            raise NotFoundError("DocumentReference not found")
        logger.info(
            "DocumentReference deleted",
            extra={"event": "document_reference.deleted", "document_reference_id": document_reference_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("DocumentReference", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "DocumentReference failed base R4 validation",
                extra={"event": "document_reference.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, document_reference_id: int, org_id: str | None) -> None:
        logger.warning(
            "DocumentReference write rejected by org scope",
            extra={
                "event": "document_reference.org_scope_miss",
                "operation": operation,
                "document_reference_id": document_reference_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

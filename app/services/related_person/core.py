from datetime import date

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.related_person import (
    merge_patch_fragment,
    patch_fragment_to_fhir_related_person,
    payload_to_fhir_related_person,
    to_fhir_related_person,
    to_plain_related_person,
)
from app.fhir.validation import validate_resource
from app.models.related_person import RelatedPersonModel
from app.repository.related_person import RelatedPersonRepository
from app.schemas.related_person import (
    RelatedPersonCreateSchema,
    RelatedPersonPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All RelatedPerson business logic."""

    def __init__(self, repository: RelatedPersonRepository):
        self.repository = repository

    def _to_fhir(self, model: RelatedPersonModel) -> dict:
        return to_fhir_related_person(model)

    def _to_plain(self, model: RelatedPersonModel) -> dict:
        return to_plain_related_person(model)

    async def get_related_person_scoped(
        self, related_person_id: int, org_id: str | None
    ) -> RelatedPersonModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "RelatedPerson operation requires an org-scoped token"
            )
        model = await self.repository.get_by_related_person_id_in_org(
            related_person_id, org_id
        )
        if not model:
            raise NotFoundError("RelatedPerson not found")
        return model

    async def list_related_persons(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        patient: str | None = None,
        relationship: str | None = None,
        name: str | None = None,
        telecom: str | None = None,
        gender: str | None = None,
        birth_date: date | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        identifier: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[RelatedPersonModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "RelatedPerson operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            patient=patient,
            relationship=relationship,
            name=name,
            telecom=telecom,
            gender=gender,
            birth_date=birth_date,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            identifier=identifier,
            email=email,
            phone=phone,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_related_person(
        self,
        payload: RelatedPersonCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> RelatedPersonModel:
        if not org_id:
            raise PermissionDeniedError(
                "RelatedPerson creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "RelatedPerson creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_related_person(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "RelatedPerson created",
            extra={
                "event": "related_person.created",
                "related_person_id": model.related_person_id,
            },
        )
        return model

    async def patch_related_person(
        self,
        related_person_id: int,
        payload: RelatedPersonPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> RelatedPersonModel:
        if not org_id:
            self._log_org_scope_miss("patch", related_person_id, org_id)
            raise NotFoundError("RelatedPerson not found")
        existing = await self.repository.get_by_related_person_id_in_org(
            related_person_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", related_person_id, org_id)
            raise NotFoundError("RelatedPerson not found")

        if not updated_by:
            raise PermissionDeniedError(
                "RelatedPerson update requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_related_person(payload)
        merged = merge_patch_fragment(
            to_fhir_related_person(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            related_person_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("RelatedPerson not found")
        logger.info(
            "RelatedPerson updated",
            extra={
                "event": "related_person.updated",
                "related_person_id": related_person_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_related_person(
        self, related_person_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.related_person_belongs_to_org(
            related_person_id, org_id
        ):
            self._log_org_scope_miss("delete", related_person_id, org_id)
            raise NotFoundError("RelatedPerson not found")
        deleted = await self.repository.delete(related_person_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("RelatedPerson not found")
        logger.info(
            "RelatedPerson deleted",
            extra={
                "event": "related_person.deleted",
                "related_person_id": related_person_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "RelatedPerson", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "RelatedPerson failed base R4 validation",
                extra={
                    "event": "related_person.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, related_person_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "RelatedPerson write rejected by org scope",
            extra={
                "event": "related_person.org_scope_miss",
                "operation": operation,
                "related_person_id": related_person_id,
                "org_id": org_id,
            },
        )


class RelatedPersonService(_CoreMixin):
    """Service orchestrating RelatedPerson operations."""
    pass

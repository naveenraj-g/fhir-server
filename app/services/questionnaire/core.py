from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.questionnaire import (
    merge_patch_fragment,
    patch_fragment_to_fhir_questionnaire,
    payload_to_fhir_questionnaire,
    to_fhir_questionnaire,
    to_plain_questionnaire,
)
from app.fhir.validation import validate_resource
from app.models.questionnaire import QuestionnaireModel, QuestionnaireStatus as QuestionnaireStatusModel
from app.repository.questionnaire import QuestionnaireRepository
from app.schemas.enums import QuestionnaireStatus
from app.schemas.questionnaire import QuestionnaireCreateSchema, QuestionnairePatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Questionnaire business logic. Auth matches Practitioner: tenant
    scoping comes from the verified JWT's activeOrganizationId claim
    (actor.org_id), never a client-suppliable field, and there's no
    org-less/super-admin bypass — every operation requires an org-scoped
    actor. Like Practitioner (and unlike Organization/Location/
    HealthcareService/PractitionerRole/Schedule/Slot/Appointment/
    AppointmentResponse/Encounter), Questionnaire also keeps `user_id`
    (plain, gateway-forwarded), so `get_me()` additionally scopes to the
    acting end-user."""

    def __init__(self, repository: QuestionnaireRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, questionnaire: QuestionnaireModel) -> dict:
        return to_fhir_questionnaire(questionnaire)

    def _to_plain(self, questionnaire: QuestionnaireModel) -> dict:
        return to_plain_questionnaire(questionnaire)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_questionnaire_scoped(
        self, questionnaire_id: int, org_id: str | None
    ) -> QuestionnaireModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire operation requires an org-scoped token"
            )
        questionnaire = await self.repository.get_by_questionnaire_id_in_org(
            questionnaire_id, org_id
        )
        if not questionnaire:
            raise NotFoundError("Questionnaire not found")
        return questionnaire

    async def get_me(
        self,
        user_id: str,
        org_id: str | None = None,
        status: QuestionnaireStatus | None = None,
        url: str | None = None,
        name: str | None = None,
        title: str | None = None,
        publisher: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireModel], int | None]:
        """Scopes list() to the authenticated end-user's own user_id,
        always combined with the org-scoped actor's org_id."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            user_id=user_id,
            status=QuestionnaireStatusModel[status.name] if status else None,
            url=url,
            name=name,
            title=title,
            publisher=publisher,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_questionnaires(
        self,
        org_id: str | None = None,
        status: QuestionnaireStatus | None = None,
        url: str | None = None,
        name: str | None = None,
        title: str | None = None,
        publisher: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_questionnaire_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=QuestionnaireStatusModel[status.name] if status else None,
            url=url,
            name=name,
            title=title,
            publisher=publisher,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_questionnaire(
        self,
        payload: QuestionnaireCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> QuestionnaireModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Questionnaire at all."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire creation requires an org-scoped token"
            )
        await self._validate_base_r4(payload_to_fhir_questionnaire(payload), org_id)
        questionnaire = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Questionnaire created",
            extra={"event": "questionnaire.created", "questionnaire_id": questionnaire.questionnaire_id},
        )
        return questionnaire

    async def patch_questionnaire(
        self,
        questionnaire_id: int,
        payload: QuestionnairePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> QuestionnaireModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a questionnaire belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating."""
        if not org_id:
            self._log_org_scope_miss("patch", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")
        existing = await self.repository.get_by_questionnaire_id_in_org(
            questionnaire_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")

        fragment, touched = patch_fragment_to_fhir_questionnaire(payload)
        merged = merge_patch_fragment(to_fhir_questionnaire(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(questionnaire_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Questionnaire not found")
        logger.info(
            "Questionnaire updated",
            extra={
                "event": "questionnaire.updated",
                "questionnaire_id": questionnaire_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_questionnaire(
        self, questionnaire_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_questionnaire."""
        if not org_id or not await self.repository.questionnaire_belongs_to_org(
            questionnaire_id, org_id
        ):
            self._log_org_scope_miss("delete", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")
        deleted = await self.repository.delete(questionnaire_id)
        if not deleted:
            raise NotFoundError("Questionnaire not found")
        logger.info(
            "Questionnaire deleted",
            extra={"event": "questionnaire.deleted", "questionnaire_id": questionnaire_id},
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Questionnaire", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Questionnaire failed base R4 validation",
                extra={"event": "questionnaire.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, questionnaire_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such questionnaire" — so
        this log line is the only place the distinction is recorded."""
        logger.warning(
            "Questionnaire write rejected by org scope",
            extra={
                "event": "questionnaire.org_scope_miss",
                "operation": operation,
                "questionnaire_id": questionnaire_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import BusinessRuleViolationError, NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.patient import to_fhir_patient
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.patient import PatientModel
from app.repository.patient import PatientRepository
from app.repository.patient.search import patient_search
from app.schemas.patient import PatientCreateSchema, PatientPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Patient business logic. Like Organization, create/patch take
    a FHIR R4 Patient as the request body and store it whole — see
    PatientCreateSchema's docstring. Auth is identical: org_id comes
    from the verified JWT's activeOrganizationId claim (actor.org_id), never
    a client-suppliable field, and there's no org-less/super-admin bypass.

    Unlike Organization, a Patient can be linked to an individual
    end-user (`user_id`, see PatientModel). That link is not part of the
    FHIR resource: it is set and cleared through link_user()/unlink_user(),
    never through create/patch, and scopes the `/me` search."""

    def __init__(self, repository: PatientRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, patient: PatientModel) -> dict:
        return to_fhir_patient(patient)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_patient_scoped(
        self, patient_id: int, org_id: str | None
    ) -> PatientModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient operation requires an org-scoped token"
            )
        patient = await self.repository.get_by_patient_id_in_org(
            patient_id, org_id
        )
        if not patient:
            raise NotFoundError("Patient not found")
        return patient

    async def search_patients(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
        user_id: str | None = None,
    ) -> tuple[
        SearchRequest, list[PatientModel], int | None, list[PatientModel]
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the Patient search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. `user_id` (the `/me` route) additionally
        restricts the result to that end-user's own records. Raises
        PermissionDeniedError (403) for an org-less token — same invariant
        as get_patient_scoped().

        Returns (parsed request, matches, total, included (type, row))."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            patient_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(
            request, ctx, user_id=user_id
        )
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_patient(
        self,
        payload: PatientCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
        link_user_id: str | None = None,
    ) -> PatientModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Patient at all.

        `link_user_id` is the self-signup flow: the caller asked (explicitly,
        `?link_me=true`) for the new record to be linked to their own user, so
        `/me` works at once. Staff creating a record for someone else leave it
        unset and link afterwards with link_user(). A user is linked to at most
        one patient per org (422 otherwise).

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient creation requires an org-scoped token"
            )
        # The body is already a FHIR Patient — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(self._raw(payload, body), "Patient")
        await self._validate_base_r4(document, org_id)
        if link_user_id:
            other = await self.repository.get_by_user_id_in_org(link_user_id, org_id)
            if other:
                raise BusinessRuleViolationError(
                    f"User '{link_user_id}' is already linked to Patient/{other.patient_id}."
                )
        patient = await self.repository.create_full(document, org_id, created_by, user_id=link_user_id)
        logger.info(
            "Patient created",
            extra={
                "event": "patient.created",
                "patient_id": patient.patient_id,
                "linked_to_actor": bool(link_user_id),
            },
        )
        return patient

    async def patch_patient(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> PatientModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a patient belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", patient_id, org_id)
            raise NotFoundError("Patient not found")
        existing = await self.repository.get_by_patient_id_in_org(
            patient_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", patient_id, org_id)
            raise NotFoundError("Patient not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(to_fhir_patient(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(patient_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient updated",
            extra={
                "event": "patient.updated",
                "patient_id": patient_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_patient(
        self, patient_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_patient."""
        if not org_id or not await self.repository.patient_belongs_to_org(
            patient_id, org_id
        ):
            self._log_org_scope_miss("delete", patient_id, org_id)
            raise NotFoundError("Patient not found")
        deleted = await self.repository.delete(patient_id)
        if not deleted:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient deleted",
            extra={
                "event": "patient.deleted",
                "patient_id": patient_id,
            },
        )

    # ── End-user link ─────────────────────────────────────────────────────

    async def get_user_link(
        self, patient_id: int, org_id: str | None
    ) -> PatientModel:
        """The patient row (its `user_id` may be None = unlinked)."""
        return await self.get_patient_scoped(patient_id, org_id)

    async def link_user(
        self,
        patient_id: int,
        user_id: str,
        org_id: str | None,
        updated_by: str | None,
    ) -> PatientModel:
        """Link the end-user `user_id` to this patient. A user acts as
        at most one patient per org (a conflict is 422), re-linking the
        same user is a no-op, and linking replaces any previous user. Same
        org-scope gate as every other write: 403 org-less, 404 cross-org."""
        patient = await self.get_patient_scoped(patient_id, org_id)
        other = await self.repository.get_by_user_id_in_org(user_id, org_id)
        if other and other.patient_id != patient_id:
            raise BusinessRuleViolationError(
                f"User '{user_id}' is already linked to Patient/{other.patient_id}."
            )
        if patient.user_id == user_id:
            return patient
        updated = await self.repository.set_user_id(patient_id, user_id, updated_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient user linked",
            extra={"event": "patient.user_linked", "patient_id": patient_id},
        )
        return updated

    async def unlink_user(
        self, patient_id: int, org_id: str | None, updated_by: str | None
    ) -> None:
        """Clear the link (idempotent). Same org-scope gate as link_user."""
        patient = await self.get_patient_scoped(patient_id, org_id)
        if patient.user_id is None:
            return
        if not await self.repository.set_user_id(patient_id, None, updated_by):
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient user unlinked",
            extra={"event": "patient.user_unlinked", "patient_id": patient_id},
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    def _raw(payload, body: dict | None) -> dict:
        """The client's request JSON as sent; when there isn't one (an
        internal caller), the parsed payload's supplied fields instead."""
        if body is not None:
            return body
        return payload.model_dump(mode="json", exclude_unset=True)

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails
        validation against the most specific applicable layer of the
        base -> country -> organization profile chain (see
        docs/architecture/fhir-profiling-and-extensibility-strategy.md).
        Delegates to validate_resource(), which picks the actual backend
        (this project's own structural-only check, or the HL7 Java validator
        sidecar) per settings.fhir_validation.backend — see
        OrganizationService._validate_base_r4 for the full note."""
        errors = await validate_resource("Patient", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Patient failed base R4 validation",
                extra={"event": "patient.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, patient_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such patient" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Patient write rejected by org scope",
            extra={
                "event": "patient.org_scope_miss",
                "operation": operation,
                "patient_id": patient_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

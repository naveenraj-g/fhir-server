from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.practitioner import (
    merge_patch_fragment,
    patch_fragment_to_fhir_practitioner,
    payload_to_fhir_practitioner,
    to_fhir_practitioner,
    to_plain_practitioner,
)
from app.fhir.validation import validate_resource
from app.models.practitioner import PractitionerModel
from app.repository.practitioner import PractitionerRepository
from app.schemas.practitioner import PractitionerCreateSchema, PractitionerPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Practitioner business logic. Shaped like OrganizationService/
    LocationService: no standalone sub-resource endpoints and no separate
    scalar-only vs. full create/patch split — see
    PractitionerCreateSchema's docstring. Auth matches Organization/Location/
    HealthcareService: tenant scoping comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor. Unlike those three, Practitioner also
    keeps `user_id` (plain, gateway-forwarded — see PractitionerModel's
    docstring), so `get_me()` additionally scopes to the acting end-user."""

    def __init__(self, repository: PractitionerRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, p: PractitionerModel) -> dict:
        return to_fhir_practitioner(p)

    def _to_plain(self, p: PractitionerModel) -> dict:
        return to_plain_practitioner(p)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_practitioner_scoped(
        self, practitioner_id: int, org_id: str | None
    ) -> PractitionerModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        p = await self.repository.get_by_practitioner_id_in_org(
            practitioner_id, org_id
        )
        if not p:
            raise NotFoundError("Practitioner not found")
        return p

    async def list_practitioners(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        gender=None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PractitionerModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_practitioner_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            gender=gender,
            family=family,
            given=given,
            name=name,
            phonetic=phonetic,
            identifier=identifier,
            telecom=telecom,
            phone=phone,
            email=email,
            communication=communication,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            address_use=address_use,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        **filters,
    ) -> tuple[list[PractitionerModel], int | None]:
        """Scopes list() to the authenticated end-user's own user_id, always
        combined with the org-scoped actor's org_id."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        return await self.repository.get_me(user_id=user_id, org_id=org_id, **filters)

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_practitioner(
        self,
        payload: PractitionerCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Practitioner at all."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner creation requires an org-scoped token"
            )
        await self._validate_base_r4(payload_to_fhir_practitioner(payload), org_id)
        p = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Practitioner created",
            extra={"event": "practitioner.created", "practitioner_id": p.practitioner_id},
        )
        return p

    async def patch_practitioner(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a practitioner belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        patch_fragment_to_fhir_practitioner()'s docstring."""
        if not org_id:
            self._log_org_scope_miss("patch", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")
        existing = await self.repository.get_by_practitioner_id_in_org(
            practitioner_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")

        fragment, touched = patch_fragment_to_fhir_practitioner(payload)
        merged = merge_patch_fragment(to_fhir_practitioner(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(practitioner_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner updated",
            extra={
                "event": "practitioner.updated",
                "practitioner_id": practitioner_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_practitioner(
        self, practitioner_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_practitioner."""
        if not org_id or not await self.repository.practitioner_belongs_to_org(
            practitioner_id, org_id
        ):
            self._log_org_scope_miss("delete", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")
        deleted = await self.repository.delete(practitioner_id)
        if not deleted:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner deleted",
            extra={"event": "practitioner.deleted", "practitioner_id": practitioner_id},
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
        errors = await validate_resource("Practitioner", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Practitioner failed base R4 validation",
                extra={"event": "practitioner.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, practitioner_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such practitioner" — so this
        log line is the only place the distinction is recorded. Worth
        WARNING because a repeated cross-org miss is a very different
        signal from a typo'd id."""
        logger.warning(
            "Practitioner write rejected by org scope",
            extra={
                "event": "practitioner.org_scope_miss",
                "operation": operation,
                "practitioner_id": practitioner_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.practitioner import to_fhir_practitioner, to_plain_practitioner
from app.models.practitioner import PractitionerModel
from app.repository.practitioner import PractitionerRepository
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerFullCreateSchema,
    PractitionerFullPatchSchema,
    PractitionerPatchSchema,
)


class _CoreMixin:
    def __init__(self, repository: PractitionerRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, practitioner: PractitionerModel) -> dict:
        return to_fhir_practitioner(practitioner)

    def _to_plain(self, practitioner: PractitionerModel) -> dict:
        return to_plain_practitioner(practitioner)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_raw_by_user_id(self, user_id: str) -> PractitionerModel | None:
        return await self.repository.get_by_user_id(user_id)

    async def get_practitioner_scoped(
        self, practitioner_id: int, org_id: str | None
    ) -> PractitionerModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup. This is the single enforcement point for
        Practitioner's "no org-less bypass" invariant: every read/write path
        that must be tenant-scoped (get_practitioner_by_id and all 28
        sub-resource methods) goes through here instead of repeating the
        check per call site."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        practitioner = await self.repository.get_by_practitioner_id_in_org(
            practitioner_id, org_id
        )
        if not practitioner:
            raise NotFoundError("Practitioner not found")
        return practitioner

    async def get_me(self, user_id: str, org_id: str | None) -> PractitionerModel:
        """Lookup scoped to both user_id and org_id — backs the GET /me route.
        Raises PermissionDeniedError (403) for an org-less token — there's no
        "my own record" without a tenant to scope it to. Raises NotFoundError
        (404) if no practitioner matches both."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner lookup requires an org-scoped token"
            )
        practitioner = await self.repository.get_me(user_id, org_id)
        if not practitioner:
            raise NotFoundError("Practitioner not found")
        return practitioner

    async def list_practitioners(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender=None,
        active: bool | None = None,
        identifier: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        qualification_code: str | None = None,
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
            user_id=user_id,
            org_id=org_id,
            family=family,
            given=given,
            name=name,
            gender=gender,
            active=active,
            identifier=identifier,
            communication=communication,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            address_use=address_use,
            telecom=telecom,
            email=email,
            phone=phone,
            qualification_code=qualification_code,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_practitioner(
        self,
        payload: PractitionerCreateSchema,
        user_id: str | None = None,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Practitioner at all."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner creation requires an org-scoped token"
            )
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def create_practitioner_full(
        self,
        payload: PractitionerFullCreateSchema,
        user_id: str | None = None,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PractitionerModel:
        """Same org_id-from-actor handling as create_practitioner."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner creation requires an org-scoped token"
            )
        return await self.repository.create_full(payload, user_id, org_id, created_by)

    async def patch_practitioner(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a practitioner belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id or not await self.repository.practitioner_belongs_to_org(
            practitioner_id, org_id
        ):
            raise NotFoundError("Practitioner not found")
        updated = await self.repository.patch(practitioner_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def patch_practitioner_full(
        self,
        practitioner_id: int,
        payload: PractitionerFullPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PractitionerModel:
        """Same org_id ownership gate as patch_practitioner."""
        if not org_id or not await self.repository.practitioner_belongs_to_org(
            practitioner_id, org_id
        ):
            raise NotFoundError("Practitioner not found")
        updated = await self.repository.patch_full(practitioner_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def delete_practitioner(
        self, practitioner_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_practitioner — raises
        NotFoundError (404) on a missing org_id or an org mismatch instead
        of deleting."""
        if not org_id or not await self.repository.practitioner_belongs_to_org(
            practitioner_id, org_id
        ):
            raise NotFoundError("Practitioner not found")
        deleted = await self.repository.delete(practitioner_id)
        if not deleted:
            raise NotFoundError("Practitioner not found")

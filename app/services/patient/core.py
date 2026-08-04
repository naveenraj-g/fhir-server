from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.patient import (
    to_fhir_patient,
    to_fhir_patient_core,
    to_plain_patient,
    to_plain_patient_core,
)
from app.models.patient.enums import AddressUse, PatientGender
from app.models.patient import PatientModel
from app.repository.patient import PatientRepository
from app.schemas.patient import (
    PatientCreateSchema,
    PatientFullCreateSchema,
    PatientFullPatchSchema,
    PatientPatchSchema,
)


class _CoreMixin:
    """Formatters plus core Patient CRUD (everything except the 9
    sub-resource lifecycles, which live in their own sibling modules)."""

    def __init__(self, repository: PatientRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────────

    def _to_fhir(self, patient: PatientModel) -> dict:
        """Full FHIR R4 Patient dict, including all sub-resource arrays."""
        return to_fhir_patient(patient)

    def _to_plain(self, patient: PatientModel) -> dict:
        """Full plain snake_case Patient dict, including all sub-resource arrays."""
        return to_plain_patient(patient)

    def _to_fhir_core(self, patient: PatientModel) -> dict:
        """FHIR R4 Patient dict — scalar fields only, no sub-resource arrays."""
        return to_fhir_patient_core(patient)

    def _to_plain_core(self, patient: PatientModel) -> dict:
        """Plain snake_case Patient dict — scalar fields only, no sub-resource arrays."""
        return to_plain_patient_core(patient)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_patient(
        self,
        patient_id: int,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        core: bool = False,
    ) -> PatientModel:
        """Fetch a Patient by public id — the single entry point for every
        by-ID lookup shape. user_id/org_id, if supplied, each scope the
        lookup to that value (combined, both must match); omitted, no filter
        on that dimension. core=True skips the 9 sub-resource relationships
        (scalars only) — pair with _to_fhir_core()/_to_plain_core(), never
        _to_fhir()/_to_plain().

        Raises NotFoundError (404) if missing or if it doesn't match the
        supplied user_id/org_id filters — callers don't need their own
        None-check."""
        if core:
            if user_id is not None or org_id is not None:
                patient = await self.repository.get_core_by_patient_id_in_org(
                    patient_id, org_id, user_id=user_id
                )
            else:
                patient = await self.repository.get_core_by_patient_id(patient_id)
        else:
            if user_id is not None or org_id is not None:
                patient = await self.repository.get_by_patient_id_in_org(
                    patient_id, user_id, org_id
                )
            else:
                patient = await self.repository.get_by_patient_id(patient_id)
        if not patient:
            raise NotFoundError("Patient not found")
        return patient

    async def get_patient_scoped(
        self, patient_id: int, org_id: str | None, *, core: bool = False
    ) -> PatientModel:
        """Same lookup as get_patient(), but requires an org-scoped actor —
        raises PermissionDeniedError (403) for an org-less token instead of
        silently falling back to get_patient()'s unscoped lookup. This is the
        single enforcement point for Patient's "no org-less bypass" invariant:
        every read/write path that must be tenant-scoped (get_patient_by_id,
        get_patient_core, list_patients, and all 36 sub-resource methods)
        goes through here instead of repeating the check per call site."""
        if not org_id:
            raise PermissionDeniedError("Patient operation requires an org-scoped token")
        return await self.get_patient(patient_id, org_id=org_id, core=core)

    async def get_raw_by_user_id(self, user_id: str) -> PatientModel | None:
        """Lookup by the gateway-forwarded user_id."""
        return await self.repository.get_by_user_id(user_id)

    async def get_me(self, user_id: str, org_id: str | None) -> PatientModel:
        """Lookup scoped to both user_id and org_id — backs the GET /me route.
        Raises PermissionDeniedError (403) for an org-less token — there's no
        "my own record" without a tenant to scope it to. Raises NotFoundError
        (404) if no patient matches both."""
        if not org_id:
            raise PermissionDeniedError("Patient lookup requires an org-scoped token")
        patient = await self.repository.get_me(user_id, org_id)
        if not patient:
            raise NotFoundError("Patient not found")
        return patient

    async def list_patients(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender: PatientGender | None = None,
        active: bool | None = None,
        identifier: str | None = None,
        birthdate: list[str] | None = None,
        death_date: list[str] | None = None,
        deceased: bool | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use: AddressUse | None = None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        language: str | None = None,
        general_practitioner: str | None = None,
        organization: str | None = None,
        link: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PatientModel], int | None]:
        """Paginated, filtered, sorted list of patients. Backs GET /. Raises
        PermissionDeniedError (403) for an org-less token — same invariant as
        get_patient_scoped()."""
        if not org_id:
            raise PermissionDeniedError("Patient operation requires an org-scoped token")
        return await self.repository.list(
            user_id=user_id,
            org_id=org_id,
            family=family,
            given=given,
            name=name,
            gender=gender,
            active=active,
            identifier=identifier,
            birthdate=birthdate,
            death_date=death_date,
            deceased=deceased,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            address_use=address_use,
            telecom=telecom,
            email=email,
            phone=phone,
            language=language,
            general_practitioner=general_practitioner,
            organization=organization,
            link=link,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create_patient(
        self,
        payload: PatientCreateSchema,
        user_id: str | None,
        org_id: str | None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient from core scalar fields only — no sub-resources.
        org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Patient at all."""
        if not org_id:
            raise PermissionDeniedError("Patient creation requires an org-scoped token")
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def create_patient_full(
        self,
        payload: PatientFullCreateSchema,
        user_id: str | None,
        org_id: str | None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient plus any supplied sub-resource lists, atomically.
        Same org_id-from-actor handling as create_patient."""
        if not org_id:
            raise PermissionDeniedError("Patient creation requires an org-scoped token")
        return await self.repository.create_full(payload, user_id, org_id, created_by)

    async def patch_patient(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PatientModel:
        """Partial update of core scalar fields only. org_id comes from the
        verified JWT's actor.org_id — no bypass: a missing org_id or a
        patient belonging to a different org both raise NotFoundError (404)."""
        if not org_id or not await self.repository.patient_belongs_to_org(
            patient_id, org_id
        ):
            raise NotFoundError("Patient not found")
        updated = await self.repository.patch(patient_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def patch_patient_full(
        self,
        patient_id: int,
        payload: PatientFullPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PatientModel:
        """Partial update of core scalar fields plus atomic replacement of any
        supplied sub-resource lists. Same org_id ownership gate as patch_patient."""
        if not org_id or not await self.repository.patient_belongs_to_org(
            patient_id, org_id
        ):
            raise NotFoundError("Patient not found")
        updated = await self.repository.patch_full(patient_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def delete_patient(self, patient_id: int, org_id: str | None = None) -> None:
        """Permanently delete the Patient and all its sub-resources (cascade).
        Same org_id ownership gate as patch_patient — raises NotFoundError
        (404) on a missing org_id or an org mismatch instead of deleting."""
        if not org_id or not await self.repository.patient_belongs_to_org(
            patient_id, org_id
        ):
            raise NotFoundError("Patient not found")
        deleted = await self.repository.delete(patient_id)
        if not deleted:
            raise NotFoundError("Patient not found")

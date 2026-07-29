from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.fhir.mappers.patient import (
    to_fhir_patient,
    to_fhir_patient_core,
    to_plain_patient,
    to_plain_patient_core,
)
from app.models.patient.enums import AddressUse, PatientGender
from app.models.patient.patient import PatientModel
from app.repository.patient_repository import PatientRepository
from app.schemas.patient import (
    AddressCreate,
    AddressPatch,
    CommunicationCreate,
    CommunicationPatch,
    ContactCreate,
    ContactPatch,
    GeneralPractitionerCreate,
    GeneralPractitionerPatch,
    IdentifierCreate,
    IdentifierPatch,
    LinkCreate,
    LinkPatch,
    NameCreate,
    NamePatch,
    PatientCreateSchema,
    PatientFullCreateSchema,
    PatientFullPatchSchema,
    PatientPatchSchema,
    PhotoCreate,
    PhotoPatch,
    TelecomCreate,
    TelecomPatch,
)


class PatientService:
    """Thin orchestration layer between the router and PatientRepository.

    Every method here is a direct pass-through to the repository — no
    business logic lives in this class. It exists to give the router a
    stable interface that doesn't depend on repository internals, and to own
    the four formatter methods (_to_fhir/_to_plain/_to_fhir_core/_to_plain_core)
    so the router never has to import the mapper functions directly for the
    main Patient representation (it still imports them directly for the
    sub-resource list routes — see app/routers/patient.py).
    """

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
        goes through here instead of repeating the check per call site.

        Deliberately NOT used by resolve_patient() (app/deps/patient_deps.py),
        which calls get_patient() directly with no org_id at all — that's an
        intentional existence-only 404 check before the caller's org is even
        known, per the "resolve deps don't enforce ownership" convention."""
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

    # ── Sub-resources ─────────────────────────────────────────────────────────
    # Every method below validates the parent patient via get_patient_scoped()
    # first (raises PermissionDeniedError for an org-less token, NotFoundError
    # if missing or wrong org) before touching the repository — this is what
    # closes the org-scoping gap: previously these methods trusted
    # resolve_patient's existence-only check and never verified the caller's
    # org at all.

    async def add_name(
        self,
        patient_id: int,
        payload: NameCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one HumanName row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_name(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_identifier(
        self,
        patient_id: int,
        payload: IdentifierCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one business identifier row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_identifier(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_telecom(
        self,
        patient_id: int,
        payload: TelecomCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one contact-point row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_telecom(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_address(
        self,
        patient_id: int,
        payload: AddressCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one address row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_address(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_photo(
        self,
        patient_id: int,
        payload: PhotoCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one photo attachment row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_photo(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_contact(
        self,
        patient_id: int,
        payload: ContactCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one contact row (plus its relationship[]/telecom[] grandchildren) to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_contact(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_communication(
        self,
        patient_id: int,
        payload: CommunicationCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one communication-language row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_communication(
            patient_id, payload, created_by
        )
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_general_practitioner(
        self,
        patient_id: int,
        payload: GeneralPractitionerCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one general-practitioner reference row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_general_practitioner(
            patient_id, payload, created_by
        )
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def add_link(
        self,
        patient_id: int,
        payload: LinkCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one patient-link row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_link(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    # ── Sub-resource reads ────────────────────────────────────────────────────

    async def get_names(self, patient_id: int, org_id: str | None = None) -> list:
        """All HumanName rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_names(patient_id)

    async def get_identifiers(self, patient_id: int, org_id: str | None = None) -> list:
        """All identifier rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_identifiers(patient_id)

    async def get_telecoms(self, patient_id: int, org_id: str | None = None) -> list:
        """All contact-point rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_telecoms(patient_id)

    async def get_addresses(self, patient_id: int, org_id: str | None = None) -> list:
        """All address rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_addresses(patient_id)

    async def get_photos(self, patient_id: int, org_id: str | None = None) -> list:
        """All photo attachment rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_photos(patient_id)

    async def get_contacts(self, patient_id: int, org_id: str | None = None) -> list:
        """All contact rows (with grandchildren eager-loaded) for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_contacts(patient_id)

    async def get_communications(
        self, patient_id: int, org_id: str | None = None
    ) -> list:
        """All communication-language rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_communications(patient_id)

    async def get_general_practitioners(
        self, patient_id: int, org_id: str | None = None
    ) -> list:
        """All general-practitioner reference rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_general_practitioners(patient_id)

    async def get_links(self, patient_id: int, org_id: str | None = None) -> list:
        """All patient-link rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_links(patient_id)

    # ── Sub-resource deletes ──────────────────────────────────────────────────

    async def delete_name(
        self, patient_id: int, name_id: int, org_id: str | None = None
    ) -> None:
        """Delete one HumanName row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_name(patient_id, name_id)
        if not deleted:
            raise NotFoundError("Name not found on this Patient")

    async def delete_identifier(
        self, patient_id: int, identifier_id: int, org_id: str | None = None
    ) -> None:
        """Delete one identifier row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_identifier(patient_id, identifier_id)
        if not deleted:
            raise NotFoundError("Identifier not found on this Patient")

    async def delete_telecom(
        self, patient_id: int, telecom_id: int, org_id: str | None = None
    ) -> None:
        """Delete one contact-point row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_telecom(patient_id, telecom_id)
        if not deleted:
            raise NotFoundError("Telecom not found on this Patient")

    async def delete_address(
        self, patient_id: int, address_id: int, org_id: str | None = None
    ) -> None:
        """Delete one address row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_address(patient_id, address_id)
        if not deleted:
            raise NotFoundError("Address not found on this Patient")

    async def delete_photo(
        self, patient_id: int, photo_id: int, org_id: str | None = None
    ) -> None:
        """Delete one photo attachment row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_photo(patient_id, photo_id)
        if not deleted:
            raise NotFoundError("Photo not found on this Patient")

    async def delete_contact(
        self, patient_id: int, contact_id: int, org_id: str | None = None
    ) -> None:
        """Delete one contact row (cascades to its grandchildren)."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_contact(patient_id, contact_id)
        if not deleted:
            raise NotFoundError("Contact not found on this Patient")

    async def delete_communication(
        self, patient_id: int, comm_id: int, org_id: str | None = None
    ) -> None:
        """Delete one communication-language row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_communication(patient_id, comm_id)
        if not deleted:
            raise NotFoundError("Communication not found on this Patient")

    async def delete_general_practitioner(
        self, patient_id: int, gp_id: int, org_id: str | None = None
    ) -> None:
        """Delete one general-practitioner reference row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_general_practitioner(patient_id, gp_id)
        if not deleted:
            raise NotFoundError("General practitioner not found on this Patient")

    async def delete_link(
        self, patient_id: int, link_id: int, org_id: str | None = None
    ) -> None:
        """Delete one patient-link row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_link(patient_id, link_id)
        if not deleted:
            raise NotFoundError("Link not found on this Patient")

    # ── Sub-resource patch ────────────────────────────────────────────────────

    async def patch_name(
        self,
        patient_id: int,
        name_id: int,
        payload: NamePatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one HumanName row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_name(
            patient_id, name_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Name not found on this Patient")
        return updated

    async def patch_identifier(
        self,
        patient_id: int,
        identifier_id: int,
        payload: IdentifierPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one identifier row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_identifier(
            patient_id, identifier_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Identifier not found on this Patient")
        return updated

    async def patch_telecom(
        self,
        patient_id: int,
        telecom_id: int,
        payload: TelecomPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one contact-point row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_telecom(
            patient_id, telecom_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Telecom not found on this Patient")
        return updated

    async def patch_address(
        self,
        patient_id: int,
        address_id: int,
        payload: AddressPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one address row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_address(
            patient_id, address_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Address not found on this Patient")
        return updated

    async def patch_photo(
        self,
        patient_id: int,
        photo_id: int,
        payload: PhotoPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one photo attachment row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_photo(
            patient_id, photo_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Photo not found on this Patient")
        return updated

    async def patch_contact(
        self,
        patient_id: int,
        contact_id: int,
        payload: ContactPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one contact row — replaces relationship[]/telecom[] wholesale if supplied."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_contact(
            patient_id, contact_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Contact not found on this Patient")
        return updated

    async def patch_communication(
        self,
        patient_id: int,
        comm_id: int,
        payload: CommunicationPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one communication-language row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_communication(
            patient_id, comm_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Communication not found on this Patient")
        return updated

    async def patch_general_practitioner(
        self,
        patient_id: int,
        gp_id: int,
        payload: GeneralPractitionerPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one general-practitioner reference row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_general_practitioner(
            patient_id, gp_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("General practitioner not found on this Patient")
        return updated

    async def patch_link(
        self,
        patient_id: int,
        link_id: int,
        payload: LinkPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one patient-link row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_link(
            patient_id, link_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Link not found on this Patient")
        return updated

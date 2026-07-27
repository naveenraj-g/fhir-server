from app.fhir.mappers.patient import (
    to_fhir_patient,
    to_fhir_patient_core,
    to_plain_patient,
    to_plain_patient_core,
)
from app.models.patient.enums import PatientGender, PatientGeneralPractitionerType
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

    async def get_raw_by_patient_id(self, patient_id: int) -> PatientModel | None:
        """Full, eager-loaded lookup by public patient_id — used by resolve_patient()."""
        return await self.repository.get_by_patient_id(patient_id)

    async def get_raw_core_by_patient_id(self, patient_id: int) -> PatientModel | None:
        """Patient table scalars only, no sub-resource fan-out. Backs GET /{patient_id}/core."""
        return await self.repository.get_core_by_patient_id(patient_id)

    async def get_raw_by_user_id(self, user_id: str) -> PatientModel | None:
        """Lookup by the gateway-forwarded user_id."""
        return await self.repository.get_by_user_id(user_id)

    async def get_patient(self, patient_id: int) -> PatientModel | None:
        """Full, eager-loaded lookup by public patient_id."""
        return await self.repository.get_by_patient_id(patient_id)

    async def get_patient_in_org(
        self, patient_id: int, user_id: str, org_id: str
    ) -> PatientModel | None:
        """Lookup scoped to a specific org — None if the patient belongs to a different org."""
        return await self.repository.get_by_patient_id_in_org(
            patient_id, user_id, org_id
        )

    async def get_me(self, user_id: str, org_id: str) -> PatientModel | None:
        """Lookup scoped to both user_id and org_id — backs the GET /me route."""
        return await self.repository.get_me(user_id, org_id)

    async def list_patients(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        family_name: str | None = None,
        given_name: str | None = None,
        gender: PatientGender | None = None,
        active: bool | None = None,
        identifier: str | None = None,
        birth_date_from=None,
        birth_date_to=None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        deceased: bool | None = None,
        general_practitioner_type: PatientGeneralPractitionerType | None = None,
        general_practitioner_id: int | None = None,
        organization_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PatientModel], int | None]:
        """Paginated, filtered, sorted list of patients. Backs GET /."""
        return await self.repository.list(
            user_id=user_id,
            org_id=org_id,
            family_name=family_name,
            given_name=given_name,
            gender=gender,
            active=active,
            identifier=identifier,
            birth_date_from=birth_date_from,
            birth_date_to=birth_date_to,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            email=email,
            phone=phone,
            deceased=deceased,
            general_practitioner_type=general_practitioner_type,
            general_practitioner_id=general_practitioner_id,
            organization_id=organization_id,
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
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient from core scalar fields only — no sub-resources."""
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def create_patient_full(
        self,
        payload: PatientFullCreateSchema,
        user_id: str | None,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient plus any supplied sub-resource lists, atomically."""
        return await self.repository.create_full(payload, user_id, org_id, created_by)

    async def patch_patient(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of core scalar fields only."""
        return await self.repository.patch(patient_id, payload, updated_by)

    async def patch_patient_full(
        self,
        patient_id: int,
        payload: PatientFullPatchSchema,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of core scalar fields plus atomic replacement of any supplied sub-resource lists."""
        return await self.repository.patch_full(patient_id, payload, updated_by)

    async def delete_patient(self, patient_id: int) -> bool:
        """Permanently delete the Patient and all its sub-resources (cascade)."""
        return await self.repository.delete(patient_id)

    # ── Sub-resources ─────────────────────────────────────────────────────────

    async def add_name(
        self, patient_id: int, payload: NameCreate
    ) -> PatientModel | None:
        """Append one HumanName row to this patient."""
        return await self.repository.add_name(patient_id, payload)

    async def add_identifier(
        self, patient_id: int, payload: IdentifierCreate
    ) -> PatientModel | None:
        """Append one business identifier row to this patient."""
        return await self.repository.add_identifier(patient_id, payload)

    async def add_telecom(
        self, patient_id: int, payload: TelecomCreate
    ) -> PatientModel | None:
        """Append one contact-point row to this patient."""
        return await self.repository.add_telecom(patient_id, payload)

    async def add_address(
        self, patient_id: int, payload: AddressCreate
    ) -> PatientModel | None:
        """Append one address row to this patient."""
        return await self.repository.add_address(patient_id, payload)

    async def add_photo(
        self, patient_id: int, payload: PhotoCreate
    ) -> PatientModel | None:
        """Append one photo attachment row to this patient."""
        return await self.repository.add_photo(patient_id, payload)

    async def add_contact(
        self, patient_id: int, payload: ContactCreate
    ) -> PatientModel | None:
        """Append one contact row (plus its relationship[]/telecom[] grandchildren) to this patient."""
        return await self.repository.add_contact(patient_id, payload)

    async def add_communication(
        self, patient_id: int, payload: CommunicationCreate
    ) -> PatientModel | None:
        """Append one communication-language row to this patient."""
        return await self.repository.add_communication(patient_id, payload)

    async def add_general_practitioner(
        self, patient_id: int, payload: GeneralPractitionerCreate
    ) -> PatientModel | None:
        """Append one general-practitioner reference row to this patient."""
        return await self.repository.add_general_practitioner(patient_id, payload)

    async def add_link(
        self, patient_id: int, payload: LinkCreate
    ) -> PatientModel | None:
        """Append one patient-link row to this patient."""
        return await self.repository.add_link(patient_id, payload)

    # ── Sub-resource reads ────────────────────────────────────────────────────

    async def get_names(self, patient_id: int) -> list:
        """All HumanName rows for this patient."""
        return await self.repository.get_names(patient_id)

    async def get_identifiers(self, patient_id: int) -> list:
        """All identifier rows for this patient."""
        return await self.repository.get_identifiers(patient_id)

    async def get_telecoms(self, patient_id: int) -> list:
        """All contact-point rows for this patient."""
        return await self.repository.get_telecoms(patient_id)

    async def get_addresses(self, patient_id: int) -> list:
        """All address rows for this patient."""
        return await self.repository.get_addresses(patient_id)

    async def get_photos(self, patient_id: int) -> list:
        """All photo attachment rows for this patient."""
        return await self.repository.get_photos(patient_id)

    async def get_contacts(self, patient_id: int) -> list:
        """All contact rows (with grandchildren eager-loaded) for this patient."""
        return await self.repository.get_contacts(patient_id)

    async def get_communications(self, patient_id: int) -> list:
        """All communication-language rows for this patient."""
        return await self.repository.get_communications(patient_id)

    async def get_general_practitioners(self, patient_id: int) -> list:
        """All general-practitioner reference rows for this patient."""
        return await self.repository.get_general_practitioners(patient_id)

    async def get_links(self, patient_id: int) -> list:
        """All patient-link rows for this patient."""
        return await self.repository.get_links(patient_id)

    # ── Sub-resource deletes ──────────────────────────────────────────────────

    async def delete_name(self, patient_id: int, name_id: int) -> bool:
        """Delete one HumanName row."""
        return await self.repository.delete_name(patient_id, name_id)

    async def delete_identifier(self, patient_id: int, identifier_id: int) -> bool:
        """Delete one identifier row."""
        return await self.repository.delete_identifier(patient_id, identifier_id)

    async def delete_telecom(self, patient_id: int, telecom_id: int) -> bool:
        """Delete one contact-point row."""
        return await self.repository.delete_telecom(patient_id, telecom_id)

    async def delete_address(self, patient_id: int, address_id: int) -> bool:
        """Delete one address row."""
        return await self.repository.delete_address(patient_id, address_id)

    async def delete_photo(self, patient_id: int, photo_id: int) -> bool:
        """Delete one photo attachment row."""
        return await self.repository.delete_photo(patient_id, photo_id)

    async def delete_contact(self, patient_id: int, contact_id: int) -> bool:
        """Delete one contact row (cascades to its grandchildren)."""
        return await self.repository.delete_contact(patient_id, contact_id)

    async def delete_communication(self, patient_id: int, comm_id: int) -> bool:
        """Delete one communication-language row."""
        return await self.repository.delete_communication(patient_id, comm_id)

    async def delete_general_practitioner(self, patient_id: int, gp_id: int) -> bool:
        """Delete one general-practitioner reference row."""
        return await self.repository.delete_general_practitioner(patient_id, gp_id)

    async def delete_link(self, patient_id: int, link_id: int) -> bool:
        """Delete one patient-link row."""
        return await self.repository.delete_link(patient_id, link_id)

    # ── Sub-resource patch ────────────────────────────────────────────────────

    async def patch_name(
        self, patient_id: int, name_id: int, payload: NamePatch
    ) -> PatientModel | None:
        """Partial update of one HumanName row."""
        return await self.repository.patch_name(patient_id, name_id, payload)

    async def patch_identifier(
        self, patient_id: int, identifier_id: int, payload: IdentifierPatch
    ) -> PatientModel | None:
        """Partial update of one identifier row."""
        return await self.repository.patch_identifier(
            patient_id, identifier_id, payload
        )

    async def patch_telecom(
        self, patient_id: int, telecom_id: int, payload: TelecomPatch
    ) -> PatientModel | None:
        """Partial update of one contact-point row."""
        return await self.repository.patch_telecom(patient_id, telecom_id, payload)

    async def patch_address(
        self, patient_id: int, address_id: int, payload: AddressPatch
    ) -> PatientModel | None:
        """Partial update of one address row."""
        return await self.repository.patch_address(patient_id, address_id, payload)

    async def patch_photo(
        self, patient_id: int, photo_id: int, payload: PhotoPatch
    ) -> PatientModel | None:
        """Partial update of one photo attachment row."""
        return await self.repository.patch_photo(patient_id, photo_id, payload)

    async def patch_contact(
        self, patient_id: int, contact_id: int, payload: ContactPatch
    ) -> PatientModel | None:
        """Partial update of one contact row — replaces relationship[]/telecom[] wholesale if supplied."""
        return await self.repository.patch_contact(patient_id, contact_id, payload)

    async def patch_communication(
        self, patient_id: int, comm_id: int, payload: CommunicationPatch
    ) -> PatientModel | None:
        """Partial update of one communication-language row."""
        return await self.repository.patch_communication(patient_id, comm_id, payload)

    async def patch_general_practitioner(
        self, patient_id: int, gp_id: int, payload: GeneralPractitionerPatch
    ) -> PatientModel | None:
        """Partial update of one general-practitioner reference row."""
        return await self.repository.patch_general_practitioner(
            patient_id, gp_id, payload
        )

    async def patch_link(
        self, patient_id: int, link_id: int, payload: LinkPatch
    ) -> PatientModel | None:
        """Partial update of one patient-link row."""
        return await self.repository.patch_link(patient_id, link_id, payload)

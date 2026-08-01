from app.errors.domain import NotFoundError
from app.models.patient.patient import PatientModel
from app.schemas.patient import GeneralPractitionerCreate, GeneralPractitionerPatch


class _GeneralPractitionerMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.generalPractitioner
    rows. Every method validates the parent patient via get_patient_scoped()
    first."""

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

    async def get_general_practitioners(
        self, patient_id: int, org_id: str | None = None
    ) -> list:
        """All general-practitioner reference rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_general_practitioners(patient_id)

    async def delete_general_practitioner(
        self, patient_id: int, gp_id: int, org_id: str | None = None
    ) -> None:
        """Delete one general-practitioner reference row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_general_practitioner(patient_id, gp_id)
        if not deleted:
            raise NotFoundError("General practitioner not found on this Patient")

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

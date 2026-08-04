from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import IdentifierCreate, IdentifierPatch


class _IdentifierMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.identifier rows.
    Every method validates the parent patient via get_patient_scoped() first."""

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

    async def get_identifiers(self, patient_id: int, org_id: str | None = None) -> list:
        """All identifier rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_identifiers(patient_id)

    async def delete_identifier(
        self, patient_id: int, identifier_id: int, org_id: str | None = None
    ) -> None:
        """Delete one identifier row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_identifier(patient_id, identifier_id)
        if not deleted:
            raise NotFoundError("Identifier not found on this Patient")

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

from sqlalchemy import select

from app.core.logging import get_logger
from app.models.patient import PatientModel

from app.repository._reference_check import validate_local_references
from ._indexer import INDEX_RELATIONSHIPS, index_columns, index_rows
from ._shared import _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Patient document:
    it's stored verbatim in `content`, and the search index is rebuilt from it
    (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
        user_id: str | None = None,
    ) -> PatientModel:
        """`user_id` links the new record to an end-user straight away (the
        self-signup flow); it is not part of the resource and never in
        `content`."""
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            patient = PatientModel(
                tenant_id=org_id,
                created_by=created_by,
                user_id=user_id,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(patient)
            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise
            return patient

    async def patch_full(
        self,
        patient_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt. `user_id` is not part of the resource and is never touched
        here — it is only changed by set_user_id()."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.patient_id == patient_id)
            )
            patient = (await session.execute(stmt)).scalars().first()
            if not patient:
                return None

            await validate_local_references(session, patient.tenant_id, document)

            patient.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(patient, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(patient, rel, rows[rel])
            if updated_by is not None:
                patient.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise
            return patient

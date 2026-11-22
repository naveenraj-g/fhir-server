from sqlalchemy import select

from app.core.logging import get_logger
from app.models.appointment import AppointmentModel

from app.repository._reference_check import validate_local_references
from ._indexer import INDEX_RELATIONSHIPS, index_columns, index_rows
from ._shared import _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Appointment
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> AppointmentModel:
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            appointment = AppointmentModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(appointment)
            try:
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise
            return appointment

    async def patch_full(
        self,
        appointment_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> AppointmentModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(
                    AppointmentModel.appointment_id == appointment_id
                )
            )
            appointment = (await session.execute(stmt)).scalars().first()
            if not appointment:
                return None

            await validate_local_references(session, appointment.tenant_id, document)

            appointment.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(appointment, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(appointment, rel, rows[rel])
            if updated_by is not None:
                appointment.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise
            return appointment

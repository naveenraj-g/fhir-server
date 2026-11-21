from sqlalchemy import select

from app.core.logging import get_logger
from app.models.schedule import ScheduleModel

from ._indexer import INDEX_RELATIONSHIPS, index_columns, index_rows, local_references
from ._shared import (
    _parse_actor_ref,
    _parse_org_ref,
    _validate_actor_reference,
    _validate_reference,
    _with_relationships,
)

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document —
    identifier.assigner and the actors of a type this server models
    (Practitioner, PractitionerRole, HealthcareService, Location) — scoped to
    the caller's org; 422 if one doesn't resolve. Patient / RelatedPerson /
    Device actors aren't resources here and aren't checked."""
    for label, resource_type, ref in local_references(document):
        if resource_type == "Organization":
            ref_type, ref_id = _parse_org_ref(ref)
            await _validate_reference(session, tenant_id, ref_type, ref_id, label)
        else:
            ref_type, ref_id = _parse_actor_ref(ref)
            await _validate_actor_reference(session, tenant_id, ref_type, ref_id)


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR Schedule
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> ScheduleModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            schedule = ScheduleModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(schedule)
            try:
                await session.commit()
                await session.refresh(schedule)
            except Exception:
                await session.rollback()
                raise
            return schedule

    async def patch_full(
        self,
        schedule_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> ScheduleModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ScheduleModel).where(ScheduleModel.schedule_id == schedule_id)
            )
            schedule = (await session.execute(stmt)).scalars().first()
            if not schedule:
                return None

            await _validate_local_references(session, schedule.tenant_id, document)

            schedule.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(schedule, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(schedule, rel, rows[rel])
            if updated_by is not None:
                schedule.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(schedule)
            except Exception:
                await session.rollback()
                raise
            return schedule

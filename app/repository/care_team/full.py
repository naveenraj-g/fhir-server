from sqlalchemy import select

from app.core.logging import get_logger
from app.models.care_team import CareTeamModel

from ._indexer import index_columns, index_rows, local_references
from ._shared import INDEX_RELATIONSHIPS, _validate_reference, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document
    (identifier assigners, subject, encounter, participants, reasons, managing organizations, note authors), scoped to the caller's org — 422 if one does not resolve."""
    for label, resource_type, ref in local_references(document):
        await _validate_reference(
            session, tenant_id, resource_type, int(ref.split("/")[1]), label
        )


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR CareTeam
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> CareTeamModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            care_team = CareTeamModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(care_team)
            try:
                await session.commit()
                await session.refresh(care_team)
            except Exception:
                await session.rollback()
                raise
            return care_team

    async def patch_full(
        self,
        care_team_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> CareTeamModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id)
            )
            care_team = (await session.execute(stmt)).scalars().first()
            if not care_team:
                return None

            await _validate_local_references(session, care_team.tenant_id, document)

            care_team.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(care_team, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(care_team, rel, rows[rel])
            if updated_by is not None:
                care_team.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(care_team)
            except Exception:
                await session.rollback()
                raise
            return care_team

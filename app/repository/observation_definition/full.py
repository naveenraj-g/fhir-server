from sqlalchemy import select

from app.core.logging import get_logger
from app.models.observation_definition import ObservationDefinitionModel
from app.repository._reference_check import validate_local_references

from ._indexer import index_columns, index_rows
from ._shared import INDEX_RELATIONSHIPS, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR ObservationDefinition
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> ObservationDefinitionModel:
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            observation_definition = ObservationDefinitionModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(observation_definition)
            try:
                await session.commit()
                await session.refresh(observation_definition)
            except Exception:
                await session.rollback()
                raise
            return observation_definition

    async def patch_full(
        self,
        observation_definition_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> ObservationDefinitionModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ObservationDefinitionModel).where(
                    ObservationDefinitionModel.observation_definition_id
                    == observation_definition_id
                )
            )
            observation_definition = (await session.execute(stmt)).scalars().first()
            if not observation_definition:
                return None

            await validate_local_references(
                session, observation_definition.tenant_id, document
            )

            observation_definition.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(observation_definition, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(observation_definition, rel, rows[rel])
            if updated_by is not None:
                observation_definition.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(observation_definition)
            except Exception:
                await session.rollback()
                raise
            return observation_definition

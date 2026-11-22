from sqlalchemy import select

from app.core.logging import get_logger
from app.models.immunization_recommendation import ImmunizationRecommendationModel

from app.repository._reference_check import validate_local_references
from ._indexer import index_columns, index_rows
from ._shared import INDEX_RELATIONSHIPS, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR ImmunizationRecommendation
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> ImmunizationRecommendationModel:
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            immunization_recommendation = ImmunizationRecommendationModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(immunization_recommendation)
            try:
                await session.commit()
                await session.refresh(immunization_recommendation)
            except Exception:
                await session.rollback()
                raise
            return immunization_recommendation

    async def patch_full(
        self,
        immunization_recommendation_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> ImmunizationRecommendationModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationRecommendationModel).where(
                    ImmunizationRecommendationModel.immunization_recommendation_id
                    == immunization_recommendation_id
                )
            )
            immunization_recommendation = (
                (await session.execute(stmt)).scalars().first()
            )
            if not immunization_recommendation:
                return None

            await validate_local_references(
                session, immunization_recommendation.tenant_id, document
            )

            immunization_recommendation.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(immunization_recommendation, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(immunization_recommendation, rel, rows[rel])
            if updated_by is not None:
                immunization_recommendation.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(immunization_recommendation)
            except Exception:
                await session.rollback()
                raise
            return immunization_recommendation

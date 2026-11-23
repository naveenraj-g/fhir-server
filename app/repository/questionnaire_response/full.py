from sqlalchemy import select

from app.core.logging import get_logger
from app.models.questionnaire_response import QuestionnaireResponseModel

from app.repository._reference_check import validate_local_references
from ._indexer import index_columns, index_rows
from ._shared import INDEX_RELATIONSHIPS, _with_relationships

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR QuestionnaireResponse
    document: it is stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> QuestionnaireResponseModel:
        async with self.session_factory() as session:
            await validate_local_references(session, org_id, document)
            questionnaire_response = QuestionnaireResponseModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(questionnaire_response)
            try:
                await session.commit()
                await session.refresh(questionnaire_response)
            except Exception:
                await session.rollback()
                raise
            return questionnaire_response

    async def patch_full(
        self,
        questionnaire_response_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> QuestionnaireResponseModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.questionnaire_response_id
                    == questionnaire_response_id
                )
            )
            questionnaire_response = (await session.execute(stmt)).scalars().first()
            if not questionnaire_response:
                return None

            await validate_local_references(
                session, questionnaire_response.tenant_id, document
            )

            questionnaire_response.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(questionnaire_response, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(questionnaire_response, rel, rows[rel])
            if updated_by is not None:
                questionnaire_response.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(questionnaire_response)
            except Exception:
                await session.rollback()
                raise
            return questionnaire_response

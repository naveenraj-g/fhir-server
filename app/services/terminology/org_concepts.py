from app.schemas.terminology import (
    CreateConceptRequest,
    OrgConceptListResponse,
    OrgConceptResponse,
    PatchConceptRequest,
)

from ._shared import _org_concept_response


class _OrgConceptsMixin:
    async def create_concept(
        self, req: CreateConceptRequest, org_id: str, user_id: str | None
    ) -> OrgConceptResponse | None:
        cs = await self.repository.get_code_system_by_url(req.code_system_url)
        if cs is None:
            return None
        concept = await self.repository.create_org_concept(
            code_system_id=cs.id,
            code=req.code,
            display=req.display,
            definition=req.definition,
            org_id=org_id,
            user_id=user_id,
        )
        return _org_concept_response(concept, cs)

    async def get_org_concept(
        self, concept_id: int, org_id: str
    ) -> OrgConceptResponse | None:
        result = await self.repository.get_org_concept(concept_id, org_id)
        if result is None:
            return None
        concept, cs = result[0], result[1]
        return _org_concept_response(concept, cs)

    async def patch_concept(
        self, concept_id: int, req: PatchConceptRequest, org_id: str
    ) -> OrgConceptResponse | None:
        result = await self.repository.patch_org_concept(
            concept_id, org_id, req.display, req.definition
        )
        if result is None:
            return None
        concept, cs = result[0], result[1]
        return _org_concept_response(concept, cs)

    async def delete_concept(self, concept_id: int, org_id: str) -> bool:
        return await self.repository.delete_org_concept(concept_id, org_id)

    async def list_org_concepts(
        self,
        org_id: str,
        code_system_url: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> OrgConceptListResponse:
        count, rows = await self.repository.list_org_concepts(
            org_id, code_system_url, q, limit, offset
        )
        return OrgConceptListResponse(
            total=count,
            limit=limit,
            offset=offset,
            data=[_org_concept_response(concept, cs) for concept, cs in rows],
        )

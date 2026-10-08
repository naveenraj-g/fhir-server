from app.schemas.terminology import (
    ConceptsForFieldResponse,
    LookupBatchRequest,
    LookupBatchResponse,
    LookupRequest,
    LookupResult,
    SearchResponse,
)

from ._shared import _concept_response, _cs_response, _vs_response


class _ConceptsMixin:
    async def search_concepts(
        self, q: str, system: str | None, limit: int, offset: int
    ) -> SearchResponse:
        count, rows = await self.repository.search_concepts(q, system, limit, offset)
        return SearchResponse(
            total=count,
            limit=limit,
            offset=offset,
            data=[_concept_response(concept, cs) for concept, cs in rows],
        )

    async def lookup(self, req: LookupRequest) -> LookupResult:
        cs, concept = await self.repository.lookup_concept(req.system, req.code)
        if concept is None:
            return LookupResult(found=False)
        return LookupResult(
            found=True,
            concept=_concept_response(concept, cs),
            code_system=_cs_response(cs),
        )

    async def lookup_batch(self, req: LookupBatchRequest) -> LookupBatchResponse:
        results = [await self.lookup(item) for item in req.items]
        return LookupBatchResponse(results=results)

    async def get_concepts_for_field(
        self, resource: str, field: str, q: str | None, limit: int, offset: int
    ) -> ConceptsForFieldResponse:
        binding = await self.repository.get_field_binding(resource, field)
        if binding is None:
            return ConceptsForFieldResponse(
                resource=resource,
                field=field,
                total=0,
                limit=limit,
                offset=offset,
                concepts=[],
            )
        vs = await self.repository.get_value_set(binding.value_set_id)
        count, rows = await self.repository.expand_value_set(
            binding.value_set_id, q, limit, offset
        )
        return ConceptsForFieldResponse(
            resource=resource,
            field=field,
            value_set=_vs_response(vs) if vs else None,
            binding_strength=binding.binding_strength,
            multiple_allowed=binding.multiple_allowed,
            total=count,
            limit=limit,
            offset=offset,
            concepts=[_concept_response(concept, cs) for concept, cs in rows],
        )

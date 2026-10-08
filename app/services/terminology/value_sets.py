from app.schemas.terminology import ValueSetExpandResponse, ValueSetListResponse

from ._shared import _concept_response, _vs_response


class _ValueSetsMixin:
    async def list_value_sets(
        self, q: str | None, limit: int, offset: int
    ) -> ValueSetListResponse:
        count, rows = await self.repository.list_value_sets(q, limit, offset)
        return ValueSetListResponse(
            total=count,
            limit=limit,
            offset=offset,
            data=[_vs_response(vs) for vs in rows],
        )

    async def expand_value_set(
        self, value_set_id: int, q: str | None, limit: int, offset: int
    ) -> ValueSetExpandResponse | None:
        vs = await self.repository.get_value_set(value_set_id)
        if vs is None:
            return None
        count, rows = await self.repository.expand_value_set(
            value_set_id, q, limit, offset
        )
        return ValueSetExpandResponse(
            value_set=_vs_response(vs),
            total=count,
            limit=limit,
            offset=offset,
            concepts=[_concept_response(concept, cs) for concept, cs in rows],
        )

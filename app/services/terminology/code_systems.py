from app.schemas.terminology import CodeSystemListResponse

from ._shared import _cs_response


class _CodeSystemsMixin:
    async def list_code_systems(self) -> CodeSystemListResponse:
        rows = await self.repository.list_code_systems()
        return CodeSystemListResponse(
            total=len(rows),
            data=[_cs_response(cs) for cs in rows],
        )

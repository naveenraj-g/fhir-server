from app.schemas.terminology import (
    CreateDisplayOverrideRequest,
    DisplayOverrideListResponse,
    DisplayOverrideResponse,
    PatchDisplayOverrideRequest,
)

from ._shared import _display_override_response


class _DisplayOverridesMixin:
    async def create_display_override(
        self, req: CreateDisplayOverrideRequest, org_id: str, user_id: str | None
    ) -> DisplayOverrideResponse | None:
        """Returns None if (system, code) doesn't resolve to an existing
        concept — the override must point at something that already
        exists; it can't invent the underlying code."""
        cs, concept = await self.repository.lookup_concept(req.system, req.code)
        if concept is None:
            return None
        override = await self.repository.create_display_override(
            concept.id, org_id, req.display, req.definition, user_id
        )
        return _display_override_response(override, concept, cs)

    async def get_display_override(
        self, override_id: int, org_id: str
    ) -> DisplayOverrideResponse | None:
        result = await self.repository.get_display_override(override_id, org_id)
        if result is None:
            return None
        override, concept, cs = result
        return _display_override_response(override, concept, cs)

    async def patch_display_override(
        self, override_id: int, req: PatchDisplayOverrideRequest, org_id: str
    ) -> DisplayOverrideResponse | None:
        result = await self.repository.patch_display_override(
            override_id, org_id, req.display, req.definition
        )
        if result is None:
            return None
        override, concept, cs = result
        return _display_override_response(override, concept, cs)

    async def delete_display_override(self, override_id: int, org_id: str) -> bool:
        return await self.repository.delete_display_override(override_id, org_id)

    async def list_display_overrides(
        self, org_id: str, limit: int, offset: int
    ) -> DisplayOverrideListResponse:
        count, rows = await self.repository.list_display_overrides(org_id, limit, offset)
        return DisplayOverrideListResponse(
            total=count,
            limit=limit,
            offset=offset,
            data=[_display_override_response(override, concept, cs) for override, concept, cs in rows],
        )

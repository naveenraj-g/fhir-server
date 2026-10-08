"""HTTP implementation of TerminologyClient (app/terminology/client.py) —
used when settings.terminology.backend is "remote" (app/terminology/dispatch.py).
Calls a standalone terminology deployment's own /api/v1/terminology routes
(the same router this application mounts, app/routers/terminology/) — when
this service is actually extracted, the remote deployment is just another
copy of this same codebase, so the HTTP contract here is already real and
already exercised by this app's own test suite, not speculative.

Service-to-service identity for the org-scoped methods (create/get/patch/
delete/list org concepts and display overrides) is a known simplification,
not a solved problem: the receiving router today reads org_id/user_id from
the caller's own verified JWT (request.state.user), not from a header a
server-to-server caller could set on its own authority. Forwarded here as
X-Org-Id/X-User-Id headers as a placeholder only — a real extraction needs
real service-to-service credentials (e.g. forwarding the original JWT, or a
dedicated service token) before this path actually works end-to-end against
today's router. Not built further here since nothing calls these particular
methods yet, same as TerminologyService's own currently-uncalled-internally
status."""

import httpx

from app.schemas.terminology import (
    AddConceptMapRequest,
    AuditLogListResponse,
    CodeSystemListResponse,
    ConceptMapListResponse,
    ConceptsForFieldResponse,
    CreateConceptRequest,
    CreateDisplayOverrideRequest,
    DisplayOverrideListResponse,
    DisplayOverrideResponse,
    LookupBatchRequest,
    LookupBatchResponse,
    LookupRequest,
    LookupResult,
    OrgConceptListResponse,
    OrgConceptResponse,
    PatchConceptRequest,
    PatchDisplayOverrideRequest,
    SearchResponse,
    TranslateRequest,
    TranslateResponse,
    ValidateRequest,
    ValidateResponse,
    ValueSetExpandResponse,
    ValueSetListResponse,
)


class RemoteTerminologyClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=f"{self._base_url}/api/v1/terminology", timeout=self._timeout
        )

    async def list_code_systems(self) -> CodeSystemListResponse:
        async with self._client() as client:
            resp = await client.get("/code-systems")
            resp.raise_for_status()
            return CodeSystemListResponse.model_validate(resp.json())

    async def list_value_sets(
        self, q: str | None, limit: int, offset: int
    ) -> ValueSetListResponse:
        async with self._client() as client:
            resp = await client.get(
                "/value-sets", params={"q": q, "limit": limit, "offset": offset}
            )
            resp.raise_for_status()
            return ValueSetListResponse.model_validate(resp.json())

    async def expand_value_set(
        self, value_set_id: int, q: str | None, limit: int, offset: int
    ) -> ValueSetExpandResponse | None:
        async with self._client() as client:
            resp = await client.get(
                f"/value-sets/{value_set_id}/expand",
                params={"q": q, "limit": limit, "offset": offset},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return ValueSetExpandResponse.model_validate(resp.json())

    async def search_concepts(
        self, q: str, system: str | None, limit: int, offset: int
    ) -> SearchResponse:
        async with self._client() as client:
            resp = await client.get(
                "/search", params={"q": q, "system": system, "limit": limit, "offset": offset}
            )
            resp.raise_for_status()
            return SearchResponse.model_validate(resp.json())

    async def lookup(self, req: LookupRequest) -> LookupResult:
        async with self._client() as client:
            resp = await client.post("/lookup", json=req.model_dump())
            resp.raise_for_status()
            return LookupResult.model_validate(resp.json())

    async def lookup_batch(self, req: LookupBatchRequest) -> LookupBatchResponse:
        async with self._client() as client:
            resp = await client.post("/lookup-batch", json=req.model_dump())
            resp.raise_for_status()
            return LookupBatchResponse.model_validate(resp.json())

    async def get_concepts_for_field(
        self, resource: str, field: str, q: str | None, limit: int, offset: int
    ) -> ConceptsForFieldResponse:
        async with self._client() as client:
            resp = await client.get(
                "/concepts",
                params={
                    "resource": resource,
                    "field": field,
                    "q": q,
                    "limit": limit,
                    "offset": offset,
                },
            )
            resp.raise_for_status()
            return ConceptsForFieldResponse.model_validate(resp.json())

    async def translate(self, req: TranslateRequest) -> TranslateResponse:
        async with self._client() as client:
            resp = await client.post("/translate", json=req.model_dump())
            resp.raise_for_status()
            return TranslateResponse.model_validate(resp.json())

    async def list_concept_maps(
        self,
        source_system: str | None,
        target_system: str | None,
        limit: int,
        offset: int,
    ) -> ConceptMapListResponse:
        async with self._client() as client:
            resp = await client.get(
                "/concept-maps",
                params={
                    "source_system": source_system,
                    "target_system": target_system,
                    "limit": limit,
                    "offset": offset,
                },
            )
            resp.raise_for_status()
            return ConceptMapListResponse.model_validate(resp.json())

    async def add_concept_map(self, req: AddConceptMapRequest) -> dict:
        async with self._client() as client:
            resp = await client.post("/concept-maps", json=req.model_dump())
            resp.raise_for_status()
            return resp.json()

    async def create_concept(
        self, req: CreateConceptRequest, org_id: str, user_id: str | None
    ) -> OrgConceptResponse | None:
        async with self._client() as client:
            headers = {"X-Org-Id": org_id}
            if user_id:
                headers["X-User-Id"] = user_id
            resp = await client.post(
                "/org-concepts", json=req.model_dump(), headers=headers
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return OrgConceptResponse.model_validate(resp.json())

    async def get_org_concept(
        self, concept_id: int, org_id: str
    ) -> OrgConceptResponse | None:
        async with self._client() as client:
            resp = await client.get(
                f"/org-concepts/{concept_id}", headers={"X-Org-Id": org_id}
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return OrgConceptResponse.model_validate(resp.json())

    async def patch_concept(
        self, concept_id: int, req: PatchConceptRequest, org_id: str
    ) -> OrgConceptResponse | None:
        async with self._client() as client:
            resp = await client.patch(
                f"/org-concepts/{concept_id}",
                json=req.model_dump(exclude_unset=True),
                headers={"X-Org-Id": org_id},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return OrgConceptResponse.model_validate(resp.json())

    async def delete_concept(self, concept_id: int, org_id: str) -> bool:
        async with self._client() as client:
            resp = await client.delete(
                f"/org-concepts/{concept_id}", headers={"X-Org-Id": org_id}
            )
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            return True

    async def list_org_concepts(
        self,
        org_id: str,
        code_system_url: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> OrgConceptListResponse:
        async with self._client() as client:
            resp = await client.get(
                "/org-concepts",
                params={
                    "code_system_url": code_system_url,
                    "q": q,
                    "limit": limit,
                    "offset": offset,
                },
                headers={"X-Org-Id": org_id},
            )
            resp.raise_for_status()
            return OrgConceptListResponse.model_validate(resp.json())

    async def list_audit_log(
        self,
        action: str | None,
        performed_by: str | None,
        concept_id: int | None,
        limit: int,
        offset: int,
    ) -> AuditLogListResponse:
        async with self._client() as client:
            resp = await client.get(
                "/audit-log",
                params={
                    "action": action,
                    "performed_by": performed_by,
                    "concept_id": concept_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
            resp.raise_for_status()
            return AuditLogListResponse.model_validate(resp.json())

    async def validate(self, req: ValidateRequest) -> ValidateResponse:
        async with self._client() as client:
            resp = await client.post("/validate", json=req.model_dump())
            resp.raise_for_status()
            return ValidateResponse.model_validate(resp.json())

    async def create_display_override(
        self, req: CreateDisplayOverrideRequest, org_id: str, user_id: str | None
    ) -> DisplayOverrideResponse | None:
        async with self._client() as client:
            headers = {"X-Org-Id": org_id}
            if user_id:
                headers["X-User-Id"] = user_id
            resp = await client.post(
                "/display-overrides", json=req.model_dump(), headers=headers
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return DisplayOverrideResponse.model_validate(resp.json())

    async def get_display_override(
        self, override_id: int, org_id: str
    ) -> DisplayOverrideResponse | None:
        async with self._client() as client:
            resp = await client.get(
                f"/display-overrides/{override_id}", headers={"X-Org-Id": org_id}
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return DisplayOverrideResponse.model_validate(resp.json())

    async def patch_display_override(
        self, override_id: int, req: PatchDisplayOverrideRequest, org_id: str
    ) -> DisplayOverrideResponse | None:
        async with self._client() as client:
            resp = await client.patch(
                f"/display-overrides/{override_id}",
                json=req.model_dump(exclude_unset=True),
                headers={"X-Org-Id": org_id},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return DisplayOverrideResponse.model_validate(resp.json())

    async def delete_display_override(self, override_id: int, org_id: str) -> bool:
        async with self._client() as client:
            resp = await client.delete(
                f"/display-overrides/{override_id}", headers={"X-Org-Id": org_id}
            )
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            return True

    async def list_display_overrides(
        self, org_id: str, limit: int, offset: int
    ) -> DisplayOverrideListResponse:
        async with self._client() as client:
            resp = await client.get(
                "/display-overrides",
                params={"limit": limit, "offset": offset},
                headers={"X-Org-Id": org_id},
            )
            resp.raise_for_status()
            return DisplayOverrideListResponse.model_validate(resp.json())

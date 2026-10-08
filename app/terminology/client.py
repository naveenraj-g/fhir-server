"""Protocol every terminology backend must satisfy — TerminologyService
(embedded, app/services/terminology/) and RemoteTerminologyClient
(remote, app/terminology/remote_client.py) both implement this exactly, so
app/terminology/dispatch.py can swap between them with zero special-casing
at any call site. Mirrors TerminologyService's own public method
signatures one-for-one; see that class for what each one actually does."""

from typing import Protocol

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


class TerminologyClient(Protocol):
    async def list_code_systems(self) -> CodeSystemListResponse: ...

    async def list_value_sets(
        self, q: str | None, limit: int, offset: int
    ) -> ValueSetListResponse: ...

    async def expand_value_set(
        self, value_set_id: int, q: str | None, limit: int, offset: int
    ) -> ValueSetExpandResponse | None: ...

    async def search_concepts(
        self, q: str, system: str | None, limit: int, offset: int
    ) -> SearchResponse: ...

    async def lookup(self, req: LookupRequest) -> LookupResult: ...

    async def lookup_batch(self, req: LookupBatchRequest) -> LookupBatchResponse: ...

    async def get_concepts_for_field(
        self, resource: str, field: str, q: str | None, limit: int, offset: int
    ) -> ConceptsForFieldResponse: ...

    async def translate(self, req: TranslateRequest) -> TranslateResponse: ...

    async def list_concept_maps(
        self,
        source_system: str | None,
        target_system: str | None,
        limit: int,
        offset: int,
    ) -> ConceptMapListResponse: ...

    async def add_concept_map(self, req: AddConceptMapRequest) -> dict: ...

    async def create_concept(
        self, req: CreateConceptRequest, org_id: str, user_id: str | None
    ) -> OrgConceptResponse | None: ...

    async def get_org_concept(
        self, concept_id: int, org_id: str
    ) -> OrgConceptResponse | None: ...

    async def patch_concept(
        self, concept_id: int, req: PatchConceptRequest, org_id: str
    ) -> OrgConceptResponse | None: ...

    async def delete_concept(self, concept_id: int, org_id: str) -> bool: ...

    async def list_org_concepts(
        self,
        org_id: str,
        code_system_url: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> OrgConceptListResponse: ...

    async def list_audit_log(
        self,
        action: str | None,
        performed_by: str | None,
        concept_id: int | None,
        limit: int,
        offset: int,
    ) -> AuditLogListResponse: ...

    async def create_display_override(
        self, req: CreateDisplayOverrideRequest, org_id: str, user_id: str | None
    ) -> DisplayOverrideResponse | None: ...

    async def get_display_override(
        self, override_id: int, org_id: str
    ) -> DisplayOverrideResponse | None: ...

    async def patch_display_override(
        self, override_id: int, req: PatchDisplayOverrideRequest, org_id: str
    ) -> DisplayOverrideResponse | None: ...

    async def delete_display_override(self, override_id: int, org_id: str) -> bool: ...

    async def list_display_overrides(
        self, org_id: str, limit: int, offset: int
    ) -> DisplayOverrideListResponse: ...

    async def validate(self, req: ValidateRequest) -> ValidateResponse: ...

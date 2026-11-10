"""Protocol every terminology backend must satisfy — TerminologyService
(embedded, app/services/terminology/) and RemoteTerminologyClient
(remote, app/terminology/remote_client.py) both implement this exactly, so
app/terminology/dispatch.py can swap between them with zero special-casing
at any call site. Mirrors TerminologyService's own public method
signatures one-for-one; see that class for what each one actually does."""

from typing import Protocol

from app.schemas.terminology import (
    AddConceptMapRequest,
    CodeSystemListResponse,
    ConceptMapListResponse,
    ConceptsForFieldResponse,
    CreateConceptRequest,
    LookupBatchRequest,
    LookupBatchResponse,
    LookupRequest,
    LookupResult,
    OrgConceptListResponse,
    OrgConceptResponse,
    PatchConceptRequest,
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

    async def validate(self, req: ValidateRequest) -> ValidateResponse: ...

    # ------------------------------------------------------------------
    # Real FHIR R4 `$`-operations — see
    # docs/terminology-service/09-fhir-r4-terminology-standard-reference.md.
    # Every one returns a plain dict already shaped as the operation's
    # FHIR `Parameters`/`ValueSet`/`ConceptMap` response body (see
    # app/fhir/parameters.py for why there's no Pydantic model here).
    # ------------------------------------------------------------------

    async def lookup_operation(
        self,
        *,
        system: str | None,
        code: str | None,
        coding: dict | None,
        properties: list[str] | None,
    ) -> dict: ...

    async def validate_code_on_codesystem_operation(
        self,
        *,
        url: str | None,
        code: str | None,
        version: str | None,
        display: str | None,
        coding: dict | None,
        codeable_concept: dict | None,
    ) -> dict: ...

    async def subsumes_operation(
        self,
        *,
        code_a: str | None,
        code_b: str | None,
        system: str | None,
        coding_a: dict | None,
        coding_b: dict | None,
    ) -> dict: ...

    async def find_matches_operation(
        self,
        *,
        system: str | None,
        version: str | None,
        properties: list[dict],
        exact: bool | None,
        compositional: bool | None,
    ) -> dict: ...

    async def expand_operation(
        self,
        *,
        value_set_id: int | None,
        url: str | None,
        value_set_version: str | None,
        filter_text: str | None,
        offset: int,
        count: int,
    ) -> dict: ...

    async def validate_code_on_valueset_operation(
        self,
        *,
        value_set_id: int | None,
        url: str | None,
        value_set_version: str | None,
        code: str | None,
        system: str | None,
        display: str | None,
    ) -> dict: ...

    async def translate_operation(
        self, system: str, code: str, targetsystem: str | None, reverse: bool
    ) -> dict: ...

    async def closure_operation(
        self, name: str, concepts: list[dict], version: str | None
    ) -> dict: ...

    async def get_terminology_capabilities(self) -> dict: ...

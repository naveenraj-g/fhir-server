from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.terminology.enums import ConceptMapEquivalence


class CodeSystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    canonical_url: str
    name: str
    title: str | None = None
    version: str | None = None
    publisher: str | None = None
    content_mode: str | None = None
    active: bool


class ConceptResponse(BaseModel):
    id: int
    code: str
    display: str
    definition: str | None = None
    active: bool
    system: str
    system_name: str


class ValueSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    canonical_url: str
    name: str
    title: str | None = None
    description: str | None = None
    version: str | None = None
    binding_strength: str
    active: bool


class CodeSystemListResponse(BaseModel):
    total: int
    data: list[CodeSystemResponse]


class ValueSetListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ValueSetResponse]


class ValueSetExpandResponse(BaseModel):
    value_set: ValueSetResponse
    total: int
    limit: int
    offset: int
    concepts: list[ConceptResponse]


class SearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ConceptResponse]


class LookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: str
    code: str


class LookupResult(BaseModel):
    found: bool
    concept: ConceptResponse | None = None
    code_system: CodeSystemResponse | None = None


class LookupBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[LookupRequest]


class LookupBatchResponse(BaseModel):
    results: list[LookupResult]


class ConceptsForFieldResponse(BaseModel):
    resource: str
    field: str
    value_set: ValueSetResponse | None = None
    binding_strength: str | None = None
    multiple_allowed: bool = False
    total: int
    limit: int
    offset: int
    concepts: list[ConceptResponse]


class ValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource: str
    field: str
    system: str
    code: str


class ValidateResponse(BaseModel):
    valid: bool
    in_value_set: bool
    binding_strength: str | None = None
    concept: ConceptResponse | None = None
    value_set: ValueSetResponse | None = None
    message: str


class TranslationResult(BaseModel):
    concept: ConceptResponse
    equivalence: ConceptMapEquivalence
    confidence: float | None = None


class TranslateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: str
    code: str
    target_system: str


class TranslateResponse(BaseModel):
    source_concept: ConceptResponse | None = None
    source_system: str
    source_code: str
    target_system: str
    translations: list[TranslationResult]
    found: bool


class ConceptMapRecord(BaseModel):
    id: int
    source_concept: ConceptResponse
    target_concept: ConceptResponse
    equivalence: ConceptMapEquivalence
    confidence: float | None = None


class ConceptMapListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ConceptMapRecord]


class AddConceptMapRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "source_system": "http://snomed.info/sct",
                "source_code": "38341003",
                "target_system": "http://hl7.org/fhir/sid/icd-10-cm",
                "target_code": "I10",
                "equivalence": "equivalent",
                "confidence": 1.0,
            }
        },
    )
    source_system: str
    source_code: str
    target_system: str
    target_code: str
    equivalence: ConceptMapEquivalence = ConceptMapEquivalence.equivalent
    confidence: float | None = None


class CreateConceptRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "code_system_url": "http://example.org/custom-codes",
                "code": "CUSTOM-01",
                "display": "Custom Finding",
                "definition": "Custom clinical finding description",
            }
        },
    )
    code_system_url: str
    code: str
    display: str
    definition: str | None = None


class PatchConceptRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "display": "Updated Finding Display",
                "definition": "Updated clinical finding definition",
            }
        },
    )
    display: str | None = None
    definition: str | None = None


class OrgConceptResponse(ConceptResponse):
    user_id: str | None = None
    org_id: str | None = None
    created_at: datetime | None = None


class OrgConceptListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[OrgConceptResponse]



from app.schemas.terminology import (
    AddConceptMapRequest,
    ConceptMapListResponse,
    ConceptMapRecord,
)

from ._shared import _concept_response


class _ConceptMapsMixin:
    async def list_concept_maps(
        self,
        source_system: str | None,
        target_system: str | None,
        limit: int,
        offset: int,
    ) -> ConceptMapListResponse:
        count, rows = await self.repository.list_concept_maps(
            source_system, target_system, limit, offset
        )
        data = [
            ConceptMapRecord(
                id=cm.id,
                source_concept=_concept_response(src_concept, src_cs),
                target_concept=_concept_response(tgt_concept, tgt_cs),
                mapping_type=cm.mapping_type,
                confidence=cm.confidence,
            )
            for cm, src_concept, src_cs, tgt_concept, tgt_cs in rows
        ]
        return ConceptMapListResponse(
            total=count, limit=limit, offset=offset, data=data
        )

    async def add_concept_map(self, req: AddConceptMapRequest) -> dict:
        src_cs, src_concept = await self.repository.lookup_concept(
            req.source_system, req.source_code
        )
        if src_concept is None:
            return {
                "inserted": False,
                "error": f"Source concept not found: {req.source_system}|{req.source_code}",
            }
        tgt_cs, tgt_concept = await self.repository.lookup_concept(
            req.target_system, req.target_code
        )
        if tgt_concept is None:
            return {
                "inserted": False,
                "error": f"Target concept not found: {req.target_system}|{req.target_code}",
            }
        inserted = await self.repository.add_concept_map(
            src_concept.id, tgt_concept.id, req.mapping_type, req.confidence
        )
        return {
            "inserted": inserted,
            "source": _concept_response(src_concept, src_cs).model_dump(),
            "target": _concept_response(tgt_concept, tgt_cs).model_dump(),
            "mapping_type": req.mapping_type,
            "confidence": req.confidence,
        }

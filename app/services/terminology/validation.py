from app.schemas.terminology import (
    TranslateRequest,
    TranslateResponse,
    TranslationResult,
    ValidateRequest,
    ValidateResponse,
)

from ._shared import _concept_response, _vs_response


class _ValidationMixin:
    async def validate(self, req: ValidateRequest) -> ValidateResponse:
        binding = await self.repository.get_field_binding(req.resource, req.field)
        if binding is None:
            cs, concept = await self.repository.lookup_concept(req.system, req.code)
            return ValidateResponse(
                valid=True,
                in_value_set=False,
                concept=_concept_response(concept, cs) if concept else None,
                message=f"No value set bound to {req.resource}.{req.field} — code accepted as-is.",
            )
        vs = await self.repository.get_value_set(binding.value_set_id)
        cs, concept, in_vs = await self.repository.lookup_concept_in_value_set(
            binding.value_set_id, req.system, req.code
        )
        strength = binding.binding_strength
        if in_vs:
            valid = True
            message = f"Code '{req.code}' is valid for {req.resource}.{req.field}."
        elif strength == "required":
            valid = False
            message = (
                f"Code '{req.code}' is NOT in the required value set for {req.resource}.{req.field}. "
                f"Value set: {vs.canonical_url if vs else 'unknown'}."
            )
        else:
            valid = True
            message = (
                f"Code '{req.code}' is not in the {strength} value set for {req.resource}.{req.field}, "
                "but is allowed as an extension."
            )
        return ValidateResponse(
            valid=valid,
            in_value_set=in_vs,
            binding_strength=strength,
            concept=_concept_response(concept, cs) if concept else None,
            value_set=_vs_response(vs) if vs else None,
            message=message,
        )

    async def translate(self, req: TranslateRequest) -> TranslateResponse:
        src_cs, src_concept = await self.repository.lookup_concept(req.system, req.code)
        if src_concept is None:
            return TranslateResponse(
                source_system=req.system,
                source_code=req.code,
                target_system=req.target_system,
                translations=[],
                found=False,
            )
        rows = await self.repository.get_translations(src_concept.id, req.target_system)
        translations = [
            TranslationResult(
                concept=_concept_response(tgt_concept, tgt_cs),
                mapping_type=cm.mapping_type,
                confidence=cm.confidence,
            )
            for cm, tgt_concept, tgt_cs in rows
        ]
        return TranslateResponse(
            source_concept=_concept_response(src_concept, src_cs),
            source_system=req.system,
            source_code=req.code,
            target_system=req.target_system,
            translations=translations,
            found=True,
        )

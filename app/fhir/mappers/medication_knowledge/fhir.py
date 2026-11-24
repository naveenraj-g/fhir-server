"""MedicationKnowledgeModel row -> FHIR R4 MedicationKnowledge. The only
read-side mapper.

The resource is stored whole in MedicationKnowledgeModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication_knowledge import MedicationKnowledgeModel


def to_fhir_medication_knowledge(
    medication_knowledge: MedicationKnowledgeModel,
) -> dict:
    return content_resource(
        "MedicationKnowledge",
        medication_knowledge.medication_knowledge_id,
        medication_knowledge,
    )

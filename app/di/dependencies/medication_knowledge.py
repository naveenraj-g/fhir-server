from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.medication_knowledge import MedicationKnowledgeService


@inject
def get_medication_knowledge_service(
    service: MedicationKnowledgeService = Depends(
        Provide[Container.medication_knowledge.medication_knowledge_service]
    ),
) -> MedicationKnowledgeService:
    return service

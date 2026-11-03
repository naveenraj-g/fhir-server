from dependency_injector import containers, providers

from app.repository.medication_knowledge import MedicationKnowledgeRepository
from app.services.medication_knowledge import MedicationKnowledgeService


class MedicationKnowledgeContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    medication_knowledge_repository = providers.Factory(
        MedicationKnowledgeRepository, session_factory=core.database.provided.session
    )
    medication_knowledge_service = providers.Factory(
        MedicationKnowledgeService, repository=medication_knowledge_repository
    )

from dependency_injector import containers, providers

from app.core.cache.factory import get_cache_backend
from app.core.config import settings
from app.repository.fhir_profile import FhirProfileRepository
from app.services.fhir_profile import FhirProfileService


class FhirProfileContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()

    fhir_profile_repository = providers.Factory(
        FhirProfileRepository,
        session_factory=core.database.provided.session,
    )

    # Singleton, not Factory: the memory backend only caches anything
    # across calls if every caller shares the same instance (see
    # app/core/cache/factory.py's module-level _memory_backend for the
    # redis-unavailable/"memory" case specifically).
    cache_backend = providers.Singleton(
        get_cache_backend,
        backend=settings.fhir_profile_cache.backend,
    )

    fhir_profile_service = providers.Factory(
        FhirProfileService,
        repository=fhir_profile_repository,
        cache_backend=cache_backend,
    )

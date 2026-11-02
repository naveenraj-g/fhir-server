from app.repository.base import BaseRepository
from app.repository.specimen_definition.core import _CoreMixin
from app.repository.specimen_definition.full import _FullMixin


class SpecimenDefinitionRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing SpecimenDefinition persistence and queries."""


__all__ = ["SpecimenDefinitionRepository"]

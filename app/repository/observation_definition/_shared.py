from sqlalchemy.orm import selectinload

from app.models.observation_definition import ObservationDefinitionModel
from app.repository._reference_shared import _validate_reference

__all__ = ["INDEX_RELATIONSHIPS", "_validate_reference", "_with_relationships"]

# Relationship attributes the search index owns - every one is rebuilt on each write. R4 defines
# no search parameter for ObservationDefinition, so there is none.
INDEX_RELATIONSHIPS: tuple[str, ...] = ()


def _with_relationships(stmt):
    """Eager-load the search-index child rows (none) - kept so every resource's repository reads
    the same way; reads never touch index rows, since every response is served straight from
    ObservationDefinitionModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(ObservationDefinitionModel, rel))
            for rel in INDEX_RELATIONSHIPS
        )
    )

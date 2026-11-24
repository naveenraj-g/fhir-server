from sqlalchemy.orm import selectinload

from app.models.specimen_definition import SpecimenDefinitionModel
from app.repository._reference_shared import _validate_reference

__all__ = ["INDEX_RELATIONSHIPS", "_validate_reference", "_with_relationships"]

# Relationship attributes the search index owns - every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is about to replace them
    (patch_full) - reads never touch them, since every response is served straight from
    SpecimenDefinitionModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(SpecimenDefinitionModel, rel))
            for rel in INDEX_RELATIONSHIPS
        )
    )

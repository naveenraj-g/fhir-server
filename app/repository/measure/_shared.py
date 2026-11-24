import re

from sqlalchemy.orm import selectinload

from app.models.measure import MeasureModel
from app.repository._reference_shared import _validate_reference

__all__ = [
    "INDEX_RELATIONSHIPS",
    "_validate_reference",
    "_with_relationships",
    "any_typed",
    "typed",
]

# Relationship attributes the search index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "references", "context_quantities")

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from MeasureModel.content."""
    return stmt.options(
        *(selectinload(getattr(MeasureModel, rel)) for rel in INDEX_RELATIONSHIPS)
    )


def typed(reference: str | None, allowed: tuple[str, ...]) -> tuple[str, int] | None:
    """('Patient', 10001) for a relative `Type/<id>` whose type is in `allowed`; None for
    an absolute URL, a contained reference or any other shape (those match by their raw
    string only)."""
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None


def any_typed(reference: str | None) -> tuple[str, int] | None:
    """`typed()` for a Reference(Any): any relative `Type/<id>` names a type."""
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match else None

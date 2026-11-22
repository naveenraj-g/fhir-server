import re

from sqlalchemy.orm import selectinload

from app.models.medication import REFERENCE_TYPES, MedicationModel
from app.repository._reference_shared import _validate_reference

__all__ = [
    "INDEX_RELATIONSHIPS",
    "_validate_reference",
    "_with_relationships",
    "any_typed",
    "ref_type_and_id",
    "typed",
]

# Relationship attributes the search index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = (
    "identifiers",
    "tokens",
    "references",
)

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from MedicationModel.content."""
    return stmt.options(
        *(selectinload(getattr(MedicationModel, rel)) for rel in INDEX_RELATIONSHIPS)
    )


def typed(reference: str | None, allowed: tuple[str, ...]) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` whose type is in
    `allowed`; None for an absolute URL, a contained reference or any other
    shape (those match by their raw string only)."""
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None


def ref_type_and_id(reference: str | None, param: str) -> tuple[str, int] | None:
    """`typed()` for the targets the reference-table parameter `param` allows."""
    return typed(reference, REFERENCE_TYPES[param])


def any_typed(reference: str | None) -> tuple[str, int] | None:
    """`typed()` for a Reference(Any): any relative `Type/<id>` names a type."""
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match else None

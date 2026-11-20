import re

from sqlalchemy.orm import selectinload

from app.models.immunization import ImmunizationModel
from app.repository._reference_shared import _validate_reference

__all__ = ["INDEX_RELATIONSHIPS", "_validate_reference", "_with_relationships", "typed"]

# Relationship attributes the search index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "protocols", "reactions", "performers", "reason_references")

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from ImmunizationModel.content."""
    return stmt.options(*(selectinload(getattr(ImmunizationModel, rel)) for rel in INDEX_RELATIONSHIPS))


def typed(reference: str | None, allowed: tuple[str, ...]) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` whose type is in
    `allowed`; None for an absolute URL, a contained reference or any other
    shape (those match by their raw string only)."""
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None

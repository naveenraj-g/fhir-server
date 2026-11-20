import re

from sqlalchemy.orm import selectinload

from app.models.encounter import REFERENCE_TYPES, EncounterModel
from app.repository._reference_shared import _validate_reference

__all__ = [
    "INDEX_RELATIONSHIPS",
    "MODELED_PARTICIPANT_TYPES",
    "_validate_reference",
    "_with_relationships",
    "ref_type_and_id",
    "typed",
]

# Relationship attributes the search index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "references", "participants", "locations")

# Of the three Encounter.participant.individual target types, these are
# resources on this server. A relative RelatedPerson reference is accepted and
# indexed but not existence-checked.
MODELED_PARTICIPANT_TYPES = {"Practitioner", "PractitionerRole"}

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from EncounterModel.content."""
    return stmt.options(*(selectinload(getattr(EncounterModel, rel)) for rel in INDEX_RELATIONSHIPS))


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

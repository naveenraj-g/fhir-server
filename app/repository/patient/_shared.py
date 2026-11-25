import re

from sqlalchemy.orm import selectinload

from app.models.patient import REFERENCE_TYPES, PatientModel
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "MODELED_TYPES",
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
    "ref_type_and_id",
]

# Of the types Patient's reference elements can point at, these are resources
# on this server (registered in RESOURCE_REGISTRY — see
# app/core/reference_resolver.py). Every one is registered, so a
# relative reference to one is existence-checked on write.
MODELED_TYPES = {
    "Organization",
    "Practitioner",
    "PractitionerRole",
    "Patient",
    "RelatedPerson",
}

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from PatientModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(PatientModel, rel))
            for rel in (
                "identifiers",
                "names",
                "telecoms",
                "addresses",
                "communications",
                "references",
            )
        )
    )


def ref_type_and_id(reference: str | None, param: str) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` naming one of the
    types the search parameter `param` (general-practitioner | link) allows;
    None for an absolute URL, a contained reference or any other shape (those
    match by their raw string only)."""
    match = _REF.match(reference or "")
    if match and match["type"] in REFERENCE_TYPES[param]:
        return match["type"], int(match["id"])
    return None

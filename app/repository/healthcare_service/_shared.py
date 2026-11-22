from sqlalchemy.orm import selectinload

from app.models.healthcare_service import (
    HealthcareServiceModel,
)
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from HealthcareServiceModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(HealthcareServiceModel, rel))
            for rel in ("identifiers", "tokens", "references")
        )
    )

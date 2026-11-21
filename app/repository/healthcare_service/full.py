from sqlalchemy import select

from app.core.logging import get_logger
from app.models.healthcare_service import HealthcareServiceModel

from ._indexer import (
    INDEX_RELATIONSHIPS,
    index_columns,
    endpoint_references,
    index_rows,
    location_references,
    organization_references,
)
from ._shared import (
    _parse_endpoint_ref,
    _parse_location_ref,
    _parse_org_ref,
    _validate_reference,
    _with_relationships,
)

logger = get_logger(__name__)

# Never stored in `content` — stamped on at read time from the row.
_SERVER_MANAGED = ("resourceType", "id", "meta")


def _storable(document: dict) -> dict:
    return {k: v for k, v in document.items() if k not in _SERVER_MANAGED}


async def _validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Existence-check every relative local reference in the document —
    Reference(Organization) in providedBy / identifier.assigner and
    Reference(Location) in location[] / coverageArea[] and Reference(Endpoint)
    in endpoint[] — scoped to the caller's org; 422 if one doesn't resolve."""
    for label, ref in organization_references(document):
        ref_type, ref_id = _parse_org_ref(ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, label)
    for label, ref in location_references(document):
        ref_type, ref_id = _parse_location_ref(ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, label)
    for ref in endpoint_references(document):
        ref_type, ref_id = _parse_endpoint_ref(ref)
        await _validate_reference(session, tenant_id, ref_type, ref_id, "endpoint")


class _FullMixin:
    """Writes. Both take the full, already-validated FHIR HealthcareService
    document: it's stored verbatim in `content`, and the search index is
    rebuilt from it (see _indexer.py)."""

    async def create_full(
        self,
        document: dict,
        org_id: str,
        created_by: str | None = None,
    ) -> HealthcareServiceModel:
        async with self.session_factory() as session:
            await _validate_local_references(session, org_id, document)
            healthcare_service = HealthcareServiceModel(
                tenant_id=org_id,
                created_by=created_by,
                content=_storable(document),
                **index_columns(document),
                **index_rows(document),
            )
            session.add(healthcare_service)
            try:
                await session.commit()
                await session.refresh(healthcare_service)
            except Exception:
                await session.rollback()
                raise
            return healthcare_service

    async def patch_full(
        self,
        healthcare_service_id: int,
        document: dict,
        updated_by: str | None = None,
    ) -> HealthcareServiceModel | None:
        """`document` is the resource as it should look *after* the patch
        (the service merges the patch onto the current content and validates
        the result). The stored content is replaced and every index row
        rebuilt."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(HealthcareServiceModel).where(
                    HealthcareServiceModel.healthcare_service_id
                    == healthcare_service_id
                )
            )
            healthcare_service = (await session.execute(stmt)).scalars().first()
            if not healthcare_service:
                return None

            await _validate_local_references(
                session, healthcare_service.tenant_id, document
            )

            healthcare_service.content = _storable(document)
            for column, value in index_columns(document).items():
                setattr(healthcare_service, column, value)
            rows = index_rows(document)
            for rel in INDEX_RELATIONSHIPS:
                setattr(healthcare_service, rel, rows[rel])
            if updated_by is not None:
                healthcare_service.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(healthcare_service)
            except Exception:
                await session.rollback()
                raise
            return healthcare_service

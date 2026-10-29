from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.encounter import (
    EncounterIdentifier,
    EncounterModel,
    EncounterStatus,
    EncounterType,
    EncounterTypeCoding,
)

from ._shared import _parse_ref, _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Encounter parent row (no sub-resources)."""

    async def get_by_encounter_id(self, encounter_id: int) -> EncounterModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_encounter_id_in_org(
        self, encounter_id: int, org_id: str
    ) -> EncounterModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns
        None unless the encounter exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(
                    EncounterModel.encounter_id == encounter_id,
                    EncounterModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def encounter_belongs_to_org(self, encounter_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for
        tenant-ownership gates on write routes."""
        async with self.session_factory() as session:
            stmt = select(EncounterModel.id).where(
                EncounterModel.encounter_id == encounter_id,
                EncounterModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        status: EncounterStatus | None = None,
        identifier: str | None = None,
        subject: str | None = None,
        class_code: str | None = None,
        type_code: str | None = None,
        service_provider: str | None = None,
        part_of: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(EncounterModel.tenant_id == org_id)
        stmt = apply_token_filter(stmt, EncounterModel.status, status)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(EncounterIdentifier.id).where(
                    EncounterIdentifier.encounter_pk == EncounterModel.id,
                    EncounterIdentifier.value == identifier,
                ),
            )
        if subject:
            from app.models.enums import SubjectReferenceType

            s_type, s_id = _parse_ref(subject, SubjectReferenceType)
            stmt = stmt.where(
                EncounterModel.subject_type == s_type, EncounterModel.subject_id == s_id
            )
        if class_code:
            stmt = stmt.where(EncounterModel.class_code == class_code)
        if type_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(EncounterTypeCoding.id)
                .join(EncounterType, EncounterTypeCoding.encounter_type_id == EncounterType.id)
                .where(
                    EncounterType.encounter_pk == EncounterModel.id,
                    EncounterTypeCoding.code == type_code,
                ),
            )
        if service_provider:
            from app.models.enums import OrganizationReferenceType

            sp_type, sp_id = _parse_ref(service_provider, OrganizationReferenceType)
            stmt = stmt.where(
                EncounterModel.service_provider_type == sp_type,
                EncounterModel.service_provider_id == sp_id,
            )
        if part_of:
            from app.models.enums import EncounterReferenceType

            po_type, po_id = _parse_ref(part_of, EncounterReferenceType)
            stmt = stmt.where(
                EncounterModel.part_of_type == po_type, EncounterModel.part_of_id == po_id
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: EncounterStatus | None = None,
        identifier: str | None = None,
        subject: str | None = None,
        class_code: str | None = None,
        type_code: str | None = None,
        service_provider: str | None = None,
        part_of: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[EncounterModel], int | None]:
        """Paginated, filtered, sorted list of encounters. Returns (rows,
        total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "identifier": identifier,
                "subject": subject,
                "class_code": class_code,
                "type_code": type_code,
                "service_provider": service_provider,
                "part_of": part_of,
            }
            base = self._apply_list_filters(
                _with_relationships(select(EncounterModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(EncounterModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=EncounterModel.encounter_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        logger.debug(
            "Encounters listed",
            extra={
                "event": "encounter.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    # ── Delete ────────────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Encounter has no separate
    # scalar-only variant, see EncounterCreateSchema's docstring.

    async def delete(self, encounter_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return False
            try:
                await session.delete(row)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

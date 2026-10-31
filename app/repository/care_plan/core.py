from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.care_plan import (
    CarePlanAddresses,
    CarePlanBasedOn,
    CarePlanCategory,
    CarePlanCategoryCoding,
    CarePlanGoal,
    CarePlanIdentifier,
    CarePlanModel,
    CarePlanPartOf,
    CarePlanReplaces,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_addresses_ref,
    _parse_author_ref,
    _parse_based_on_ref,
    _parse_encounter_ref,
    _parse_goal_ref,
    _parse_part_of_ref,
    _parse_replaces_ref,
    _parse_subject_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for CarePlan."""

    async def get_by_care_plan_id(self, care_plan_id: int) -> CarePlanModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CarePlanModel).where(CarePlanModel.care_plan_id == care_plan_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_care_plan_id_in_org(
        self, care_plan_id: int, org_id: str
    ) -> CarePlanModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CarePlanModel).where(
                    CarePlanModel.care_plan_id == care_plan_id,
                    CarePlanModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def care_plan_belongs_to_org(self, care_plan_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(CarePlanModel.id).where(
                CarePlanModel.care_plan_id == care_plan_id,
                CarePlanModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | None = None,
        intent: str | None = None,
        title: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        author: str | None = None,
        based_on: str | None = None,
        replaces: str | None = None,
        part_of: str | None = None,
        addresses: str | None = None,
        goal: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(CarePlanModel.tenant_id == org_id)
        if status:
            stmt = stmt.where(CarePlanModel.status == status)
        if intent:
            stmt = stmt.where(CarePlanModel.intent == intent)
        if title:
            stmt = stmt.where(CarePlanModel.title.ilike(f"%{title}%"))
        if category:
            stmt = apply_child_exists_filter(
                stmt,
                select(CarePlanCategoryCoding.id)
                .join(
                    CarePlanCategory,
                    CarePlanCategoryCoding.category_id == CarePlanCategory.id,
                )
                .where(
                    CarePlanCategory.care_plan_pk == CarePlanModel.id,
                    CarePlanCategoryCoding.code == category,
                ),
            )
        if subject:
            s_type, s_id = _parse_subject_ref(subject)
            if s_id:
                stmt = stmt.where(CarePlanModel.subject_id == s_id)
                if s_type:
                    stmt = stmt.where(CarePlanModel.subject_type == s_type)
            else:
                stmt = stmt.where(CarePlanModel.subject_reference == subject)
        if encounter:
            e_type, e_id = _parse_encounter_ref(encounter)
            if e_id:
                stmt = stmt.where(CarePlanModel.encounter_id == e_id)
            else:
                stmt = stmt.where(CarePlanModel.encounter_reference == encounter)
        if author:
            a_type, a_id = _parse_author_ref(author)
            if a_id:
                stmt = stmt.where(CarePlanModel.author_id == a_id)
                if a_type:
                    stmt = stmt.where(CarePlanModel.author_type == a_type)
            else:
                stmt = stmt.where(CarePlanModel.author_reference == author)
        if based_on:
            bo_type, bo_id = _parse_based_on_ref(based_on)
            if bo_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanBasedOn.id).where(
                        CarePlanBasedOn.care_plan_pk == CarePlanModel.id,
                        CarePlanBasedOn.reference_id == bo_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanBasedOn.id).where(
                        CarePlanBasedOn.care_plan_pk == CarePlanModel.id,
                        CarePlanBasedOn.reference_reference == based_on,
                    ),
                )
        if replaces:
            rep_type, rep_id = _parse_replaces_ref(replaces)
            if rep_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanReplaces.id).where(
                        CarePlanReplaces.care_plan_pk == CarePlanModel.id,
                        CarePlanReplaces.reference_id == rep_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanReplaces.id).where(
                        CarePlanReplaces.care_plan_pk == CarePlanModel.id,
                        CarePlanReplaces.reference_reference == replaces,
                    ),
                )
        if part_of:
            po_type, po_id = _parse_part_of_ref(part_of)
            if po_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanPartOf.id).where(
                        CarePlanPartOf.care_plan_pk == CarePlanModel.id,
                        CarePlanPartOf.reference_id == po_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanPartOf.id).where(
                        CarePlanPartOf.care_plan_pk == CarePlanModel.id,
                        CarePlanPartOf.reference_reference == part_of,
                    ),
                )
        if addresses:
            addr_type, addr_id = _parse_addresses_ref(addresses)
            if addr_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanAddresses.id).where(
                        CarePlanAddresses.care_plan_pk == CarePlanModel.id,
                        CarePlanAddresses.reference_id == addr_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanAddresses.id).where(
                        CarePlanAddresses.care_plan_pk == CarePlanModel.id,
                        CarePlanAddresses.reference_reference == addresses,
                    ),
                )
        if goal:
            g_type, g_id = _parse_goal_ref(goal)
            if g_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanGoal.id).where(
                        CarePlanGoal.care_plan_pk == CarePlanModel.id,
                        CarePlanGoal.reference_id == g_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(CarePlanGoal.id).where(
                        CarePlanGoal.care_plan_pk == CarePlanModel.id,
                        CarePlanGoal.reference_reference == goal,
                    ),
                )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(CarePlanIdentifier.id).where(
                    CarePlanIdentifier.care_plan_pk == CarePlanModel.id,
                    CarePlanIdentifier.value == identifier,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        intent: str | None = None,
        title: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        author: str | None = None,
        based_on: str | None = None,
        replaces: str | None = None,
        part_of: str | None = None,
        addresses: str | None = None,
        goal: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[CarePlanModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "status": status,
                "intent": intent,
                "title": title,
                "category": category,
                "subject": subject,
                "encounter": encounter,
                "author": author,
                "based_on": based_on,
                "replaces": replaces,
                "part_of": part_of,
                "addresses": addresses,
                "goal": goal,
                "identifier": identifier,
            }
            base = self._apply_list_filters(
                _with_relationships(select(CarePlanModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(CarePlanModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=CarePlanModel.care_plan_id,
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
            return list(rows), total

    async def delete(self, care_plan_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(CarePlanModel).where(CarePlanModel.care_plan_id == care_plan_id)
            care_plan = (await session.execute(stmt)).scalars().first()
            if not care_plan:
                return False
            await session.delete(care_plan)
            await session.commit()
            return True

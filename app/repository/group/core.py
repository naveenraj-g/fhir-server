from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.group import (
    GroupCharacteristic,
    GroupCharacteristicCodeCoding,
    GroupCharacteristicValueCoding,
    GroupCodeCoding,
    GroupIdentifier,
    GroupManagingEntityReferenceType,
    GroupMember,
    GroupMemberEntityReferenceType,
    GroupModel,
    GroupType,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_generic_ref,
    _parse_managing_entity_ref,
    _parse_member_entity_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Group."""

    async def get_by_group_id(self, group_id: int) -> GroupModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(GroupModel).where(GroupModel.group_id == group_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_group_id_in_org(
        self, group_id: int, org_id: str
    ) -> GroupModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(GroupModel).where(
                    GroupModel.group_id == group_id,
                    GroupModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def group_belongs_to_org(self, group_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(GroupModel.id).where(
                GroupModel.group_id == group_id,
                GroupModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        type: str | GroupType | None = None,
        actual: bool | None = None,
        active: bool | None = None,
        name: str | None = None,
        code: str | None = None,
        managing_entity: str | None = None,
        member: str | None = None,
        characteristic: str | None = None,
        characteristic_value: str | None = None,
        exclude: bool | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(GroupModel.tenant_id == org_id)
        if type:
            stmt = apply_token_filter(stmt, GroupModel.type, type)
        if actual is not None:
            stmt = stmt.where(GroupModel.actual == actual)
        if active is not None:
            stmt = stmt.where(GroupModel.active == active)
        if name:
            stmt = stmt.where(GroupModel.name.ilike(f"%{name}%"))

        if code:
            stmt = stmt.where(
                or_(
                    GroupModel.code_text.ilike(f"%{code}%"),
                    GroupModel.id.in_(
                        select(GroupCodeCoding.group_pk).where(
                            GroupCodeCoding.code == code
                        )
                    ),
                )
            )

        if managing_entity:
            me_type, me_id = _parse_managing_entity_ref(managing_entity)
            if me_id:
                stmt = stmt.where(GroupModel.managing_entity_id == me_id)
                if me_type:
                    stmt = stmt.where(GroupModel.managing_entity_type == me_type)
            else:
                stmt = stmt.where(
                    GroupModel.managing_entity_reference == managing_entity
                )

        if member:
            m_type, m_id = _parse_member_entity_ref(member)
            if m_id:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(GroupMember.id).where(
                        GroupMember.group_pk == GroupModel.id,
                        GroupMember.entity_id == m_id,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(GroupMember.id).where(
                        GroupMember.group_pk == GroupModel.id,
                        GroupMember.entity_reference == member,
                    ),
                )

        if characteristic:
            stmt = apply_child_exists_filter(
                stmt,
                select(GroupCharacteristic.id).where(
                    GroupCharacteristic.group_pk == GroupModel.id,
                    or_(
                        GroupCharacteristic.code_text.ilike(f"%{characteristic}%"),
                        GroupCharacteristic.id.in_(
                            select(GroupCharacteristicCodeCoding.characteristic_id).where(
                                GroupCharacteristicCodeCoding.code == characteristic
                            )
                        ),
                    ),
                ),
            )

        if characteristic_value:
            stmt = apply_child_exists_filter(
                stmt,
                select(GroupCharacteristic.id).where(
                    GroupCharacteristic.group_pk == GroupModel.id,
                    or_(
                        GroupCharacteristic.value_codeable_concept_text.ilike(
                            f"%{characteristic_value}%"
                        ),
                        GroupCharacteristic.id.in_(
                            select(GroupCharacteristicValueCoding.characteristic_id).where(
                                GroupCharacteristicValueCoding.code == characteristic_value
                            )
                        ),
                    ),
                ),
            )

        if exclude is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(GroupCharacteristic.id).where(
                    GroupCharacteristic.group_pk == GroupModel.id,
                    GroupCharacteristic.exclude == exclude,
                ),
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(GroupIdentifier.id).where(
                    GroupIdentifier.group_pk == GroupModel.id,
                    GroupIdentifier.value == identifier,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        type: str | GroupType | None = None,
        actual: bool | None = None,
        active: bool | None = None,
        name: str | None = None,
        code: str | None = None,
        managing_entity: str | None = None,
        member: str | None = None,
        characteristic: str | None = None,
        characteristic_value: str | None = None,
        exclude: bool | None = None,
        identifier: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[GroupModel], int]:
        async with self.session_factory() as session:
            filter_kwargs = dict(
                org_id=org_id,
                type=type,
                actual=actual,
                active=active,
                name=name,
                code=code,
                managing_entity=managing_entity,
                member=member,
                characteristic=characteristic,
                characteristic_value=characteristic_value,
                exclude=exclude,
                identifier=identifier,
            )
            base = self._apply_list_filters(select(GroupModel), **filter_kwargs)
            base = _with_relationships(base)
            count_stmt = self._apply_list_filters(
                select(func.count()).select_from(GroupModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                GroupModel.group_id,
            )

            rows, total = await self._execute_paginated(
                session,
                base,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total

    async def delete(self, group_id: int, org_id: str | None = None) -> bool:
        async with self.session_factory() as session:
            stmt = select(GroupModel).where(GroupModel.group_id == group_id)
            if org_id:
                stmt = stmt.where(GroupModel.tenant_id == org_id)
            group = (await session.execute(stmt)).scalars().first()
            if not group:
                return False
            await session.delete(group)
            await session.commit()
            return True

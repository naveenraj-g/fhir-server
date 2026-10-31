from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.group import (
    GroupCharacteristic,
    GroupCharacteristicCodeCoding,
    GroupCharacteristicValueCoding,
    GroupCodeCoding,
    GroupIdentifier,
    GroupIdentifierTypeCoding,
    GroupMember,
    GroupModel,
)
from app.schemas.group import GroupCreateSchema, GroupPatchSchema

from ._shared import (
    _parse_assigner_ref,
    _parse_generic_ref,
    _parse_managing_entity_ref,
    _parse_member_entity_ref,
    _validate_ref,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifiers(
    session, group_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = GroupIdentifier(
            group_pk=group_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    GroupIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_code_codings(
    session, group_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            GroupCodeCoding(
                group_pk=group_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_characteristics(
    session, group_pk: int, org_id: str, characteristics, created_by: str
) -> None:
    for char in characteristics or []:
        val_ref_type, val_ref_id = (
            _parse_generic_ref(char.value_reference)
            if char.value_reference
            else (None, None)
        )
        if val_ref_type and val_ref_id:
            await _validate_ref(
                session, org_id, val_ref_type, val_ref_id, "characteristic.value_reference"
            )

        row = GroupCharacteristic(
            group_pk=group_pk,
            tenant_id=org_id,
            code_text=char.code.text if char.code else None,
            exclude=char.exclude,
            period_start=char.period_start,
            period_end=char.period_end,
            value_boolean=char.value_boolean,
            value_codeable_concept_text=(
                char.value_codeable_concept.text
                if char.value_codeable_concept
                else None
            ),
            value_quantity=char.value_quantity,
            value_range=char.value_range,
            value_reference_reference=char.value_reference,
            value_reference_type=val_ref_type,
            value_reference_id=val_ref_id,
            value_reference_display=char.value_reference_display,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()

        if char.code and char.code.coding:
            for c in char.code.coding:
                session.add(
                    GroupCharacteristicCodeCoding(
                        characteristic_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if char.value_codeable_concept and char.value_codeable_concept.coding:
            for c in char.value_codeable_concept.coding:
                session.add(
                    GroupCharacteristicValueCoding(
                        characteristic_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_members(
    session, group_pk: int, org_id: str, members, created_by: str
) -> None:
    for m in members or []:
        m_type, m_id = _parse_member_entity_ref(m.entity)
        if m_type and m_id:
            await _validate_ref(session, org_id, m_type, m_id, "member.entity")

        session.add(
            GroupMember(
                group_pk=group_pk,
                tenant_id=org_id,
                entity_reference=m.entity,
                entity_type=m_type,
                entity_id=m_id,
                entity_display=m.entity_display,
                period_start=m.period_start,
                period_end=m.period_end,
                inactive=m.inactive,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Full atomic CRUD operations for Group."""

    async def create_full(
        self,
        payload: GroupCreateSchema,
        org_id: str,
        created_by: str,
    ) -> GroupModel:
        async with self.session_factory() as session:
            me_type, me_id = (
                _parse_managing_entity_ref(payload.managing_entity)
                if payload.managing_entity
                else (None, None)
            )
            if me_type and me_id:
                await _validate_ref(session, org_id, me_type, me_id, "managing_entity")

            group = GroupModel(
                active=payload.active,
                type=payload.type,
                actual=payload.actual,
                code_text=payload.code.text if payload.code else None,
                name=payload.name,
                quantity=payload.quantity,
                managing_entity_reference=payload.managing_entity,
                managing_entity_type=me_type,
                managing_entity_id=me_id,
                managing_entity_display=payload.managing_entity_display,
                extension=payload.extension or [],
                tenant_id=org_id,
                created_by=created_by,
            )
            session.add(group)
            await session.flush()

            await _add_identifiers(session, group.id, org_id, payload.identifier, created_by)

            if payload.code and payload.code.coding:
                await _add_code_codings(session, group.id, org_id, payload.code.coding, created_by)

            await _add_characteristics(session, group.id, org_id, payload.characteristic, created_by)
            await _add_members(session, group.id, org_id, payload.member, created_by)

            await session.commit()

        return await self.get_by_group_id_in_org(group.group_id, org_id)

    async def patch_full(
        self,
        group_id: int,
        payload: GroupPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> GroupModel | None:
        async with self.session_factory() as session:
            stmt = select(GroupModel).where(
                GroupModel.group_id == group_id,
                GroupModel.tenant_id == org_id,
            )
            group = (await session.execute(stmt)).scalars().first()
            if not group:
                return None

            fields_set = payload.model_fields_set

            if "active" in fields_set:
                group.active = payload.active
            if "type" in fields_set:
                group.type = payload.type
            if "actual" in fields_set:
                group.actual = payload.actual
            if "name" in fields_set:
                group.name = payload.name
            if "quantity" in fields_set:
                group.quantity = payload.quantity
            if "extension" in fields_set:
                group.extension = payload.extension or []

            if "managing_entity" in fields_set or "managing_entity_display" in fields_set:
                if payload.managing_entity:
                    me_type, me_id = _parse_managing_entity_ref(payload.managing_entity)
                    await _validate_ref(session, org_id, me_type, me_id, "managing_entity")
                    group.managing_entity_reference = payload.managing_entity
                    group.managing_entity_type = me_type
                    group.managing_entity_id = me_id
                elif "managing_entity" in fields_set and payload.managing_entity is None:
                    group.managing_entity_reference = None
                    group.managing_entity_type = None
                    group.managing_entity_id = None
                if "managing_entity_display" in fields_set:
                    group.managing_entity_display = payload.managing_entity_display

            if "code" in fields_set:
                await session.execute(
                    delete(GroupCodeCoding).where(GroupCodeCoding.group_pk == group.id)
                )
                group.code_text = payload.code.text if payload.code else None
                if payload.code and payload.code.coding:
                    await _add_code_codings(
                        session, group.id, org_id, payload.code.coding, updated_by
                    )

            if "identifier" in fields_set:
                await session.execute(
                    delete(GroupIdentifier).where(GroupIdentifier.group_pk == group.id)
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, group.id, org_id, payload.identifier, updated_by
                    )

            if "characteristic" in fields_set:
                await session.execute(
                    delete(GroupCharacteristic).where(
                        GroupCharacteristic.group_pk == group.id
                    )
                )
                if payload.characteristic:
                    await _add_characteristics(
                        session, group.id, org_id, payload.characteristic, updated_by
                    )

            if "member" in fields_set:
                await session.execute(
                    delete(GroupMember).where(GroupMember.group_pk == group.id)
                )
                if payload.member:
                    await _add_members(
                        session, group.id, org_id, payload.member, updated_by
                    )

            group.updated_by = updated_by
            await session.commit()

        return await self.get_by_group_id_in_org(group_id, org_id)

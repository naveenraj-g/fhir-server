from sqlalchemy import select

from app.models.practitioner import PractitionerIdentifier, PractitionerModel
from app.schemas.practitioner import PractitionerIdentifierCreate, PractitionerIdentifierPatch

from ._shared import _delete_child, _fetch_child, _org_ref_kwargs, _parse_org_ref, _reference_kwargs, _validate_reference


class _IdentifierMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.identifier rows."""

    async def add_identifier(
        self, practitioner_id: int, payload: PractitionerIdentifierCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            a_type, a_id = (
                _parse_org_ref(payload.assigner) if payload.assigner else (None, None)
            )
            await _validate_reference(session, practitioner.org_id, a_type, a_id, "identifier.assigner")
            row = PractitionerIdentifier(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                type_system=payload.type_system,
                type_version=payload.type_version,
                type_code=payload.type_code,
                type_display=payload.type_display,
                type_text=payload.type_text,
                type_user_selected=payload.type_user_selected,
                system=payload.system,
                value=payload.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                **_org_ref_kwargs("assigner", payload.assigner, payload.assigner_display),
                **_reference_kwargs("assigner", payload),
                created_by=created_by,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_identifiers(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerIdentifier).where(PractitionerIdentifier.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_identifier(self, practitioner_id: int, identifier_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerIdentifier, identifier_id, practitioner.id)

    async def patch_identifier(
        self, practitioner_id: int, identifier_id: int, payload: PractitionerIdentifierPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerIdentifier, identifier_id, practitioner.id)
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            if "assigner" in data:
                ref = data.pop("assigner")
                if ref:
                    a_type, a_id = _parse_org_ref(ref)
                    await _validate_reference(
                        session, practitioner.org_id, a_type, a_id, "identifier.assigner"
                    )
                    row.assigner_type = a_type
                    row.assigner_id = a_id
                else:
                    row.assigner_type = None
                    row.assigner_id = None
            for field, value in data.items():
                setattr(row, field, value)
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

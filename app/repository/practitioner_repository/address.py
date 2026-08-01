from sqlalchemy import select

from app.models.practitioner import PractitionerAddress, PractitionerModel
from app.schemas.practitioner import PractitionerAddressCreate, PractitionerAddressPatch

from ._shared import _delete_child, _fetch_child


class _AddressMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.address rows."""

    async def add_address(
        self, practitioner_id: int, payload: PractitionerAddressCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerAddress(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                type=payload.type,
                text=payload.text,
                line=",".join(payload.line) if payload.line else None,
                city=payload.city,
                district=payload.district,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_addresses(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerAddress).where(PractitionerAddress.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_address(self, practitioner_id: int, address_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerAddress, address_id, practitioner.id)

    async def patch_address(
        self, practitioner_id: int, address_id: int, payload: PractitionerAddressPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerAddress, address_id, practitioner.id)
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            if "line" in data:
                data["line"] = ",".join(data["line"]) if data["line"] else None
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

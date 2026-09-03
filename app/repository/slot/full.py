from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.slot import (
    SlotIdentifier,
    SlotModel,
    SlotServiceCategory,
    SlotServiceType,
    SlotSpecialty,
)
from app.schemas.slot import SlotCreateSchema, SlotPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _parse_schedule_ref,
    _reference_kwargs,
    _schedule_ref_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 4 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: SlotCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> SlotModel:
        """Create a Slot plus any combination of its sub-resource lists,
        atomically in one DB transaction. `schedule` is required (1..1) and
        is ALWAYS validated for existence — unlike an optional reference,
        there is no None-skip path."""
        async with self.session_factory() as session:
            sched_type, sched_id = _parse_schedule_ref(payload.schedule)
            await _validate_reference(session, org_id, sched_type, sched_id, "schedule")

            slot = SlotModel(
                org_id=org_id,
                created_by=created_by,
                **_schedule_ref_kwargs(
                    "schedule", payload.schedule, payload.schedule_display
                ),
                **_reference_kwargs("schedule", payload),
                status=payload.status,
                start=payload.start,
                end=payload.end,
                overbooked=payload.overbooked,
                comment=payload.comment,
                appointment_type_system=payload.appointment_type_system,
                appointment_type_version=payload.appointment_type_version,
                appointment_type_code=payload.appointment_type_code,
                appointment_type_display=payload.appointment_type_display,
                appointment_type_text=payload.appointment_type_text,
                appointment_type_user_selected=payload.appointment_type_user_selected,
            )
            session.add(slot)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        SlotIdentifier(
                            slot_id=slot.id,
                            org_id=org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=created_by,
                        )
                    )

            if payload.service_category:
                for sc in payload.service_category:
                    session.add(
                        SlotServiceCategory(
                            slot_id=slot.id,
                            org_id=org_id,
                            coding_system=sc.coding_system,
                            coding_version=sc.coding_version,
                            coding_code=sc.coding_code,
                            coding_display=sc.coding_display,
                            text=sc.text,
                            coding_user_selected=sc.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.service_type:
                for st in payload.service_type:
                    session.add(
                        SlotServiceType(
                            slot_id=slot.id,
                            org_id=org_id,
                            coding_system=st.coding_system,
                            coding_version=st.coding_version,
                            coding_code=st.coding_code,
                            coding_display=st.coding_display,
                            text=st.text,
                            coding_user_selected=st.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.specialty:
                for sp in payload.specialty:
                    session.add(
                        SlotSpecialty(
                            slot_id=slot.id,
                            org_id=org_id,
                            coding_system=sp.coding_system,
                            coding_version=sp.coding_version,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                            coding_user_selected=sp.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
                await session.refresh(slot)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_slot_id(slot.slot_id)

    async def patch_full(
        self,
        slot_id: int,
        payload: SlotPatchSchema,
        updated_by: str | None = None,
    ) -> SlotModel | None:
        """Patches core scalar fields and, for each sub-resource list that is
        supplied — even `[]` — atomically deletes all existing rows and
        inserts the new ones. Lists omitted from the payload are left
        untouched. The `schedule` reference is immutable via PATCH — it isn't
        a field on SlotPatchSchema at all."""
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(SlotModel.slot_id == slot_id)
            slot = (await session.execute(stmt)).scalars().first()
            if not slot:
                return None

            _SUB = {"identifier", "service_category", "service_type", "specialty"}
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                setattr(slot, field, value)
            if updated_by is not None:
                slot.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(SlotIdentifier).where(SlotIdentifier.slot_id == slot.id)
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, slot.org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        SlotIdentifier(
                            slot_id=slot.id,
                            org_id=slot.org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=updated_by,
                        )
                    )

            if payload.service_category is not None:
                await session.execute(
                    delete(SlotServiceCategory).where(
                        SlotServiceCategory.slot_id == slot.id
                    )
                )
                for sc in payload.service_category:
                    session.add(
                        SlotServiceCategory(
                            slot_id=slot.id,
                            org_id=slot.org_id,
                            coding_system=sc.coding_system,
                            coding_version=sc.coding_version,
                            coding_code=sc.coding_code,
                            coding_display=sc.coding_display,
                            text=sc.text,
                            coding_user_selected=sc.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.service_type is not None:
                await session.execute(
                    delete(SlotServiceType).where(SlotServiceType.slot_id == slot.id)
                )
                for st in payload.service_type:
                    session.add(
                        SlotServiceType(
                            slot_id=slot.id,
                            org_id=slot.org_id,
                            coding_system=st.coding_system,
                            coding_version=st.coding_version,
                            coding_code=st.coding_code,
                            coding_display=st.coding_display,
                            text=st.text,
                            coding_user_selected=st.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.specialty is not None:
                await session.execute(
                    delete(SlotSpecialty).where(SlotSpecialty.slot_id == slot.id)
                )
                for sp in payload.specialty:
                    session.add(
                        SlotSpecialty(
                            slot_id=slot.id,
                            org_id=slot.org_id,
                            coding_system=sp.coding_system,
                            coding_version=sp.coding_version,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                            coding_user_selected=sp.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Slot sub-resource lists replaced",
                    extra={
                        "event": "slot.sublists_replaced",
                        "slot_id": slot_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_slot_id(slot_id)

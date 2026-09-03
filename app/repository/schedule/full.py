from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceType,
    ScheduleSpecialty,
)
from app.schemas.schedule import ScheduleCreateSchema, SchedulePatchSchema

from ._shared import (
    _actor_ref_kwargs,
    _org_ref_kwargs,
    _parse_actor_ref,
    _parse_org_ref,
    _reference_kwargs,
    _validate_actor_reference,
    _validate_reference,
)

logger = get_logger(__name__)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 5 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: ScheduleCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> ScheduleModel:
        """Create a Schedule plus any combination of its sub-resource lists,
        atomically in one DB transaction. `actor` is required (1..*); every
        other list is optional and only inserted if supplied."""
        async with self.session_factory() as session:
            sched = ScheduleModel(
                org_id=org_id,
                created_by=created_by,
                active=payload.active,
                planning_horizon_start=payload.planning_horizon_start,
                planning_horizon_end=payload.planning_horizon_end,
                comment=payload.comment,
            )
            session.add(sched)
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
                        ScheduleIdentifier(
                            schedule_id=sched.id,
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
                        ScheduleServiceCategory(
                            schedule_id=sched.id,
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
                        ScheduleServiceType(
                            schedule_id=sched.id,
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
                        ScheduleSpecialty(
                            schedule_id=sched.id,
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

            for a in payload.actor:
                a_type, a_id = (
                    _parse_actor_ref(a.reference) if a.reference else (None, None)
                )
                await _validate_actor_reference(session, org_id, a_type, a_id, "actor")
                session.add(
                    ScheduleActor(
                        schedule_id=sched.id,
                        org_id=org_id,
                        **_actor_ref_kwargs(
                            "reference", a.reference, a.reference_display
                        ),
                        **_reference_kwargs("reference", a),
                        created_by=created_by,
                    )
                )

            try:
                await session.commit()
                await session.refresh(sched)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_schedule_id(sched.schedule_id)

    async def patch_full(
        self,
        schedule_id: int,
        payload: SchedulePatchSchema,
        updated_by: str | None = None,
    ) -> ScheduleModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` for the 0..*
        lists — atomically deletes all existing rows and inserts the new
        ones. Lists omitted from the payload are left untouched. `actor`
        cannot be supplied as an empty list — see SchedulePatchSchema's
        validator."""
        async with self.session_factory() as session:
            stmt = select(ScheduleModel).where(
                ScheduleModel.schedule_id == schedule_id
            )
            sched = (await session.execute(stmt)).scalars().first()
            if not sched:
                return None

            _SUB = {
                "identifier",
                "service_category",
                "service_type",
                "specialty",
                "actor",
            }
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                setattr(sched, field, value)
            if updated_by is not None:
                sched.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(ScheduleIdentifier).where(
                        ScheduleIdentifier.schedule_id == sched.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, sched.org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        ScheduleIdentifier(
                            schedule_id=sched.id,
                            org_id=sched.org_id,
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
                    delete(ScheduleServiceCategory).where(
                        ScheduleServiceCategory.schedule_id == sched.id
                    )
                )
                for sc in payload.service_category:
                    session.add(
                        ScheduleServiceCategory(
                            schedule_id=sched.id,
                            org_id=sched.org_id,
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
                    delete(ScheduleServiceType).where(
                        ScheduleServiceType.schedule_id == sched.id
                    )
                )
                for st in payload.service_type:
                    session.add(
                        ScheduleServiceType(
                            schedule_id=sched.id,
                            org_id=sched.org_id,
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
                    delete(ScheduleSpecialty).where(
                        ScheduleSpecialty.schedule_id == sched.id
                    )
                )
                for sp in payload.specialty:
                    session.add(
                        ScheduleSpecialty(
                            schedule_id=sched.id,
                            org_id=sched.org_id,
                            coding_system=sp.coding_system,
                            coding_version=sp.coding_version,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                            coding_user_selected=sp.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.actor is not None:
                await session.execute(
                    delete(ScheduleActor).where(ScheduleActor.schedule_id == sched.id)
                )
                for a in payload.actor:
                    a_type, a_id = (
                        _parse_actor_ref(a.reference) if a.reference else (None, None)
                    )
                    await _validate_actor_reference(
                        session, sched.org_id, a_type, a_id, "actor"
                    )
                    session.add(
                        ScheduleActor(
                            schedule_id=sched.id,
                            org_id=sched.org_id,
                            **_actor_ref_kwargs(
                                "reference", a.reference, a.reference_display
                            ),
                            **_reference_kwargs("reference", a),
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
                    "Schedule sub-resource lists replaced",
                    extra={
                        "event": "schedule.sublists_replaced",
                        "schedule_id": schedule_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_schedule_id(schedule_id)

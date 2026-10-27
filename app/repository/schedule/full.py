from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleIdentifierTypeCoding,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceCategoryCoding,
    ScheduleServiceType,
    ScheduleServiceTypeCoding,
    ScheduleSpecialty,
    ScheduleSpecialtyCoding,
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

# Sub-resource list fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is untouched.
_SUB = {"identifier", "service_category", "service_type", "specialty", "actor"}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput entry,
    targeting any of the three dedicated coding[] child tables — all share
    the same shape via FhirCodingMixin. Mirrors
    app.repository.practitioner_role.full._coding_kwargs."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


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
        """Create a Schedule plus any combination of its 5 sub-resource
        lists, atomically in one DB transaction. Every list on the payload
        is optional; only the ones supplied get inserted."""
        async with self.session_factory() as session:
            sch = ScheduleModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                active=payload.active,
                planning_horizon_start=payload.planning_horizon_start,
                planning_horizon_end=payload.planning_horizon_end,
                comment=payload.comment,
            )
            session.add(sch)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = ScheduleIdentifier(
                        schedule_pk=sch.id,
                        tenant_id=org_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=created_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                ScheduleIdentifierTypeCoding(
                                    schedule_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.service_category:
                for sc in payload.service_category:
                    service_category = ScheduleServiceCategory(
                        schedule_pk=sch.id,
                        tenant_id=org_id,
                        text=sc.text,
                        created_by=created_by,
                    )
                    session.add(service_category)
                    if sc.coding:
                        await session.flush()
                        for coding in sc.coding:
                            session.add(
                                ScheduleServiceCategoryCoding(
                                    schedule_service_category_id=service_category.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.service_type:
                for st in payload.service_type:
                    service_type = ScheduleServiceType(
                        schedule_pk=sch.id,
                        tenant_id=org_id,
                        text=st.text,
                        created_by=created_by,
                    )
                    session.add(service_type)
                    if st.coding:
                        await session.flush()
                        for coding in st.coding:
                            session.add(
                                ScheduleServiceTypeCoding(
                                    schedule_service_type_id=service_type.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.specialty:
                for sp in payload.specialty:
                    specialty = ScheduleSpecialty(
                        schedule_pk=sch.id,
                        tenant_id=org_id,
                        text=sp.text,
                        created_by=created_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                ScheduleSpecialtyCoding(
                                    schedule_specialty_id=specialty.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.actor:
                for a in payload.actor:
                    a_type, a_id = (
                        _parse_actor_ref(a.reference) if a.reference else (None, None)
                    )
                    await _validate_actor_reference(session, org_id, a_type, a_id)
                    session.add(
                        ScheduleActor(
                            schedule_pk=sch.id,
                            tenant_id=org_id,
                            reference_reference=a.reference,
                            **_actor_ref_kwargs(
                                "reference", a.reference, a.reference_display
                            ),
                            **_reference_kwargs("reference", a),
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
                await session.refresh(sch)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_schedule_id(sch.schedule_id)

    async def patch_full(
        self,
        schedule_id: int,
        payload: SchedulePatchSchema,
        updated_by: str | None = None,
    ) -> ScheduleModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(ScheduleModel).where(
                ScheduleModel.schedule_id == schedule_id
            )
            sch = (await session.execute(stmt)).scalars().first()
            if not sch:
                return None

            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                setattr(sch, field, value)
            if updated_by is not None:
                sch.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(ScheduleIdentifier).where(
                        ScheduleIdentifier.schedule_pk == sch.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, sch.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = ScheduleIdentifier(
                        schedule_pk=sch.id,
                        tenant_id=sch.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=updated_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                ScheduleIdentifierTypeCoding(
                                    schedule_identifier_id=identifier.id,
                                    tenant_id=sch.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_category is not None:
                await session.execute(
                    delete(ScheduleServiceCategory).where(
                        ScheduleServiceCategory.schedule_pk == sch.id
                    )
                )
                for sc in payload.service_category:
                    service_category = ScheduleServiceCategory(
                        schedule_pk=sch.id,
                        tenant_id=sch.tenant_id,
                        text=sc.text,
                        created_by=updated_by,
                    )
                    session.add(service_category)
                    if sc.coding:
                        await session.flush()
                        for coding in sc.coding:
                            session.add(
                                ScheduleServiceCategoryCoding(
                                    schedule_service_category_id=service_category.id,
                                    tenant_id=sch.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_type is not None:
                await session.execute(
                    delete(ScheduleServiceType).where(
                        ScheduleServiceType.schedule_pk == sch.id
                    )
                )
                for st in payload.service_type:
                    service_type = ScheduleServiceType(
                        schedule_pk=sch.id,
                        tenant_id=sch.tenant_id,
                        text=st.text,
                        created_by=updated_by,
                    )
                    session.add(service_type)
                    if st.coding:
                        await session.flush()
                        for coding in st.coding:
                            session.add(
                                ScheduleServiceTypeCoding(
                                    schedule_service_type_id=service_type.id,
                                    tenant_id=sch.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.specialty is not None:
                await session.execute(
                    delete(ScheduleSpecialty).where(
                        ScheduleSpecialty.schedule_pk == sch.id
                    )
                )
                for sp in payload.specialty:
                    specialty = ScheduleSpecialty(
                        schedule_pk=sch.id,
                        tenant_id=sch.tenant_id,
                        text=sp.text,
                        created_by=updated_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                ScheduleSpecialtyCoding(
                                    schedule_specialty_id=specialty.id,
                                    tenant_id=sch.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.actor is not None:
                await session.execute(
                    delete(ScheduleActor).where(ScheduleActor.schedule_pk == sch.id)
                )
                for a in payload.actor:
                    a_type, a_id = (
                        _parse_actor_ref(a.reference) if a.reference else (None, None)
                    )
                    await _validate_actor_reference(
                        session, sch.tenant_id, a_type, a_id
                    )
                    session.add(
                        ScheduleActor(
                            schedule_pk=sch.id,
                            tenant_id=sch.tenant_id,
                            reference_reference=a.reference,
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

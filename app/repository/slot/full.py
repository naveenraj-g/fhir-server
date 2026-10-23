from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.slot import (
    SlotAppointmentTypeCoding,
    SlotIdentifier,
    SlotIdentifierTypeCoding,
    SlotModel,
    SlotServiceCategory,
    SlotServiceCategoryCoding,
    SlotServiceType,
    SlotServiceTypeCoding,
    SlotSpecialty,
    SlotSpecialtyCoding,
    SlotStatus as SlotStatusModel,
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

# Sub-resource list fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is untouched.
_SUB = {"identifier", "service_category", "service_type", "specialty"}

# Handled by hand in create_full/patch_full rather than the generic setattr
# loop in patch_full, since they need conversion/promotion, not a plain
# column assignment.
_SPECIAL = {
    "schedule", "schedule_display",
    "schedule_identifier_use", "schedule_identifier_type_system",
    "schedule_identifier_type_version", "schedule_identifier_type_code",
    "schedule_identifier_type_display", "schedule_identifier_type_text",
    "schedule_identifier_type_user_selected", "schedule_identifier_system",
    "schedule_identifier_value", "schedule_identifier_period_start",
    "schedule_identifier_period_end",
    "status", "appointment_type_coding", "appointment_type_text",
}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput entry,
    targeting any of the four dedicated coding[] child tables — all share
    the same shape via FhirCodingMixin. Mirrors
    app.repository.schedule.full._coding_kwargs."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _model_status(status) -> SlotStatusModel:
    """Convert the Pydantic input schema's app.schemas.enums.SlotStatus
    (hyphenated .value, e.g. "busy-unavailable") to the model-layer
    app.models.slot.enums.SlotStatus (underscore-only .value) by member
    NAME, which is identical between the two enums — never by value. See
    app.models.slot.enums.SlotStatus's docstring."""
    return SlotStatusModel[status.name]


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 4 sub-resource types (plus core scalar fields,
    including the required schedule reference/status/start/end) in one
    transaction."""

    async def create_full(
        self,
        payload: SlotCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> SlotModel:
        """Create a Slot plus any combination of its 4 sub-resource lists,
        atomically in one DB transaction. `schedule`/`status`/`start`/`end`
        are required; every sub-resource list is optional."""
        s_type, s_id = _parse_schedule_ref(payload.schedule)
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, s_type, s_id, "schedule")
            slot = SlotModel(
                tenant_id=org_id,
                created_by=created_by,
                **_schedule_ref_kwargs(
                    "schedule", payload.schedule, payload.schedule_display
                ),
                **_reference_kwargs("schedule", payload),
                status=_model_status(payload.status),
                start=payload.start,
                end=payload.end,
                appointment_type_text=payload.appointment_type_text,
                overbooked=payload.overbooked,
                comment=payload.comment,
            )
            session.add(slot)
            await session.flush()

            if payload.appointment_type_coding:
                for coding in payload.appointment_type_coding:
                    session.add(
                        SlotAppointmentTypeCoding(
                            slot_pk=slot.id,
                            tenant_id=org_id,
                            **_coding_kwargs(coding, created_by),
                        )
                    )

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = SlotIdentifier(
                        slot_pk=slot.id,
                        tenant_id=org_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=created_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                SlotIdentifierTypeCoding(
                                    slot_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.service_category:
                for sc in payload.service_category:
                    service_category = SlotServiceCategory(
                        slot_pk=slot.id,
                        tenant_id=org_id,
                        text=sc.text,
                        created_by=created_by,
                    )
                    session.add(service_category)
                    if sc.coding:
                        await session.flush()
                        for coding in sc.coding:
                            session.add(
                                SlotServiceCategoryCoding(
                                    slot_service_category_id=service_category.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.service_type:
                for st in payload.service_type:
                    service_type = SlotServiceType(
                        slot_pk=slot.id,
                        tenant_id=org_id,
                        text=st.text,
                        created_by=created_by,
                    )
                    session.add(service_type)
                    if st.coding:
                        await session.flush()
                        for coding in st.coding:
                            session.add(
                                SlotServiceTypeCoding(
                                    slot_service_type_id=service_type.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.specialty:
                for sp in payload.specialty:
                    specialty = SlotSpecialty(
                        slot_pk=slot.id,
                        tenant_id=org_id,
                        text=sp.text,
                        created_by=created_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                SlotSpecialtyCoding(
                                    slot_specialty_id=specialty.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
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
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(SlotModel).where(SlotModel.slot_id == slot_id)
            slot = (await session.execute(stmt)).scalars().first()
            if not slot:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(slot, field, value)

            if "schedule" in provided or "schedule_display" in provided:
                if payload.schedule is not None:
                    s_type, s_id = _parse_schedule_ref(payload.schedule)
                    await _validate_reference(
                        session, slot.tenant_id, s_type, s_id, "schedule"
                    )
                    slot.schedule_type = s_type
                    slot.schedule_id = s_id
                if "schedule_display" in provided:
                    slot.schedule_display = payload.schedule_display
            for suffix in (
                "use", "type_system", "type_version", "type_code", "type_display",
                "type_text", "type_user_selected", "system", "value",
                "period_start", "period_end",
            ):
                field = f"schedule_identifier_{suffix}"
                if field in provided:
                    setattr(slot, field, getattr(payload, field))

            if "status" in provided and payload.status is not None:
                slot.status = _model_status(payload.status)
            if "appointment_type_text" in provided:
                slot.appointment_type_text = payload.appointment_type_text

            if updated_by is not None:
                slot.updated_by = updated_by

            if "appointment_type_coding" in provided:
                await session.execute(
                    delete(SlotAppointmentTypeCoding).where(
                        SlotAppointmentTypeCoding.slot_pk == slot.id
                    )
                )
                for coding in payload.appointment_type_coding or []:
                    session.add(
                        SlotAppointmentTypeCoding(
                            slot_pk=slot.id,
                            tenant_id=slot.tenant_id,
                            **_coding_kwargs(coding, updated_by),
                        )
                    )

            if payload.identifier is not None:
                await session.execute(
                    delete(SlotIdentifier).where(SlotIdentifier.slot_pk == slot.id)
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, slot.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = SlotIdentifier(
                        slot_pk=slot.id,
                        tenant_id=slot.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=updated_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                SlotIdentifierTypeCoding(
                                    slot_identifier_id=identifier.id,
                                    tenant_id=slot.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_category is not None:
                await session.execute(
                    delete(SlotServiceCategory).where(
                        SlotServiceCategory.slot_pk == slot.id
                    )
                )
                for sc in payload.service_category:
                    service_category = SlotServiceCategory(
                        slot_pk=slot.id,
                        tenant_id=slot.tenant_id,
                        text=sc.text,
                        created_by=updated_by,
                    )
                    session.add(service_category)
                    if sc.coding:
                        await session.flush()
                        for coding in sc.coding:
                            session.add(
                                SlotServiceCategoryCoding(
                                    slot_service_category_id=service_category.id,
                                    tenant_id=slot.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_type is not None:
                await session.execute(
                    delete(SlotServiceType).where(SlotServiceType.slot_pk == slot.id)
                )
                for st in payload.service_type:
                    service_type = SlotServiceType(
                        slot_pk=slot.id,
                        tenant_id=slot.tenant_id,
                        text=st.text,
                        created_by=updated_by,
                    )
                    session.add(service_type)
                    if st.coding:
                        await session.flush()
                        for coding in st.coding:
                            session.add(
                                SlotServiceTypeCoding(
                                    slot_service_type_id=service_type.id,
                                    tenant_id=slot.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.specialty is not None:
                await session.execute(
                    delete(SlotSpecialty).where(SlotSpecialty.slot_pk == slot.id)
                )
                for sp in payload.specialty:
                    specialty = SlotSpecialty(
                        slot_pk=slot.id,
                        tenant_id=slot.tenant_id,
                        text=sp.text,
                        created_by=updated_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                SlotSpecialtyCoding(
                                    slot_specialty_id=specialty.id,
                                    tenant_id=slot.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
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

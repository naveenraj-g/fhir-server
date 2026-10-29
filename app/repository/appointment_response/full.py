from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.appointment_response import (
    AppointmentResponseIdentifier,
    AppointmentResponseIdentifierTypeCoding,
    AppointmentResponseModel,
    AppointmentResponseParticipantStatus as AppointmentResponseParticipantStatusModel,
    AppointmentResponseParticipantType,
    AppointmentResponseParticipantTypeCoding,
)
from app.schemas.appointment_response import (
    AppointmentResponseCreateSchema,
    AppointmentResponsePatchSchema,
)

from ._shared import (
    _actor_ref_kwargs,
    _appointment_ref_kwargs,
    _org_ref_kwargs,
    _parse_actor_ref,
    _parse_appointment_ref,
    _parse_org_ref,
    _reference_kwargs,
    _validate_actor_reference,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource list fields on the create/patch payloads. A supplied list
# (even `[]`) replaces the corresponding rows wholesale; an omitted one is
# untouched.
_SUB = {"identifier", "participant_type"}

# Handled by hand in create_full/patch_full rather than the generic setattr
# loop in patch_full, since they need conversion/promotion, not a plain
# column assignment.
_SPECIAL = {
    "appointment", "appointment_display",
    "appointment_identifier_use", "appointment_identifier_type_system",
    "appointment_identifier_type_version", "appointment_identifier_type_code",
    "appointment_identifier_type_display", "appointment_identifier_type_text",
    "appointment_identifier_type_user_selected", "appointment_identifier_system",
    "appointment_identifier_value", "appointment_identifier_period_start",
    "appointment_identifier_period_end",
    "actor", "actor_display",
    "actor_identifier_use", "actor_identifier_type_system",
    "actor_identifier_type_version", "actor_identifier_type_code",
    "actor_identifier_type_display", "actor_identifier_type_text",
    "actor_identifier_type_user_selected", "actor_identifier_system",
    "actor_identifier_value", "actor_identifier_period_start",
    "actor_identifier_period_end",
    "participant_status",
}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput
    entry, targeting any of the dedicated coding[] child tables — all
    share the same shape via FhirCodingMixin. Mirrors
    app.repository.appointment.full._coding_kwargs."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _model_participant_status(status) -> AppointmentResponseParticipantStatusModel:
    """Convert the Pydantic input schema's
    app.schemas.enums.AppointmentResponseParticipantStatus (hyphenated
    .value) to the model-layer app.models.appointment_response.enums.
    AppointmentResponseParticipantStatus (underscore-only .value) by
    member NAME, which is identical between the two enums — never by
    value. See app.models.slot.enums.SlotStatus's docstring for the full
    reasoning."""
    return AppointmentResponseParticipantStatusModel[status.name]


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch both sub-resource types (plus core scalar fields, including
    the required appointment reference/participantStatus) in one
    transaction."""

    async def create_full(
        self,
        payload: AppointmentResponseCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> AppointmentResponseModel:
        """Create an AppointmentResponse plus any combination of its 2
        sub-resource lists, atomically in one DB transaction.
        `appointment`/`participant_status` are required; every sub-resource
        list is optional."""
        a_type, a_id = _parse_appointment_ref(payload.appointment)
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, a_type, a_id, "appointment")

            act_type, act_id = (
                _parse_actor_ref(payload.actor) if payload.actor else (None, None)
            )
            await _validate_actor_reference(session, org_id, act_type, act_id)

            appointment_response = AppointmentResponseModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                appointment_reference=payload.appointment,
                **_appointment_ref_kwargs(
                    "appointment", payload.appointment, payload.appointment_display
                ),
                **_reference_kwargs("appointment", payload),
                start=payload.start,
                end=payload.end,
                actor_reference=payload.actor,
                **_actor_ref_kwargs("actor", payload.actor, payload.actor_display),
                **_reference_kwargs("actor", payload),
                participant_status=_model_participant_status(payload.participant_status),
                comment=payload.comment,
            )
            session.add(appointment_response)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    asn_type, asn_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, asn_type, asn_id, "identifier.assigner"
                    )
                    identifier = AppointmentResponseIdentifier(
                        appointment_response_pk=appointment_response.id,
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
                                AppointmentResponseIdentifierTypeCoding(
                                    appointment_response_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            for pt in payload.participant_type or []:
                participant_type = AppointmentResponseParticipantType(
                    appointment_response_pk=appointment_response.id,
                    tenant_id=org_id,
                    text=pt.text,
                    created_by=created_by,
                )
                session.add(participant_type)
                if pt.coding:
                    await session.flush()
                    for coding in pt.coding:
                        session.add(
                            AppointmentResponseParticipantTypeCoding(
                                appointment_response_participant_type_id=participant_type.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            try:
                await session.commit()
                await session.refresh(appointment_response)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_response_id(
            appointment_response.appointment_response_id
        )

    async def patch_full(
        self,
        appointment_response_id: int,
        payload: AppointmentResponsePatchSchema,
        updated_by: str | None = None,
    ) -> AppointmentResponseModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(AppointmentResponseModel).where(
                AppointmentResponseModel.appointment_response_id
                == appointment_response_id
            )
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(row, field, value)

            if "appointment" in provided or "appointment_display" in provided:
                if payload.appointment is not None:
                    a_type, a_id = _parse_appointment_ref(payload.appointment)
                    await _validate_reference(
                        session, row.tenant_id, a_type, a_id, "appointment"
                    )
                    row.appointment_type = a_type
                    row.appointment_id = a_id
                if "appointment_display" in provided:
                    row.appointment_display = payload.appointment_display
            for suffix in (
                "use", "type_system", "type_version", "type_code", "type_display",
                "type_text", "type_user_selected", "system", "value",
                "period_start", "period_end",
            ):
                field = f"appointment_identifier_{suffix}"
                if field in provided:
                    setattr(row, field, getattr(payload, field))

            if "actor" in provided or "actor_display" in provided:
                if payload.actor is not None:
                    act_type, act_id = _parse_actor_ref(payload.actor)
                    await _validate_actor_reference(session, row.tenant_id, act_type, act_id)
                    row.actor_type = act_type
                    row.actor_id = act_id
                else:
                    row.actor_type = None
                    row.actor_id = None
                if "actor_display" in provided:
                    row.actor_display = payload.actor_display
            for suffix in (
                "use", "type_system", "type_version", "type_code", "type_display",
                "type_text", "type_user_selected", "system", "value",
                "period_start", "period_end",
            ):
                field = f"actor_identifier_{suffix}"
                if field in provided:
                    setattr(row, field, getattr(payload, field))

            if "participant_status" in provided and payload.participant_status is not None:
                row.participant_status = _model_participant_status(payload.participant_status)

            if updated_by is not None:
                row.updated_by = updated_by

            if payload.identifier is not None:
                # Grandchildren first — there's no DB-level ON DELETE CASCADE
                # on this FK (deliberately, see every other child/grandchild
                # table in this codebase), so a bulk Core delete() of the
                # parent rows alone would violate the FK whenever any of
                # them still has type_codings.
                await session.execute(
                    delete(AppointmentResponseIdentifierTypeCoding).where(
                        AppointmentResponseIdentifierTypeCoding.appointment_response_identifier_id.in_(
                            select(AppointmentResponseIdentifier.id).where(
                                AppointmentResponseIdentifier.appointment_response_pk
                                == row.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(AppointmentResponseIdentifier).where(
                        AppointmentResponseIdentifier.appointment_response_pk == row.id
                    )
                )
                for i in payload.identifier:
                    asn_type, asn_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, row.tenant_id, asn_type, asn_id, "identifier.assigner"
                    )
                    identifier = AppointmentResponseIdentifier(
                        appointment_response_pk=row.id,
                        tenant_id=row.tenant_id,
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
                                AppointmentResponseIdentifierTypeCoding(
                                    appointment_response_identifier_id=identifier.id,
                                    tenant_id=row.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.participant_type is not None:
                # Grandchildren first — see the identifier block above for
                # why.
                await session.execute(
                    delete(AppointmentResponseParticipantTypeCoding).where(
                        AppointmentResponseParticipantTypeCoding.appointment_response_participant_type_id.in_(
                            select(AppointmentResponseParticipantType.id).where(
                                AppointmentResponseParticipantType.appointment_response_pk
                                == row.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(AppointmentResponseParticipantType).where(
                        AppointmentResponseParticipantType.appointment_response_pk == row.id
                    )
                )
                for pt in payload.participant_type:
                    participant_type = AppointmentResponseParticipantType(
                        appointment_response_pk=row.id,
                        tenant_id=row.tenant_id,
                        text=pt.text,
                        created_by=updated_by,
                    )
                    session.add(participant_type)
                    if pt.coding:
                        await session.flush()
                        for coding in pt.coding:
                            session.add(
                                AppointmentResponseParticipantTypeCoding(
                                    appointment_response_participant_type_id=participant_type.id,
                                    tenant_id=row.tenant_id,
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
                    "AppointmentResponse sub-resource lists replaced",
                    extra={
                        "event": "appointment_response.sublists_replaced",
                        "appointment_response_id": appointment_response_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_appointment_response_id(appointment_response_id)

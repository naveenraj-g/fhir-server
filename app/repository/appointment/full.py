from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.appointment import (
    AppointmentAppointmentTypeCoding,
    AppointmentBasedOn,
    AppointmentCancelationReasonCoding,
    AppointmentIdentifier,
    AppointmentIdentifierTypeCoding,
    AppointmentModel,
    AppointmentParticipant,
    AppointmentParticipantType,
    AppointmentParticipantTypeCoding,
    AppointmentReasonCode,
    AppointmentReasonCodeCoding,
    AppointmentReasonReference,
    AppointmentRequestedPeriod,
    AppointmentServiceCategory,
    AppointmentServiceCategoryCoding,
    AppointmentServiceType,
    AppointmentServiceTypeCoding,
    AppointmentSlot,
    AppointmentSpecialty,
    AppointmentSpecialtyCoding,
    AppointmentSupportingInformation,
)
from app.models.appointment.enums import (
    AppointmentParticipantRequired as AppointmentParticipantRequiredModel,
    AppointmentParticipationStatus as AppointmentParticipationStatusModel,
    AppointmentStatus as AppointmentStatusModel,
)
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema

from ._shared import (
    _actor_ref_kwargs,
    _any_ref_kwargs,
    _based_on_ref_kwargs,
    _org_ref_kwargs,
    _parse_actor_ref,
    _parse_org_ref,
    _parse_slot_ref,
    _reason_reference_ref_kwargs,
    _reference_kwargs,
    _slot_ref_kwargs,
    _validate_actor_reference,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource list fields on the create/patch payloads. A supplied list
# (even `[]`) replaces the corresponding rows wholesale; an omitted one is
# untouched.
_SUB = {
    "identifier", "service_category", "service_type", "specialty",
    "reason_code", "reason_reference", "supporting_information", "slot",
    "based_on", "requested_period", "participant",
}

# Handled by hand in create_full/patch_full rather than the generic setattr
# loop in patch_full, since they need conversion/promotion, not a plain
# column assignment.
_SPECIAL = {
    "status", "cancelation_reason_coding", "cancelation_reason_text",
    "appointment_type_coding", "appointment_type_text",
}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput
    entry, targeting any of the dedicated coding[] child tables — all share
    the same shape via FhirCodingMixin. Mirrors
    app.repository.slot.full._coding_kwargs."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _model_status(status) -> AppointmentStatusModel:
    """Convert the Pydantic input schema's app.schemas.enums.AppointmentStatus
    (hyphenated .value) to the model-layer
    app.models.appointment.enums.AppointmentStatus (underscore-only .value)
    by member NAME, which is identical between the two enums — never by
    value. See app.models.slot.enums.SlotStatus's docstring for the full
    reasoning."""
    return AppointmentStatusModel[status.name]


def _model_required(required) -> AppointmentParticipantRequiredModel | None:
    return AppointmentParticipantRequiredModel[required.name] if required else None


def _model_participation_status(status) -> AppointmentParticipationStatusModel:
    return AppointmentParticipationStatusModel[status.name]


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch every sub-resource type (plus core scalar fields, including
    the required status and 1..*-per-spec participant list) in one
    transaction."""

    async def create_full(
        self,
        payload: AppointmentCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> AppointmentModel:
        """Create an Appointment plus any combination of its sub-resource
        lists, atomically in one DB transaction. `status` is required;
        every sub-resource list is optional (though `participant` is 1..*
        per spec — enforced by the FHIR validator, not here)."""
        async with self.session_factory() as session:
            appointment = AppointmentModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                status=_model_status(payload.status),
                cancelation_reason_text=payload.cancelation_reason_text,
                appointment_type_text=payload.appointment_type_text,
                priority=payload.priority,
                description=payload.description,
                start=payload.start,
                end=payload.end,
                minutes_duration=payload.minutes_duration,
                created=payload.created,
                comment=payload.comment,
                patient_instruction=payload.patient_instruction,
            )
            session.add(appointment)
            await session.flush()

            if payload.cancelation_reason_coding:
                for coding in payload.cancelation_reason_coding:
                    session.add(
                        AppointmentCancelationReasonCoding(
                            appointment_pk=appointment.id,
                            tenant_id=org_id,
                            **_coding_kwargs(coding, created_by),
                        )
                    )

            if payload.appointment_type_coding:
                for coding in payload.appointment_type_coding:
                    session.add(
                        AppointmentAppointmentTypeCoding(
                            appointment_pk=appointment.id,
                            tenant_id=org_id,
                            **_coding_kwargs(coding, created_by),
                        )
                    )

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
                    identifier = AppointmentIdentifier(
                        appointment_pk=appointment.id,
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
                                AppointmentIdentifierTypeCoding(
                                    appointment_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            for sc in payload.service_category or []:
                service_category = AppointmentServiceCategory(
                    appointment_pk=appointment.id, tenant_id=org_id, text=sc.text, created_by=created_by
                )
                session.add(service_category)
                if sc.coding:
                    await session.flush()
                    for coding in sc.coding:
                        session.add(
                            AppointmentServiceCategoryCoding(
                                appointment_service_category_id=service_category.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for st in payload.service_type or []:
                service_type = AppointmentServiceType(
                    appointment_pk=appointment.id, tenant_id=org_id, text=st.text, created_by=created_by
                )
                session.add(service_type)
                if st.coding:
                    await session.flush()
                    for coding in st.coding:
                        session.add(
                            AppointmentServiceTypeCoding(
                                appointment_service_type_id=service_type.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for sp in payload.specialty or []:
                specialty = AppointmentSpecialty(
                    appointment_pk=appointment.id, tenant_id=org_id, text=sp.text, created_by=created_by
                )
                session.add(specialty)
                if sp.coding:
                    await session.flush()
                    for coding in sp.coding:
                        session.add(
                            AppointmentSpecialtyCoding(
                                appointment_specialty_id=specialty.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for rc in payload.reason_code or []:
                reason_code = AppointmentReasonCode(
                    appointment_pk=appointment.id, tenant_id=org_id, text=rc.text, created_by=created_by
                )
                session.add(reason_code)
                if rc.coding:
                    await session.flush()
                    for coding in rc.coding:
                        session.add(
                            AppointmentReasonCodeCoding(
                                appointment_reason_code_id=reason_code.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for rr in payload.reason_reference or []:
                session.add(
                    AppointmentReasonReference(
                        appointment_pk=appointment.id,
                        tenant_id=org_id,
                        reference_reference=rr.reference,
                        **_reason_reference_ref_kwargs(
                            "reference", rr.reference, rr.reference_display
                        ),
                        **_reference_kwargs("reference", rr),
                        created_by=created_by,
                    )
                )

            for si in payload.supporting_information or []:
                session.add(
                    AppointmentSupportingInformation(
                        appointment_pk=appointment.id,
                        tenant_id=org_id,
                        reference_reference=si.reference,
                        **_any_ref_kwargs("reference", si.reference, si.reference_display),
                        **_reference_kwargs("reference", si),
                        created_by=created_by,
                    )
                )

            for s in payload.slot or []:
                s_type, s_id = _parse_slot_ref(s.reference) if s.reference else (None, None)
                await _validate_reference(session, org_id, s_type, s_id, "slot")
                session.add(
                    AppointmentSlot(
                        appointment_pk=appointment.id,
                        tenant_id=org_id,
                        reference_reference=s.reference,
                        **_slot_ref_kwargs("reference", s.reference, s.reference_display),
                        **_reference_kwargs("reference", s),
                        created_by=created_by,
                    )
                )

            for bo in payload.based_on or []:
                session.add(
                    AppointmentBasedOn(
                        appointment_pk=appointment.id,
                        tenant_id=org_id,
                        reference_reference=bo.reference,
                        **_based_on_ref_kwargs("reference", bo.reference, bo.reference_display),
                        **_reference_kwargs("reference", bo),
                        created_by=created_by,
                    )
                )

            for rp in payload.requested_period or []:
                session.add(
                    AppointmentRequestedPeriod(
                        appointment_pk=appointment.id,
                        tenant_id=org_id,
                        start=rp.start,
                        end=rp.end,
                        created_by=created_by,
                    )
                )

            for p in payload.participant or []:
                a_type, a_id = _parse_actor_ref(p.actor) if p.actor else (None, None)
                await _validate_actor_reference(session, org_id, a_type, a_id)
                participant = AppointmentParticipant(
                    appointment_pk=appointment.id,
                    tenant_id=org_id,
                    actor_reference=p.actor,
                    **_actor_ref_kwargs("actor", p.actor, p.actor_display),
                    **_reference_kwargs("actor", p),
                    required=_model_required(p.required),
                    status=_model_participation_status(p.status),
                    period_start=p.period_start,
                    period_end=p.period_end,
                    created_by=created_by,
                )
                session.add(participant)
                if p.type:
                    await session.flush()
                    for t in p.type:
                        participant_type = AppointmentParticipantType(
                            appointment_participant_id=participant.id,
                            tenant_id=org_id,
                            text=t.text,
                            created_by=created_by,
                        )
                        session.add(participant_type)
                        if t.coding:
                            await session.flush()
                            for coding in t.coding:
                                session.add(
                                    AppointmentParticipantTypeCoding(
                                        appointment_participant_type_id=participant_type.id,
                                        tenant_id=org_id,
                                        **_coding_kwargs(coding, created_by),
                                    )
                                )

            try:
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_id(appointment.appointment_id)

    async def patch_full(
        self,
        appointment_id: int,
        payload: AppointmentPatchSchema,
        updated_by: str | None = None,
    ) -> AppointmentModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(
                AppointmentModel.appointment_id == appointment_id
            )
            appointment = (await session.execute(stmt)).scalars().first()
            if not appointment:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(appointment, field, value)

            if "status" in provided and payload.status is not None:
                appointment.status = _model_status(payload.status)
            if "cancelation_reason_text" in provided:
                appointment.cancelation_reason_text = payload.cancelation_reason_text
            if "appointment_type_text" in provided:
                appointment.appointment_type_text = payload.appointment_type_text

            if updated_by is not None:
                appointment.updated_by = updated_by

            if "cancelation_reason_coding" in provided:
                await session.execute(
                    delete(AppointmentCancelationReasonCoding).where(
                        AppointmentCancelationReasonCoding.appointment_pk == appointment.id
                    )
                )
                for coding in payload.cancelation_reason_coding or []:
                    session.add(
                        AppointmentCancelationReasonCoding(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            **_coding_kwargs(coding, updated_by),
                        )
                    )

            if "appointment_type_coding" in provided:
                await session.execute(
                    delete(AppointmentAppointmentTypeCoding).where(
                        AppointmentAppointmentTypeCoding.appointment_pk == appointment.id
                    )
                )
                for coding in payload.appointment_type_coding or []:
                    session.add(
                        AppointmentAppointmentTypeCoding(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            **_coding_kwargs(coding, updated_by),
                        )
                    )

            if payload.identifier is not None:
                await session.execute(
                    delete(AppointmentIdentifier).where(
                        AppointmentIdentifier.appointment_pk == appointment.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    await _validate_reference(
                        session, appointment.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = AppointmentIdentifier(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
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
                                AppointmentIdentifierTypeCoding(
                                    appointment_identifier_id=identifier.id,
                                    tenant_id=appointment.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_category is not None:
                await session.execute(
                    delete(AppointmentServiceCategory).where(
                        AppointmentServiceCategory.appointment_pk == appointment.id
                    )
                )
                for sc in payload.service_category:
                    service_category = AppointmentServiceCategory(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
                        text=sc.text,
                        created_by=updated_by,
                    )
                    session.add(service_category)
                    if sc.coding:
                        await session.flush()
                        for coding in sc.coding:
                            session.add(
                                AppointmentServiceCategoryCoding(
                                    appointment_service_category_id=service_category.id,
                                    tenant_id=appointment.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.service_type is not None:
                await session.execute(
                    delete(AppointmentServiceType).where(
                        AppointmentServiceType.appointment_pk == appointment.id
                    )
                )
                for st in payload.service_type:
                    service_type = AppointmentServiceType(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
                        text=st.text,
                        created_by=updated_by,
                    )
                    session.add(service_type)
                    if st.coding:
                        await session.flush()
                        for coding in st.coding:
                            session.add(
                                AppointmentServiceTypeCoding(
                                    appointment_service_type_id=service_type.id,
                                    tenant_id=appointment.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.specialty is not None:
                await session.execute(
                    delete(AppointmentSpecialty).where(
                        AppointmentSpecialty.appointment_pk == appointment.id
                    )
                )
                for sp in payload.specialty:
                    specialty = AppointmentSpecialty(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
                        text=sp.text,
                        created_by=updated_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                AppointmentSpecialtyCoding(
                                    appointment_specialty_id=specialty.id,
                                    tenant_id=appointment.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.reason_code is not None:
                await session.execute(
                    delete(AppointmentReasonCode).where(
                        AppointmentReasonCode.appointment_pk == appointment.id
                    )
                )
                for rc in payload.reason_code:
                    reason_code = AppointmentReasonCode(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
                        text=rc.text,
                        created_by=updated_by,
                    )
                    session.add(reason_code)
                    if rc.coding:
                        await session.flush()
                        for coding in rc.coding:
                            session.add(
                                AppointmentReasonCodeCoding(
                                    appointment_reason_code_id=reason_code.id,
                                    tenant_id=appointment.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.reason_reference is not None:
                await session.execute(
                    delete(AppointmentReasonReference).where(
                        AppointmentReasonReference.appointment_pk == appointment.id
                    )
                )
                for rr in payload.reason_reference:
                    session.add(
                        AppointmentReasonReference(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            reference_reference=rr.reference,
                            **_reason_reference_ref_kwargs(
                                "reference", rr.reference, rr.reference_display
                            ),
                            **_reference_kwargs("reference", rr),
                            created_by=updated_by,
                        )
                    )

            if payload.supporting_information is not None:
                await session.execute(
                    delete(AppointmentSupportingInformation).where(
                        AppointmentSupportingInformation.appointment_pk == appointment.id
                    )
                )
                for si in payload.supporting_information:
                    session.add(
                        AppointmentSupportingInformation(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            reference_reference=si.reference,
                            **_any_ref_kwargs("reference", si.reference, si.reference_display),
                            **_reference_kwargs("reference", si),
                            created_by=updated_by,
                        )
                    )

            if payload.slot is not None:
                await session.execute(
                    delete(AppointmentSlot).where(AppointmentSlot.appointment_pk == appointment.id)
                )
                for s in payload.slot:
                    s_type, s_id = _parse_slot_ref(s.reference) if s.reference else (None, None)
                    await _validate_reference(session, appointment.tenant_id, s_type, s_id, "slot")
                    session.add(
                        AppointmentSlot(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            reference_reference=s.reference,
                            **_slot_ref_kwargs("reference", s.reference, s.reference_display),
                            **_reference_kwargs("reference", s),
                            created_by=updated_by,
                        )
                    )

            if payload.based_on is not None:
                await session.execute(
                    delete(AppointmentBasedOn).where(
                        AppointmentBasedOn.appointment_pk == appointment.id
                    )
                )
                for bo in payload.based_on:
                    session.add(
                        AppointmentBasedOn(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            reference_reference=bo.reference,
                            **_based_on_ref_kwargs(
                                "reference", bo.reference, bo.reference_display
                            ),
                            **_reference_kwargs("reference", bo),
                            created_by=updated_by,
                        )
                    )

            if payload.requested_period is not None:
                await session.execute(
                    delete(AppointmentRequestedPeriod).where(
                        AppointmentRequestedPeriod.appointment_pk == appointment.id
                    )
                )
                for rp in payload.requested_period:
                    session.add(
                        AppointmentRequestedPeriod(
                            appointment_pk=appointment.id,
                            tenant_id=appointment.tenant_id,
                            start=rp.start,
                            end=rp.end,
                            created_by=updated_by,
                        )
                    )

            if payload.participant is not None:
                await session.execute(
                    delete(AppointmentParticipant).where(
                        AppointmentParticipant.appointment_pk == appointment.id
                    )
                )
                for p in payload.participant:
                    a_type, a_id = _parse_actor_ref(p.actor) if p.actor else (None, None)
                    await _validate_actor_reference(session, appointment.tenant_id, a_type, a_id)
                    participant = AppointmentParticipant(
                        appointment_pk=appointment.id,
                        tenant_id=appointment.tenant_id,
                        actor_reference=p.actor,
                        **_actor_ref_kwargs("actor", p.actor, p.actor_display),
                        **_reference_kwargs("actor", p),
                        required=_model_required(p.required),
                        status=_model_participation_status(p.status),
                        period_start=p.period_start,
                        period_end=p.period_end,
                        created_by=updated_by,
                    )
                    session.add(participant)
                    if p.type:
                        await session.flush()
                        for t in p.type:
                            participant_type = AppointmentParticipantType(
                                appointment_participant_id=participant.id,
                                tenant_id=appointment.tenant_id,
                                text=t.text,
                                created_by=updated_by,
                            )
                            session.add(participant_type)
                            if t.coding:
                                await session.flush()
                                for coding in t.coding:
                                    session.add(
                                        AppointmentParticipantTypeCoding(
                                            appointment_participant_type_id=participant_type.id,
                                            tenant_id=appointment.tenant_id,
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
                    "Appointment sub-resource lists replaced",
                    extra={
                        "event": "appointment.sublists_replaced",
                        "appointment_id": appointment_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_appointment_id(appointment_id)

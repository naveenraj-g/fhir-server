from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.appointment.appointment import (
    AppointmentModel,
    AppointmentIdentifier,
    AppointmentServiceCategory,
    AppointmentServiceType,
    AppointmentSpecialty,
    AppointmentReasonCode,
    AppointmentReasonReference,
    AppointmentSupportingInformation,
    AppointmentSlot,
    AppointmentBasedOn,
    AppointmentParticipant,
    AppointmentParticipantType,
    AppointmentRequestedPeriod,
    AppointmentRecurrenceTemplate,
)
from app.models.appointment.enums import (
    AppointmentParticipantActorType,
    AppointmentReasonReferenceType,
    AppointmentBasedOnReferenceType,
    AppointmentSlotReferenceType,
)
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema
from app.core.references import parse_reference


def _with_relationships(stmt):
    return stmt.options(
        selectinload(AppointmentModel.identifiers),
        selectinload(AppointmentModel.service_categories),
        selectinload(AppointmentModel.service_types),
        selectinload(AppointmentModel.specialties),
        selectinload(AppointmentModel.reason_codes),
        selectinload(AppointmentModel.reason_references),
        selectinload(AppointmentModel.supporting_informations),
        selectinload(AppointmentModel.slots),
        selectinload(AppointmentModel.based_ons),
        selectinload(AppointmentModel.participants).selectinload(AppointmentParticipant.types),
        selectinload(AppointmentModel.requested_periods),
        selectinload(AppointmentModel.recurrence_template),
    )


def _parse_open_ref(ref: str) -> Tuple[str, int]:
    """Parse 'ResourceType/id' into (type_str, id_int) without enum validation."""
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        return parts[0], int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )


def _cast_ref_type(value: str, enum_cls, field: str):
    """Cast a parsed reference type string to the required enum, raising 422 for unknown values."""
    try:
        return enum_cls(value)
    except ValueError:
        allowed = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference type '{value}' for {field}. Allowed: {allowed}.",
        )


class AppointmentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_appointment_id(self, appointment_id: int) -> Optional[AppointmentModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(
        self, stmt, user_id, org_id, status, patient_id, start_from, start_to,
        practitioner_id=None,
    ):
        if user_id:
            stmt = stmt.where(AppointmentModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(AppointmentModel.org_id == org_id)
        if status:
            stmt = stmt.where(AppointmentModel.status == status)
        if patient_id is not None:
            sub = (
                select(AppointmentParticipant.id)
                .where(
                    AppointmentParticipant.appointment_id == AppointmentModel.id,
                    AppointmentParticipant.reference_type == AppointmentParticipantActorType.Patient,
                    AppointmentParticipant.reference_id == patient_id,
                )
                .correlate(AppointmentModel)
            )
            stmt = stmt.where(sub.exists())
        if practitioner_id is not None:
            sub = (
                select(AppointmentParticipant.id)
                .where(
                    AppointmentParticipant.appointment_id == AppointmentModel.id,
                    AppointmentParticipant.reference_type == AppointmentParticipantActorType.Practitioner,
                    AppointmentParticipant.reference_id == practitioner_id,
                )
                .correlate(AppointmentModel)
            )
            stmt = stmt.where(sub.exists())
        if start_from is not None:
            stmt = stmt.where(AppointmentModel.start >= start_from)
        if start_to is not None:
            stmt = stmt.where(AppointmentModel.start <= start_to)
        return stmt

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        practitioner_id: Optional[int] = None,
        start_from: Optional[datetime] = None,
        start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AppointmentModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(AppointmentModel)),
                user_id, org_id, status, patient_id, start_from, start_to,
                practitioner_id=practitioner_id,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(AppointmentModel),
                user_id, org_id, status, patient_id, start_from, start_to,
                practitioner_id=practitioner_id,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(AppointmentModel.start.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        practitioner_id: Optional[int] = None,
        start_from: Optional[datetime] = None,
        start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AppointmentModel], int]:
        return await self.list(
            user_id=user_id, org_id=org_id, status=status, patient_id=patient_id,
            practitioner_id=practitioner_id,
            start_from=start_from, start_to=start_to,
            limit=limit, offset=offset,
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: AppointmentCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> AppointmentModel:
        async with self.session_factory() as session:
            appointment = AppointmentModel(
                user_id=user_id,
                org_id=org_id,
                created_by=created_by,
                status=payload.status,
                cancelation_reason_system=payload.cancelation_reason_system,
                cancelation_reason_code=payload.cancelation_reason_code,
                cancelation_reason_display=payload.cancelation_reason_display,
                cancelation_reason_text=payload.cancelation_reason_text,
                appointment_type_system=payload.appointment_type_system,
                appointment_type_code=payload.appointment_type_code,
                appointment_type_display=payload.appointment_type_display,
                appointment_type_text=payload.appointment_type_text,
                priority=payload.priority,
                start=payload.start,
                end=payload.end,
                minutes_duration=payload.minutes_duration,
                created=payload.created,
                description=payload.description,
                comment=payload.comment,
                patient_instruction=payload.patient_instruction,
            )

            # identifier
            if payload.identifier:
                for i in payload.identifier:
                    appointment.identifiers.append(AppointmentIdentifier(
                        org_id=org_id,
                        use=i.use,
                        type_system=i.type_system,
                        type_code=i.type_code,
                        type_display=i.type_display,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner=i.assigner,
                    ))

            # serviceCategory
            if payload.service_category:
                for sc in payload.service_category:
                    appointment.service_categories.append(AppointmentServiceCategory(
                        org_id=org_id,
                        coding_system=sc.coding_system,
                        coding_code=sc.coding_code,
                        coding_display=sc.coding_display,
                        text=sc.text,
                    ))

            # serviceType (plain CodeableConcept)
            if payload.service_type:
                for st in payload.service_type:
                    appointment.service_types.append(AppointmentServiceType(
                        org_id=org_id,
                        coding_system=st.coding_system,
                        coding_code=st.coding_code,
                        coding_display=st.coding_display,
                        text=st.text,
                    ))

            # specialty
            if payload.specialty:
                for sp in payload.specialty:
                    appointment.specialties.append(AppointmentSpecialty(
                        org_id=org_id,
                        coding_system=sp.coding_system,
                        coding_code=sp.coding_code,
                        coding_display=sp.coding_display,
                        text=sp.text,
                    ))

            # reasonCode
            if payload.reason_code:
                for rc in payload.reason_code:
                    appointment.reason_codes.append(AppointmentReasonCode(
                        org_id=org_id,
                        coding_system=rc.coding_system,
                        coding_code=rc.coding_code,
                        coding_display=rc.coding_display,
                        text=rc.text,
                    ))

            # reasonReference
            if payload.reason_reference:
                for rr in payload.reason_reference:
                    rr_ref_str, rr_ref_id = _parse_open_ref(rr.reference)
                    rr_ref_type_enum = _cast_ref_type(
                        rr_ref_str, AppointmentReasonReferenceType, "reasonReference.reference"
                    )
                    appointment.reason_references.append(AppointmentReasonReference(
                        org_id=org_id,
                        reference_type=rr_ref_type_enum,
                        reference_id=rr_ref_id,
                        reference_display=rr.reference_display,
                    ))

            # supportingInformation
            if payload.supporting_information:
                for si in payload.supporting_information:
                    ref_type, ref_id = _parse_open_ref(si.reference)
                    appointment.supporting_informations.append(AppointmentSupportingInformation(
                        org_id=org_id,
                        reference_type=ref_type,
                        reference_id=ref_id,
                        reference_display=si.reference_display,
                    ))

            # slot
            if payload.slot:
                for s in payload.slot:
                    slot_ref_str, slot_ref_id = _parse_open_ref(s.reference)
                    slot_ref_type_enum = _cast_ref_type(
                        slot_ref_str, AppointmentSlotReferenceType, "slot.reference"
                    )
                    appointment.slots.append(AppointmentSlot(
                        org_id=org_id,
                        reference_type=slot_ref_type_enum,
                        reference_id=slot_ref_id,
                        reference_display=s.reference_display,
                    ))

            # basedOn (R4: Reference(ServiceRequest) only)
            if payload.based_on:
                for b in payload.based_on:
                    based_on_ref_str, based_on_ref_id = _parse_open_ref(b.reference)
                    based_on_ref_type_enum = _cast_ref_type(
                        based_on_ref_str, AppointmentBasedOnReferenceType, "basedOn.reference"
                    )
                    appointment.based_ons.append(AppointmentBasedOn(
                        org_id=org_id,
                        reference_type=based_on_ref_type_enum,
                        reference_id=based_on_ref_id,
                        reference_display=b.reference_display,
                    ))

            # participants (R4: actor allowed types narrowed, required is a code)
            for p in payload.participant:
                ref_type, ref_id = (
                    parse_reference(p.reference, AppointmentParticipantActorType)
                    if p.reference else (None, None)
                )
                participant = AppointmentParticipant(
                    org_id=org_id,
                    reference_type=ref_type,
                    reference_id=ref_id,
                    reference_display=p.reference_display,
                    required=p.required,
                    status=p.status.value if p.status else "needs-action",
                    period_start=p.period_start,
                    period_end=p.period_end,
                )
                if p.types:
                    for t in p.types:
                        participant.types.append(AppointmentParticipantType(
                            org_id=org_id,
                            coding_system=t.coding_system,
                            coding_code=t.coding_code,
                            coding_display=t.coding_display,
                            text=t.text,
                        ))
                appointment.participants.append(participant)

            # requestedPeriod
            if payload.requested_period:
                for rp in payload.requested_period:
                    appointment.requested_periods.append(AppointmentRequestedPeriod(
                        org_id=org_id,
                        period_start=rp.period_start,
                        period_end=rp.period_end,
                    ))

            # recurrenceTemplate (operational, not FHIR core — see model docstring)
            if payload.recurrence_template:
                rt = payload.recurrence_template
                appointment.recurrence_template = AppointmentRecurrenceTemplate(
                    recurrence_type_code=rt.recurrence_type_code,
                    recurrence_type_display=rt.recurrence_type_display,
                    recurrence_type_system=rt.recurrence_type_system,
                    timezone_code=rt.timezone_code,
                    timezone_display=rt.timezone_display,
                    last_occurrence_date=rt.last_occurrence_date,
                    occurrence_count=rt.occurrence_count,
                    occurrence_dates=",".join(str(d) for d in rt.occurrence_dates) if rt.occurrence_dates else None,
                    excluding_dates=",".join(str(d) for d in rt.excluding_dates) if rt.excluding_dates else None,
                    excluding_recurrence_ids=",".join(str(i) for i in rt.excluding_recurrence_ids) if rt.excluding_recurrence_ids else None,
                    weekly_monday=rt.weekly_template.monday if rt.weekly_template else None,
                    weekly_tuesday=rt.weekly_template.tuesday if rt.weekly_template else None,
                    weekly_wednesday=rt.weekly_template.wednesday if rt.weekly_template else None,
                    weekly_thursday=rt.weekly_template.thursday if rt.weekly_template else None,
                    weekly_friday=rt.weekly_template.friday if rt.weekly_template else None,
                    weekly_saturday=rt.weekly_template.saturday if rt.weekly_template else None,
                    weekly_sunday=rt.weekly_template.sunday if rt.weekly_template else None,
                    weekly_week_interval=rt.weekly_template.week_interval if rt.weekly_template else None,
                    monthly_day_of_month=rt.monthly_template.day_of_month if rt.monthly_template else None,
                    monthly_nth_week_code=rt.monthly_template.nth_week_code if rt.monthly_template else None,
                    monthly_nth_week_display=rt.monthly_template.nth_week_display if rt.monthly_template else None,
                    monthly_day_of_week_code=rt.monthly_template.day_of_week_code if rt.monthly_template else None,
                    monthly_day_of_week_display=rt.monthly_template.day_of_week_display if rt.monthly_template else None,
                    monthly_month_interval=rt.monthly_template.month_interval if rt.monthly_template else None,
                    yearly_year_interval=rt.yearly_template.year_interval if rt.yearly_template else None,
                )

            try:
                session.add(appointment)
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_id(appointment.appointment_id)

    async def patch(
        self,
        appointment_id: int,
        payload: AppointmentPatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[AppointmentModel]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
            )
            appointment = result.scalars().first()
            if not appointment:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(appointment, field, value)
            if updated_by is not None:
                appointment.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_id(appointment_id)

    async def delete(self, appointment_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(AppointmentModel).where(AppointmentModel.appointment_id == appointment_id)
            )
            appointment = result.scalars().first()
            if not appointment:
                return False

            try:
                await session.delete(appointment)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

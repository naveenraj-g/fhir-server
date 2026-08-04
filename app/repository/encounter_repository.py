from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.orm import selectinload

from app.models.encounter.encounter import (
    EncounterModel,
    EncounterIdentifier,
    EncounterStatusHistory,
    EncounterClassHistory,
    EncounterType,
    EncounterEpisodeOfCare,
    EncounterBasedOn,
    EncounterParticipant,
    EncounterParticipantType,
    EncounterAppointmentRef,
    EncounterReasonCode,
    EncounterReasonReference,
    EncounterDiagnosis,
    EncounterAccount,
    EncounterDietPreference,
    EncounterSpecialArrangement,
    EncounterSpecialCourtesy,
    EncounterLocation,
)
from app.models.encounter.enums import (
    EncounterBasedOnReferenceType,
    EncounterDiagnosisConditionType,
    EncounterParticipantReferenceType,
    EncounterReasonReferenceType,
    EncounterEpisodeOfCareReferenceType,
    EncounterAppointmentReferenceType,
    EncounterAccountReferenceType,
    EncounterLocationReferenceType,
)
from app.models.enums import SubjectReferenceType, OrganizationReferenceType
from app.models.organization import OrganizationModel
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema


def _with_relationships(stmt):
    """Attach eager-load options for all R4 encounter sub-resources."""
    return stmt.options(
        selectinload(EncounterModel.identifiers),
        selectinload(EncounterModel.status_history),
        selectinload(EncounterModel.class_history),
        selectinload(EncounterModel.types),
        selectinload(EncounterModel.episode_of_cares),
        selectinload(EncounterModel.based_ons),
        selectinload(EncounterModel.participants).selectinload(EncounterParticipant.types),
        selectinload(EncounterModel.appointment_refs),
        selectinload(EncounterModel.reason_codes),
        selectinload(EncounterModel.reason_references),
        selectinload(EncounterModel.diagnoses),
        selectinload(EncounterModel.accounts),
        selectinload(EncounterModel.diet_preferences),
        selectinload(EncounterModel.special_arrangements),
        selectinload(EncounterModel.special_courtesies),
        selectinload(EncounterModel.locations),
        selectinload(EncounterModel.service_provider),
        selectinload(EncounterModel.part_of),
    )


def _parse_ref(ref_str: Optional[str]) -> tuple:
    """Split 'ResourceType/123' → ('ResourceType', 123). Returns (None, None) on failure."""
    if not ref_str:
        return None, None
    parts = ref_str.split("/")
    if len(parts) != 2 or not parts[1].isdigit():
        return None, None
    return parts[0], int(parts[1])


def _parse_open_ref(ref: str) -> tuple:
    """Parse 'ResourceType/id' for open (any type) references."""
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        return parts[0], int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )


def _cast_ref_type(type_str: Optional[str], enum_cls, field: str):
    """Cast a string resource type to an enum; raises HTTP 422 if not valid."""
    if not type_str:
        return None
    try:
        return enum_cls(type_str)
    except ValueError:
        allowed = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference type '{type_str}' for {field}. Allowed: {allowed}",
        )


def _parse_subject(subject_str: Optional[str]):
    type_str, ref_id = _parse_ref(subject_str)
    if not type_str:
        return None, None
    try:
        return SubjectReferenceType(type_str), ref_id
    except ValueError:
        return None, None


async def _resolve_org_pk(
    session: AsyncSession, ref: Optional[str], field: str
) -> Tuple[Optional[OrganizationReferenceType], Optional[int]]:
    """Resolve 'Organization/<public_id>' to the internal organization.id PK."""
    if not ref:
        return None, None
    type_str, org_public_id = _parse_open_ref(ref)
    if type_str != "Organization":
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference type '{type_str}' for {field}. Allowed: ['Organization'].",
        )
    result = await session.execute(
        select(OrganizationModel.id).where(OrganizationModel.organization_id == org_public_id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(status_code=422, detail=f"Organization/{org_public_id} not found.")
    return OrganizationReferenceType.Organization, pk


async def _resolve_part_of_pk(session: AsyncSession, ref: Optional[str]) -> Optional[int]:
    """Resolve 'Encounter/<public_id>' to the internal encounter.id PK (self-reference)."""
    if not ref:
        return None
    type_str, encounter_public_id = _parse_open_ref(ref)
    if type_str != "Encounter":
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference type '{type_str}' for partOf. Allowed: ['Encounter'].",
        )
    result = await session.execute(
        select(EncounterModel.id).where(EncounterModel.encounter_id == encounter_public_id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(status_code=422, detail=f"Encounter/{encounter_public_id} not found.")
    return pk


class EncounterRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_encounter_id(self, encounter_id: int) -> Optional[EncounterModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(
        self, stmt, user_id, org_id, status, patient_id,
        period_start_from, period_start_to,
        appointment_id=None,
    ):
        if user_id:
            stmt = stmt.where(EncounterModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(EncounterModel.org_id == org_id)
        if status:
            stmt = stmt.where(EncounterModel.status == status)
        if patient_id is not None:
            stmt = stmt.where(
                EncounterModel.subject_type == SubjectReferenceType.Patient,
                EncounterModel.subject_id == patient_id,
            )
        if appointment_id is not None:
            sub = (
                select(EncounterAppointmentRef.id)
                .where(
                    EncounterAppointmentRef.encounter_id == EncounterModel.id,
                    EncounterAppointmentRef.reference_type == EncounterAppointmentReferenceType.Appointment,
                    EncounterAppointmentRef.reference_id == appointment_id,
                )
                .correlate(EncounterModel)
            )
            stmt = stmt.where(sub.exists())
        if period_start_from is not None:
            stmt = stmt.where(EncounterModel.period_start >= period_start_from)
        if period_start_to is not None:
            stmt = stmt.where(EncounterModel.period_start <= period_start_to)
        return stmt

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        period_start_from: Optional[datetime] = None,
        period_start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EncounterModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(EncounterModel)),
                user_id, org_id, status, patient_id,
                period_start_from, period_start_to,
                appointment_id=appointment_id,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(EncounterModel),
                user_id, org_id, status, patient_id,
                period_start_from, period_start_to,
                appointment_id=appointment_id,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(EncounterModel.period_start.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        period_start_from: Optional[datetime] = None,
        period_start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EncounterModel], int]:
        return await self.list(
            user_id=user_id, org_id=org_id, status=status, patient_id=patient_id,
            appointment_id=appointment_id,
            period_start_from=period_start_from, period_start_to=period_start_to,
            limit=limit, offset=offset,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: EncounterCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        subject_display: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> EncounterModel:
        subject_type, subject_id = _parse_subject(payload.subject)

        async with self.session_factory() as session:
            service_provider_type, service_provider_id = await _resolve_org_pk(
                session, payload.service_provider, "serviceProvider"
            )
            part_of_pk = await _resolve_part_of_pk(session, payload.part_of)

            encounter = EncounterModel(
                user_id=user_id,
                org_id=org_id,
                status=payload.status,
                class_system=payload.class_system,
                class_code=payload.class_code,
                class_display=payload.class_display,
                service_type_system=payload.service_type_system,
                service_type_code=payload.service_type_code,
                service_type_display=payload.service_type_display,
                service_type_text=payload.service_type_text,
                priority_system=payload.priority_system,
                priority_code=payload.priority_code,
                priority_display=payload.priority_display,
                priority_text=payload.priority_text,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=subject_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
                length_value=payload.length_value,
                length_comparator=payload.length_comparator,
                length_unit=payload.length_unit,
                length_system=payload.length_system,
                length_code=payload.length_code,
                service_provider_type=service_provider_type,
                service_provider_id=service_provider_id,
                service_provider_display=payload.service_provider_display,
                part_of_id=part_of_pk,
                created_by=created_by,
            )

            # identifier
            if payload.identifier:
                for inp in payload.identifier:
                    encounter.identifiers.append(EncounterIdentifier(
                        org_id=org_id,
                        use=inp.use,
                        type_system=inp.type_system, type_code=inp.type_code,
                        type_display=inp.type_display, type_text=inp.type_text,
                        system=inp.system, value=inp.value,
                        period_start=inp.period_start, period_end=inp.period_end,
                        assigner=inp.assigner,
                    ))

            # statusHistory
            if payload.status_history:
                for sh in payload.status_history:
                    encounter.status_history.append(EncounterStatusHistory(
                        org_id=org_id, status=sh.status,
                        period_start=sh.period_start, period_end=sh.period_end,
                    ))

            # classHistory
            if payload.class_history:
                for ch in payload.class_history:
                    encounter.class_history.append(EncounterClassHistory(
                        org_id=org_id,
                        class_system=ch.class_system, class_version=ch.class_version,
                        class_code=ch.class_code, class_display=ch.class_display,
                        period_start=ch.period_start, period_end=ch.period_end,
                    ))

            # type[]
            if payload.type:
                for t in payload.type:
                    encounter.types.append(EncounterType(
                        org_id=org_id,
                        coding_system=t.coding_system, coding_code=t.coding_code,
                        coding_display=t.coding_display, text=t.text,
                    ))

            # episodeOfCare[]
            if payload.episode_of_care:
                for e in payload.episode_of_care:
                    eoc_type_str, eoc_id = _parse_ref(e.reference)
                    eoc_type = _cast_ref_type(eoc_type_str, EncounterEpisodeOfCareReferenceType, "episodeOfCare.reference")
                    encounter.episode_of_cares.append(EncounterEpisodeOfCare(
                        org_id=org_id,
                        reference_type=eoc_type, reference_id=eoc_id,
                        reference_display=e.reference_display,
                    ))

            # basedOn[] (R4: Reference(ServiceRequest) only)
            if payload.based_on:
                for b in payload.based_on:
                    bo_type_str, bo_id = _parse_ref(b.reference)
                    bo_type = _cast_ref_type(bo_type_str, EncounterBasedOnReferenceType, "basedOn.reference")
                    encounter.based_ons.append(EncounterBasedOn(
                        org_id=org_id, reference_type=bo_type,
                        reference_id=bo_id, reference_display=b.reference_display,
                    ))

            # participant[] (R4: individual is Practitioner|PractitionerRole|RelatedPerson)
            if payload.participant:
                for p in payload.participant:
                    ref_type = None
                    ref_id = None
                    if p.reference:
                        ref_type_str, ref_id = _parse_ref(p.reference)
                        ref_type = _cast_ref_type(ref_type_str, EncounterParticipantReferenceType, "participant.individual")
                    participant = EncounterParticipant(
                        org_id=org_id,
                        reference_type=ref_type, reference_id=ref_id,
                        reference_display=p.reference_display,
                        period_start=p.period_start, period_end=p.period_end,
                    )
                    if p.type:
                        for pt in p.type:
                            participant.types.append(EncounterParticipantType(
                                org_id=org_id,
                                coding_system=pt.coding_system, coding_code=pt.coding_code,
                                coding_display=pt.coding_display, text=pt.text,
                            ))
                    encounter.participants.append(participant)

            # appointment[]
            if payload.appointment:
                for a in payload.appointment:
                    appt_type_str, appt_id = _parse_ref(a.reference)
                    appt_type = _cast_ref_type(appt_type_str, EncounterAppointmentReferenceType, "appointment.reference")
                    encounter.appointment_refs.append(EncounterAppointmentRef(
                        org_id=org_id,
                        reference_type=appt_type, reference_id=appt_id,
                        reference_display=a.reference_display,
                    ))

            # reasonCode[] (0..* CodeableConcept)
            if payload.reason_code:
                for rc in payload.reason_code:
                    encounter.reason_codes.append(EncounterReasonCode(
                        org_id=org_id,
                        coding_system=rc.coding_system, coding_code=rc.coding_code,
                        coding_display=rc.coding_display, text=rc.text,
                    ))

            # reasonReference[] (0..* Reference(Condition|Procedure|Observation|ImmunizationRecommendation))
            if payload.reason_reference:
                for rr in payload.reason_reference:
                    rr_type_str, rr_id = _parse_ref(rr.reference)
                    rr_type = _cast_ref_type(rr_type_str, EncounterReasonReferenceType, "reasonReference.reference")
                    encounter.reason_references.append(EncounterReasonReference(
                        org_id=org_id,
                        reference_type=rr_type, reference_id=rr_id,
                        reference_display=rr.reference_display,
                    ))

            # diagnosis[] (condition 1..1, use 0..1, rank 0..1 — flattened per entry)
            if payload.diagnosis:
                for d_inp in payload.diagnosis:
                    cond_type_str, cond_id = _parse_ref(d_inp.condition)
                    cond_type = _cast_ref_type(cond_type_str, EncounterDiagnosisConditionType, "diagnosis.condition")
                    encounter.diagnoses.append(EncounterDiagnosis(
                        org_id=org_id,
                        condition_type=cond_type, condition_id=cond_id,
                        condition_display=d_inp.condition_display,
                        use_system=d_inp.use_system, use_code=d_inp.use_code,
                        use_display=d_inp.use_display, use_text=d_inp.use_text,
                        rank=d_inp.rank,
                    ))

            # account[]
            if payload.account:
                for a in payload.account:
                    acct_type_str, acct_id = _parse_ref(a.reference)
                    acct_type = _cast_ref_type(acct_type_str, EncounterAccountReferenceType, "account.reference")
                    encounter.accounts.append(EncounterAccount(
                        org_id=org_id,
                        reference_type=acct_type, reference_id=acct_id,
                        reference_display=a.reference_display,
                    ))

            # hospitalization (flat columns on main table)
            if payload.hospitalization:
                hosp = payload.hospitalization
                origin_type_str, origin_id = _parse_ref(hosp.origin)
                dest_type_str, dest_id = _parse_ref(hosp.destination)
                encounter.hospitalization_pre_admission_identifier_system = hosp.pre_admission_identifier_system
                encounter.hospitalization_pre_admission_identifier_value = hosp.pre_admission_identifier_value
                encounter.hospitalization_origin_type = origin_type_str
                encounter.hospitalization_origin_id = origin_id
                encounter.hospitalization_origin_display = hosp.origin_display
                encounter.hospitalization_admit_source_system = hosp.admit_source_system
                encounter.hospitalization_admit_source_code = hosp.admit_source_code
                encounter.hospitalization_admit_source_display = hosp.admit_source_display
                encounter.hospitalization_admit_source_text = hosp.admit_source_text
                encounter.hospitalization_re_admission_system = hosp.re_admission_system
                encounter.hospitalization_re_admission_code = hosp.re_admission_code
                encounter.hospitalization_re_admission_display = hosp.re_admission_display
                encounter.hospitalization_re_admission_text = hosp.re_admission_text
                encounter.hospitalization_destination_type = dest_type_str
                encounter.hospitalization_destination_id = dest_id
                encounter.hospitalization_destination_display = hosp.destination_display
                encounter.hospitalization_discharge_disposition_system = hosp.discharge_disposition_system
                encounter.hospitalization_discharge_disposition_code = hosp.discharge_disposition_code
                encounter.hospitalization_discharge_disposition_display = hosp.discharge_disposition_display
                encounter.hospitalization_discharge_disposition_text = hosp.discharge_disposition_text

                # hospitalization.dietPreference[] / specialArrangement[] / specialCourtesy[]
                for dp in (hosp.diet_preference or []):
                    encounter.diet_preferences.append(EncounterDietPreference(
                        org_id=org_id,
                        coding_system=dp.coding_system, coding_code=dp.coding_code,
                        coding_display=dp.coding_display, text=dp.text,
                    ))
                for sa in (hosp.special_arrangement or []):
                    encounter.special_arrangements.append(EncounterSpecialArrangement(
                        org_id=org_id,
                        coding_system=sa.coding_system, coding_code=sa.coding_code,
                        coding_display=sa.coding_display, text=sa.text,
                    ))
                for sc in (hosp.special_courtesy or []):
                    encounter.special_courtesies.append(EncounterSpecialCourtesy(
                        org_id=org_id,
                        coding_system=sc.coding_system, coding_code=sc.coding_code,
                        coding_display=sc.coding_display, text=sc.text,
                    ))

            # location[]
            if payload.location:
                for loc in payload.location:
                    loc_type_str, loc_id = _parse_ref(loc.reference)
                    loc_type = _cast_ref_type(loc_type_str, EncounterLocationReferenceType, "location.reference")
                    encounter.locations.append(EncounterLocation(
                        org_id=org_id,
                        reference_type=loc_type, reference_id=loc_id,
                        reference_display=loc.reference_display,
                        status=loc.status,
                        physical_type_system=loc.physical_type_system,
                        physical_type_code=loc.physical_type_code,
                        physical_type_display=loc.physical_type_display,
                        physical_type_text=loc.physical_type_text,
                        period_start=loc.period_start, period_end=loc.period_end,
                    ))

            try:
                session.add(encounter)
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter.encounter_id)

    async def patch(
        self,
        encounter_id: int,
        payload: EncounterPatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[EncounterModel]:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            encounter = (await session.execute(stmt)).scalars().first()
            if not encounter:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(encounter, field, value)
            if updated_by is not None:
                encounter.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter_id)

    async def delete(self, encounter_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            encounter = (await session.execute(stmt)).scalars().first()
            if not encounter:
                return False
            try:
                await session.delete(encounter)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

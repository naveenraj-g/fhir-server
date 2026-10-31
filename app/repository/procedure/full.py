from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.procedure import (
    ProcedureBasedOn,
    ProcedureBodySite,
    ProcedureBodySiteCoding,
    ProcedureCategoryCoding,
    ProcedureCodeCoding,
    ProcedureComplication,
    ProcedureComplicationCoding,
    ProcedureComplicationDetail,
    ProcedureFocalDevice,
    ProcedureFocalDeviceActionCoding,
    ProcedureFollowUp,
    ProcedureFollowUpCoding,
    ProcedureIdentifier,
    ProcedureIdentifierTypeCoding,
    ProcedureModel,
    ProcedureNote,
    ProcedureOutcomeCoding,
    ProcedurePartOf,
    ProcedurePerformer,
    ProcedurePerformerFunctionCoding,
    ProcedureReasonCode,
    ProcedureReasonCodeCoding,
    ProcedureReasonReference,
    ProcedureReport,
    ProcedureStatusReasonCoding,
    ProcedureUsedCode,
    ProcedureUsedCodeCoding,
    ProcedureUsedReference,
)
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema

from ._shared import (
    _parse_asserter_ref,
    _parse_assigner_ref,
    _parse_author_ref,
    _parse_based_on_ref,
    _parse_complication_detail_ref,
    _parse_encounter_ref,
    _parse_focal_device_manipulated_ref,
    _parse_location_ref,
    _parse_part_of_ref,
    _parse_performer_actor_ref,
    _parse_performer_on_behalf_of_ref,
    _parse_reason_reference_ref,
    _parse_recorder_ref,
    _parse_report_ref,
    _parse_subject_ref,
    _parse_used_reference_ref,
    _validate_ref,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifiers(session, procedure_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = ProcedureIdentifier(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()
        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    ProcedureIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_based_on(session, procedure_pk: int, org_id: str, based_on, created_by: str) -> None:
    for b in based_on or []:
        b_type, b_id = _parse_based_on_ref(b)
        if b_type and b_id:
            await _validate_ref(session, org_id, b_type, b_id, "based_on")
        session.add(
            ProcedureBasedOn(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=b,
                reference_type=b_type,
                reference_id=b_id,
                created_by=created_by,
            )
        )


async def _add_part_of(session, procedure_pk: int, org_id: str, part_of, created_by: str) -> None:
    for p in part_of or []:
        p_type, p_id = _parse_part_of_ref(p)
        if p_type and p_id:
            await _validate_ref(session, org_id, p_type, p_id, "part_of")
        session.add(
            ProcedurePartOf(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=p,
                reference_type=p_type,
                reference_id=p_id,
                created_by=created_by,
            )
        )


async def _add_status_reason_codings(session, procedure_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            ProcedureStatusReasonCoding(
                procedure_pk=procedure_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_category_codings(session, procedure_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            ProcedureCategoryCoding(
                procedure_pk=procedure_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_code_codings(session, procedure_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            ProcedureCodeCoding(
                procedure_pk=procedure_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_outcome_codings(session, procedure_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            ProcedureOutcomeCoding(
                procedure_pk=procedure_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_performers(session, procedure_pk: int, org_id: str, performers, created_by: str) -> None:
    for p in performers or []:
        a_type, a_id = _parse_performer_actor_ref(p.actor)
        await _validate_ref(session, org_id, a_type, a_id, "performer.actor")

        ob_type, ob_id = _parse_performer_on_behalf_of_ref(p.on_behalf_of) if p.on_behalf_of else (None, None)
        if ob_type and ob_id:
            await _validate_ref(session, org_id, ob_type, ob_id, "performer.on_behalf_of")

        perf = ProcedurePerformer(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            function_text=p.function.text if p.function else None,
            actor_reference=p.actor,
            actor_type=a_type,
            actor_id=a_id,
            actor_display=p.actor_display,
            on_behalf_of_reference=p.on_behalf_of,
            on_behalf_of_type=ob_type,
            on_behalf_of_id=ob_id,
            on_behalf_of_display=p.on_behalf_of_display,
            created_by=created_by,
        )
        session.add(perf)
        await session.flush()

        if p.function and p.function.coding:
            for c in p.function.coding:
                session.add(
                    ProcedurePerformerFunctionCoding(
                        performer_id=perf.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_reason_codes(session, procedure_pk: int, org_id: str, reason_codes, created_by: str) -> None:
    for rc in reason_codes or []:
        row = ProcedureReasonCode(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            text=rc.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        if rc.coding:
            for c in rc.coding:
                session.add(
                    ProcedureReasonCodeCoding(
                        reason_code_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_reason_references(session, procedure_pk: int, org_id: str, reason_references, created_by: str) -> None:
    for rr in reason_references or []:
        rr_type, rr_id = _parse_reason_reference_ref(rr)
        if rr_type and rr_id:
            await _validate_ref(session, org_id, rr_type, rr_id, "reason_reference")
        session.add(
            ProcedureReasonReference(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=rr,
                reference_type=rr_type,
                reference_id=rr_id,
                created_by=created_by,
            )
        )


async def _add_body_sites(session, procedure_pk: int, org_id: str, body_sites, created_by: str) -> None:
    for bs in body_sites or []:
        row = ProcedureBodySite(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            text=bs.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        if bs.coding:
            for c in bs.coding:
                session.add(
                    ProcedureBodySiteCoding(
                        body_site_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_reports(session, procedure_pk: int, org_id: str, reports, created_by: str) -> None:
    for r in reports or []:
        r_type, r_id = _parse_report_ref(r)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "report")
        session.add(
            ProcedureReport(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=r,
                reference_type=r_type,
                reference_id=r_id,
                created_by=created_by,
            )
        )


async def _add_complications(session, procedure_pk: int, org_id: str, complications, created_by: str) -> None:
    for comp in complications or []:
        row = ProcedureComplication(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            text=comp.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        if comp.coding:
            for c in comp.coding:
                session.add(
                    ProcedureComplicationCoding(
                        complication_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_complication_details(session, procedure_pk: int, org_id: str, complication_details, created_by: str) -> None:
    for cd in complication_details or []:
        cd_type, cd_id = _parse_complication_detail_ref(cd)
        if cd_type and cd_id:
            await _validate_ref(session, org_id, cd_type, cd_id, "complication_detail")
        session.add(
            ProcedureComplicationDetail(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=cd,
                reference_type=cd_type,
                reference_id=cd_id,
                created_by=created_by,
            )
        )


async def _add_follow_ups(session, procedure_pk: int, org_id: str, follow_ups, created_by: str) -> None:
    for fu in follow_ups or []:
        row = ProcedureFollowUp(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            text=fu.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        if fu.coding:
            for c in fu.coding:
                session.add(
                    ProcedureFollowUpCoding(
                        follow_up_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_notes(session, procedure_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        auth_type, auth_id = _parse_author_ref(n.author_reference) if n.author_reference else (None, None)
        if auth_type and auth_id:
            await _validate_ref(session, org_id, auth_type, auth_id, "note.author_reference")
        session.add(
            ProcedureNote(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                author_string=n.author_string,
                author_reference_reference=n.author_reference,
                author_reference_type=auth_type,
                author_reference_id=auth_id,
                author_reference_display=n.author_reference_display,
                time=n.time,
                text=n.text,
                created_by=created_by,
            )
        )


async def _add_focal_devices(session, procedure_pk: int, org_id: str, focal_devices, created_by: str) -> None:
    for d in focal_devices or []:
        m_type, m_id = _parse_focal_device_manipulated_ref(d.manipulated)
        await _validate_ref(session, org_id, m_type, m_id, "focal_device.manipulated")

        row = ProcedureFocalDevice(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            action_text=d.action.text if d.action else None,
            manipulated_reference=d.manipulated,
            manipulated_type=m_type,
            manipulated_id=m_id,
            manipulated_display=d.manipulated_display,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()

        if d.action and d.action.coding:
            for c in d.action.coding:
                session.add(
                    ProcedureFocalDeviceActionCoding(
                        focal_device_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_used_references(session, procedure_pk: int, org_id: str, used_references, created_by: str) -> None:
    for ur in used_references or []:
        ur_type, ur_id = _parse_used_reference_ref(ur)
        if ur_type and ur_id:
            await _validate_ref(session, org_id, ur_type, ur_id, "used_reference")
        session.add(
            ProcedureUsedReference(
                procedure_pk=procedure_pk,
                tenant_id=org_id,
                reference_reference=ur,
                reference_type=ur_type,
                reference_id=ur_id,
                created_by=created_by,
            )
        )


async def _add_used_codes(session, procedure_pk: int, org_id: str, used_codes, created_by: str) -> None:
    for uc in used_codes or []:
        row = ProcedureUsedCode(
            procedure_pk=procedure_pk,
            tenant_id=org_id,
            text=uc.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        if uc.coding:
            for c in uc.coding:
                session.add(
                    ProcedureUsedCodeCoding(
                        used_code_id=row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


class _FullMixin:
    """Full atomic CRUD operations for Procedure."""

    async def create_full(
        self,
        payload: ProcedureCreateSchema,
        org_id: str,
        created_by: str,
    ) -> ProcedureModel:
        async with self.session_factory() as session:
            s_type, s_id = _parse_subject_ref(payload.subject)
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            e_type, e_id = _parse_encounter_ref(payload.encounter) if payload.encounter else (None, None)
            if e_type and e_id:
                await _validate_ref(session, org_id, e_type, e_id, "encounter")

            rec_type, rec_id = _parse_recorder_ref(payload.recorder) if payload.recorder else (None, None)
            if rec_type and rec_id:
                await _validate_ref(session, org_id, rec_type, rec_id, "recorder")

            ass_type, ass_id = _parse_asserter_ref(payload.asserter) if payload.asserter else (None, None)
            if ass_type and ass_id:
                await _validate_ref(session, org_id, ass_type, ass_id, "asserter")

            loc_type, loc_id = _parse_location_ref(payload.location) if payload.location else (None, None)
            if loc_type and loc_id:
                await _validate_ref(session, org_id, loc_type, loc_id, "location")

            procedure = ProcedureModel(
                tenant_id=org_id,
                created_by=created_by,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                status=payload.status,
                status_reason_text=payload.status_reason.text if payload.status_reason else None,
                category_text=payload.category.text if payload.category else None,
                code_text=payload.code.text if payload.code else None,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject_display,
                encounter_reference=payload.encounter,
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=payload.encounter_display,
                performed_date_time=payload.performed_date_time,
                performed_period_start=payload.performed_period_start,
                performed_period_end=payload.performed_period_end,
                performed_string=payload.performed_string,
                performed_age=payload.performed_age,
                performed_range=payload.performed_range,
                recorder_reference=payload.recorder,
                recorder_type=rec_type,
                recorder_id=rec_id,
                recorder_display=payload.recorder_display,
                asserter_reference=payload.asserter,
                asserter_type=ass_type,
                asserter_id=ass_id,
                asserter_display=payload.asserter_display,
                location_reference=payload.location,
                location_type=loc_type,
                location_id=loc_id,
                location_display=payload.location_display,
                outcome_text=payload.outcome.text if payload.outcome else None,
                extension=payload.extension,
            )
            session.add(procedure)
            await session.flush()

            # Add collections and codings
            await _add_identifiers(session, procedure.id, org_id, payload.identifier, created_by)
            await _add_based_on(session, procedure.id, org_id, payload.based_on, created_by)
            await _add_part_of(session, procedure.id, org_id, payload.part_of, created_by)

            if payload.status_reason and payload.status_reason.coding:
                await _add_status_reason_codings(session, procedure.id, org_id, payload.status_reason.coding, created_by)

            if payload.category and payload.category.coding:
                await _add_category_codings(session, procedure.id, org_id, payload.category.coding, created_by)

            if payload.code and payload.code.coding:
                await _add_code_codings(session, procedure.id, org_id, payload.code.coding, created_by)

            await _add_performers(session, procedure.id, org_id, payload.performer, created_by)
            await _add_reason_codes(session, procedure.id, org_id, payload.reason_code, created_by)
            await _add_reason_references(session, procedure.id, org_id, payload.reason_reference, created_by)
            await _add_body_sites(session, procedure.id, org_id, payload.body_site, created_by)

            if payload.outcome and payload.outcome.coding:
                await _add_outcome_codings(session, procedure.id, org_id, payload.outcome.coding, created_by)

            await _add_reports(session, procedure.id, org_id, payload.report, created_by)
            await _add_complications(session, procedure.id, org_id, payload.complication, created_by)
            await _add_complication_details(session, procedure.id, org_id, payload.complication_detail, created_by)
            await _add_follow_ups(session, procedure.id, org_id, payload.follow_up, created_by)
            await _add_notes(session, procedure.id, org_id, payload.note, created_by)
            await _add_focal_devices(session, procedure.id, org_id, payload.focal_device, created_by)
            await _add_used_references(session, procedure.id, org_id, payload.used_reference, created_by)
            await _add_used_codes(session, procedure.id, org_id, payload.used_code, created_by)

            await session.commit()

        return await self.get_by_procedure_id_in_org(procedure.procedure_id, org_id)

    async def patch_full(
        self,
        procedure_id: int,
        payload: ProcedurePatchSchema,
        org_id: str,
        updated_by: str,
    ) -> ProcedureModel | None:
        async with self.session_factory() as session:
            stmt = select(ProcedureModel).where(
                ProcedureModel.procedure_id == procedure_id,
                ProcedureModel.tenant_id == org_id,
            )
            procedure = (await session.execute(stmt)).scalars().first()
            if not procedure:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set:
                procedure.status = payload.status
            if "instantiates_canonical" in fields_set:
                procedure.instantiates_canonical = payload.instantiates_canonical
            if "instantiates_uri" in fields_set:
                procedure.instantiates_uri = payload.instantiates_uri
            if "extension" in fields_set:
                procedure.extension = payload.extension

            # Performed fields
            if "performed_date_time" in fields_set:
                procedure.performed_date_time = payload.performed_date_time
            if "performed_period_start" in fields_set:
                procedure.performed_period_start = payload.performed_period_start
            if "performed_period_end" in fields_set:
                procedure.performed_period_end = payload.performed_period_end
            if "performed_string" in fields_set:
                procedure.performed_string = payload.performed_string
            if "performed_age" in fields_set:
                procedure.performed_age = payload.performed_age
            if "performed_range" in fields_set:
                procedure.performed_range = payload.performed_range

            if "subject" in fields_set or "subject_display" in fields_set:
                if payload.subject:
                    s_type, s_id = _parse_subject_ref(payload.subject)
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                    procedure.subject_reference = payload.subject
                    procedure.subject_type = s_type
                    procedure.subject_id = s_id
                elif "subject" in fields_set and payload.subject is None:
                    procedure.subject_reference = None
                    procedure.subject_type = None
                    procedure.subject_id = None
                if "subject_display" in fields_set:
                    procedure.subject_display = payload.subject_display

            if "encounter" in fields_set or "encounter_display" in fields_set:
                if payload.encounter:
                    e_type, e_id = _parse_encounter_ref(payload.encounter)
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                    procedure.encounter_reference = payload.encounter
                    procedure.encounter_type = e_type
                    procedure.encounter_id = e_id
                elif "encounter" in fields_set and payload.encounter is None:
                    procedure.encounter_reference = None
                    procedure.encounter_type = None
                    procedure.encounter_id = None
                if "encounter_display" in fields_set:
                    procedure.encounter_display = payload.encounter_display

            if "recorder" in fields_set or "recorder_display" in fields_set:
                if payload.recorder:
                    rec_type, rec_id = _parse_recorder_ref(payload.recorder)
                    await _validate_ref(session, org_id, rec_type, rec_id, "recorder")
                    procedure.recorder_reference = payload.recorder
                    procedure.recorder_type = rec_type
                    procedure.recorder_id = rec_id
                elif "recorder" in fields_set and payload.recorder is None:
                    procedure.recorder_reference = None
                    procedure.recorder_type = None
                    procedure.recorder_id = None
                if "recorder_display" in fields_set:
                    procedure.recorder_display = payload.recorder_display

            if "asserter" in fields_set or "asserter_display" in fields_set:
                if payload.asserter:
                    ass_type, ass_id = _parse_asserter_ref(payload.asserter)
                    await _validate_ref(session, org_id, ass_type, ass_id, "asserter")
                    procedure.asserter_reference = payload.asserter
                    procedure.asserter_type = ass_type
                    procedure.asserter_id = ass_id
                elif "asserter" in fields_set and payload.asserter is None:
                    procedure.asserter_reference = None
                    procedure.asserter_type = None
                    procedure.asserter_id = None
                if "asserter_display" in fields_set:
                    procedure.asserter_display = payload.asserter_display

            if "location" in fields_set or "location_display" in fields_set:
                if payload.location:
                    loc_type, loc_id = _parse_location_ref(payload.location)
                    await _validate_ref(session, org_id, loc_type, loc_id, "location")
                    procedure.location_reference = payload.location
                    procedure.location_type = loc_type
                    procedure.location_id = loc_id
                elif "location" in fields_set and payload.location is None:
                    procedure.location_reference = None
                    procedure.location_type = None
                    procedure.location_id = None
                if "location_display" in fields_set:
                    procedure.location_display = payload.location_display

            # 0..1 Concept fields
            if "status_reason" in fields_set:
                procedure.status_reason_text = payload.status_reason.text if payload.status_reason else None
                await session.execute(
                    delete(ProcedureStatusReasonCoding).where(
                        ProcedureStatusReasonCoding.procedure_pk == procedure.id
                    )
                )
                if payload.status_reason and payload.status_reason.coding:
                    await _add_status_reason_codings(
                        session, procedure.id, org_id, payload.status_reason.coding, updated_by
                    )

            if "category" in fields_set:
                procedure.category_text = payload.category.text if payload.category else None
                await session.execute(
                    delete(ProcedureCategoryCoding).where(
                        ProcedureCategoryCoding.procedure_pk == procedure.id
                    )
                )
                if payload.category and payload.category.coding:
                    await _add_category_codings(
                        session, procedure.id, org_id, payload.category.coding, updated_by
                    )

            if "code" in fields_set:
                procedure.code_text = payload.code.text if payload.code else None
                await session.execute(
                    delete(ProcedureCodeCoding).where(
                        ProcedureCodeCoding.procedure_pk == procedure.id
                    )
                )
                if payload.code and payload.code.coding:
                    await _add_code_codings(
                        session, procedure.id, org_id, payload.code.coding, updated_by
                    )

            if "outcome" in fields_set:
                procedure.outcome_text = payload.outcome.text if payload.outcome else None
                await session.execute(
                    delete(ProcedureOutcomeCoding).where(
                        ProcedureOutcomeCoding.procedure_pk == procedure.id
                    )
                )
                if payload.outcome and payload.outcome.coding:
                    await _add_outcome_codings(
                        session, procedure.id, org_id, payload.outcome.coding, updated_by
                    )

            # Collection fields
            if "identifier" in fields_set:
                await session.execute(
                    delete(ProcedureIdentifier).where(
                        ProcedureIdentifier.procedure_pk == procedure.id
                    )
                )
                await _add_identifiers(session, procedure.id, org_id, payload.identifier, updated_by)

            if "based_on" in fields_set:
                await session.execute(
                    delete(ProcedureBasedOn).where(
                        ProcedureBasedOn.procedure_pk == procedure.id
                    )
                )
                await _add_based_on(session, procedure.id, org_id, payload.based_on, updated_by)

            if "part_of" in fields_set:
                await session.execute(
                    delete(ProcedurePartOf).where(
                        ProcedurePartOf.procedure_pk == procedure.id
                    )
                )
                await _add_part_of(session, procedure.id, org_id, payload.part_of, updated_by)

            if "performer" in fields_set:
                await session.execute(
                    delete(ProcedurePerformer).where(
                        ProcedurePerformer.procedure_pk == procedure.id
                    )
                )
                await _add_performers(session, procedure.id, org_id, payload.performer, updated_by)

            if "reason_code" in fields_set:
                await session.execute(
                    delete(ProcedureReasonCode).where(
                        ProcedureReasonCode.procedure_pk == procedure.id
                    )
                )
                await _add_reason_codes(session, procedure.id, org_id, payload.reason_code, updated_by)

            if "reason_reference" in fields_set:
                await session.execute(
                    delete(ProcedureReasonReference).where(
                        ProcedureReasonReference.procedure_pk == procedure.id
                    )
                )
                await _add_reason_references(session, procedure.id, org_id, payload.reason_reference, updated_by)

            if "body_site" in fields_set:
                await session.execute(
                    delete(ProcedureBodySite).where(
                        ProcedureBodySite.procedure_pk == procedure.id
                    )
                )
                await _add_body_sites(session, procedure.id, org_id, payload.body_site, updated_by)

            if "report" in fields_set:
                await session.execute(
                    delete(ProcedureReport).where(
                        ProcedureReport.procedure_pk == procedure.id
                    )
                )
                await _add_reports(session, procedure.id, org_id, payload.report, updated_by)

            if "complication" in fields_set:
                await session.execute(
                    delete(ProcedureComplication).where(
                        ProcedureComplication.procedure_pk == procedure.id
                    )
                )
                await _add_complications(session, procedure.id, org_id, payload.complication, updated_by)

            if "complication_detail" in fields_set:
                await session.execute(
                    delete(ProcedureComplicationDetail).where(
                        ProcedureComplicationDetail.procedure_pk == procedure.id
                    )
                )
                await _add_complication_details(session, procedure.id, org_id, payload.complication_detail, updated_by)

            if "follow_up" in fields_set:
                await session.execute(
                    delete(ProcedureFollowUp).where(
                        ProcedureFollowUp.procedure_pk == procedure.id
                    )
                )
                await _add_follow_ups(session, procedure.id, org_id, payload.follow_up, updated_by)

            if "note" in fields_set:
                await session.execute(
                    delete(ProcedureNote).where(
                        ProcedureNote.procedure_pk == procedure.id
                    )
                )
                await _add_notes(session, procedure.id, org_id, payload.note, updated_by)

            if "focal_device" in fields_set:
                await session.execute(
                    delete(ProcedureFocalDevice).where(
                        ProcedureFocalDevice.procedure_pk == procedure.id
                    )
                )
                await _add_focal_devices(session, procedure.id, org_id, payload.focal_device, updated_by)

            if "used_reference" in fields_set:
                await session.execute(
                    delete(ProcedureUsedReference).where(
                        ProcedureUsedReference.procedure_pk == procedure.id
                    )
                )
                await _add_used_references(session, procedure.id, org_id, payload.used_reference, updated_by)

            if "used_code" in fields_set:
                await session.execute(
                    delete(ProcedureUsedCode).where(
                        ProcedureUsedCode.procedure_pk == procedure.id
                    )
                )
                await _add_used_codes(session, procedure.id, org_id, payload.used_code, updated_by)

            procedure.updated_by = updated_by
            await session.commit()

        return await self.get_by_procedure_id_in_org(procedure.procedure_id, org_id)

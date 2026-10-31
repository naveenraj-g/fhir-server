from sqlalchemy import delete, func, select

from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.task import (
    TaskBasedOn,
    TaskBusinessStatusCoding,
    TaskCodeCoding,
    TaskIdentifier,
    TaskIdentifierTypeCoding,
    TaskInput,
    TaskInputTypeCoding,
    TaskInsurance,
    TaskModel,
    TaskNote,
    TaskOutput,
    TaskOutputTypeCoding,
    TaskPartOf,
    TaskPerformerType,
    TaskPerformerTypeCoding,
    TaskReasonCodeCoding,
    TaskRelevantHistory,
    TaskRestrictionRecipient,
    TaskStatusReasonCoding,
)
from app.schemas.task import TaskCreateSchema, TaskPatchSchema

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_assigner_ref,
    _parse_encounter_ref,
    _parse_generic_ref,
    _parse_insurance_ref,
    _parse_location_ref,
    _parse_owner_ref,
    _parse_part_of_ref,
    _parse_recipient_ref,
    _parse_relevant_history_ref,
    _parse_requester_ref,
    _validate_ref,
    _with_relationships,
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


async def _add_identifiers(
    session, task_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = TaskIdentifier(
            task_pk=task_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type_text,
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

        for c in i.type_coding or []:
            session.add(
                TaskIdentifierTypeCoding(
                    task_identifier_id=ident.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_codings(session, model_cls, task_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            model_cls(
                task_pk=task_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_performer_types(
    session, task_pk: int, org_id: str, performer_types, created_by: str
) -> None:
    for pt in performer_types or []:
        row = TaskPerformerType(
            task_pk=task_pk,
            tenant_id=org_id,
            text=pt.text,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()

        for c in pt.coding or []:
            session.add(
                TaskPerformerTypeCoding(
                    task_performer_type_id=row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_based_on(
    session, task_pk: int, org_id: str, items, created_by: str
) -> None:
    for r in items or []:
        ref_str = r.reference if hasattr(r, "reference") else str(r)
        display = getattr(r, "display", None) if hasattr(r, "display") else None
        r_type, r_id = _parse_generic_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "based_on")
        session.add(
            TaskBasedOn(
                task_pk=task_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=display,
                created_by=created_by,
            )
        )


async def _add_part_of(
    session, task_pk: int, org_id: str, items, created_by: str
) -> None:
    for r in items or []:
        ref_str = r.reference if hasattr(r, "reference") else str(r)
        display = getattr(r, "display", None) if hasattr(r, "display") else None
        r_type, r_id = _parse_part_of_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "part_of")
        session.add(
            TaskPartOf(
                task_pk=task_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=display,
                created_by=created_by,
            )
        )


async def _add_insurance(
    session, task_pk: int, org_id: str, items, created_by: str
) -> None:
    for r in items or []:
        ref_str = r.reference if hasattr(r, "reference") else str(r)
        display = getattr(r, "display", None) if hasattr(r, "display") else None
        r_type, r_id = _parse_insurance_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "insurance")
        session.add(
            TaskInsurance(
                task_pk=task_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=display,
                created_by=created_by,
            )
        )


async def _add_relevant_history(
    session, task_pk: int, org_id: str, items, created_by: str
) -> None:
    for r in items or []:
        ref_str = r.reference if hasattr(r, "reference") else str(r)
        display = getattr(r, "display", None) if hasattr(r, "display") else None
        r_type, r_id = _parse_relevant_history_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "relevant_history")
        session.add(
            TaskRelevantHistory(
                task_pk=task_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=display,
                created_by=created_by,
            )
        )


async def _add_restriction_recipients(
    session, task_pk: int, org_id: str, items, created_by: str
) -> None:
    for r in items or []:
        ref_str = r.reference if hasattr(r, "reference") else str(r)
        display = getattr(r, "display", None) if hasattr(r, "display") else None
        r_type, r_id = _parse_recipient_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "restriction.recipient")
        session.add(
            TaskRestrictionRecipient(
                task_pk=task_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=display,
                created_by=created_by,
            )
        )


def _add_notes(session, task_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        r_type, r_id = (
            _parse_generic_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        session.add(
            TaskNote(
                task_pk=task_pk,
                tenant_id=org_id,
                author_string=n.author_string,
                author_reference=n.author_reference,
                author_type=r_type,
                author_id=r_id,
                author_display=n.author_display,
                time=n.time,
                text=n.text,
                created_by=created_by,
            )
        )


async def _add_inputs(
    session, task_pk: int, org_id: str, inputs, created_by: str
) -> None:
    for inp in inputs or []:
        r_type, r_id = (
            _parse_generic_ref(inp.value_reference)
            if inp.value_reference
            else (None, None)
        )
        row = TaskInput(
            task_pk=task_pk,
            tenant_id=org_id,
            type_text=inp.type_text,
            value_string=inp.value_string,
            value_boolean=inp.value_boolean,
            value_integer=inp.value_integer,
            value_decimal=inp.value_decimal,
            value_date=inp.value_date,
            value_date_time=inp.value_date_time,
            value_time=inp.value_time,
            value_uri=inp.value_uri,
            value_code=inp.value_code,
            value_reference_reference=inp.value_reference,
            value_reference_type=r_type,
            value_reference_id=r_id,
            value_reference_display=inp.value_reference_display,
            value_json=inp.value_json,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()

        for c in inp.type_coding or []:
            session.add(
                TaskInputTypeCoding(
                    task_input_id=row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_outputs(
    session, task_pk: int, org_id: str, outputs, created_by: str
) -> None:
    for out in outputs or []:
        r_type, r_id = (
            _parse_generic_ref(out.value_reference)
            if out.value_reference
            else (None, None)
        )
        row = TaskOutput(
            task_pk=task_pk,
            tenant_id=org_id,
            type_text=out.type_text,
            value_string=out.value_string,
            value_boolean=out.value_boolean,
            value_integer=out.value_integer,
            value_decimal=out.value_decimal,
            value_date=out.value_date,
            value_date_time=out.value_date_time,
            value_time=out.value_time,
            value_uri=out.value_uri,
            value_code=out.value_code,
            value_reference_reference=out.value_reference,
            value_reference_type=r_type,
            value_reference_id=r_id,
            value_reference_display=out.value_reference_display,
            value_json=out.value_json,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()

        for c in out.type_coding or []:
            session.add(
                TaskOutputTypeCoding(
                    task_output_id=row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


class TaskRepository:
    """Repository handling database operations for Task resources."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_task_id(self, task_id: int) -> TaskModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(TaskModel).where(TaskModel.task_id == task_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_task_id_in_org(
        self, task_id: int, org_id: str
    ) -> TaskModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(TaskModel).where(
                    TaskModel.task_id == task_id,
                    TaskModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def task_belongs_to_org(self, task_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(TaskModel.id).where(
                TaskModel.task_id == task_id,
                TaskModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    async def create_full(
        self, payload: TaskCreateSchema, org_id: str, created_by: str
    ) -> TaskModel:
        async with self.session_factory() as session:
            # Validate reference targets against RESOURCE_REGISTRY
            req_type, req_id = (
                _parse_requester_ref(payload.requester)
                if payload.requester
                else (None, None)
            )
            await _validate_ref(session, org_id, req_type, req_id, "requester")

            owner_type, owner_id = (
                _parse_owner_ref(payload.owner) if payload.owner else (None, None)
            )
            await _validate_ref(session, org_id, owner_type, owner_id, "owner")

            loc_type, loc_id = (
                _parse_location_ref(payload.location)
                if payload.location
                else (None, None)
            )
            await _validate_ref(session, org_id, loc_type, loc_id, "location")

            enc_type, enc_id = (
                _parse_encounter_ref(payload.encounter)
                if payload.encounter
                else (None, None)
            )
            await _validate_ref(session, org_id, enc_type, enc_id, "encounter")

            for_val = payload.for_
            for_type, for_id = (
                _parse_generic_ref(for_val) if for_val else (None, None)
            )
            if for_type and for_id:
                await _validate_ref(session, org_id, for_type, for_id, "for")

            foc_type, foc_id = (
                _parse_generic_ref(payload.focus) if payload.focus else (None, None)
            )
            if foc_type and foc_id:
                await _validate_ref(session, org_id, foc_type, foc_id, "focus")

            rr_type, rr_id = (
                _parse_generic_ref(payload.reason_reference)
                if payload.reason_reference
                else (None, None)
            )
            if rr_type and rr_id:
                await _validate_ref(
                    session, org_id, rr_type, rr_id, "reason_reference"
                )

            grp_a_type, grp_a_id = (
                _parse_assigner_ref(payload.group_identifier_assigner)
                if payload.group_identifier_assigner
                else (None, None)
            )
            if grp_a_type and grp_a_id:
                await _validate_ref(
                    session, org_id, grp_a_type, grp_a_id, "group_identifier.assigner"
                )

            # Extract restriction period & repetitions
            restr_rep = (
                payload.restriction.repetitions
                if payload.restriction
                else None
            )
            restr_p_start = (
                payload.restriction.period_start
                if payload.restriction
                else None
            )
            restr_p_end = (
                payload.restriction.period_end
                if payload.restriction
                else None
            )

            model = TaskModel(
                tenant_id=org_id,
                created_by=created_by,
                status=payload.status,
                intent=payload.intent,
                priority=payload.priority,
                description=payload.description,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                authored_on=payload.authored_on,
                last_modified=payload.last_modified,
                code_text=payload.code_text,
                status_reason_text=payload.status_reason_text,
                business_status_text=payload.business_status_text,
                reason_code_text=payload.reason_code_text,
                focus_reference=payload.focus,
                focus_type=foc_type,
                focus_id=foc_id,
                focus_display=payload.focus_display,
                for_reference=for_val,
                for_type=for_type,
                for_id=for_id,
                for_display=payload.for_display,
                encounter_reference=payload.encounter,
                encounter_type=enc_type,
                encounter_id=enc_id,
                encounter_display=payload.encounter_display,
                execution_period_start=payload.execution_period_start,
                execution_period_end=payload.execution_period_end,
                requester_reference=payload.requester,
                requester_type=req_type,
                requester_id=req_id,
                requester_display=payload.requester_display,
                owner_reference=payload.owner,
                owner_type=owner_type,
                owner_id=owner_id,
                owner_display=payload.owner_display,
                location_reference=payload.location,
                location_type=loc_type,
                location_id=loc_id,
                location_display=payload.location_display,
                reason_reference_reference=payload.reason_reference,
                reason_reference_type=rr_type,
                reason_reference_id=rr_id,
                reason_reference_display=payload.reason_reference_display,
                group_identifier_use=payload.group_identifier_use,
                group_identifier_system=payload.group_identifier_system,
                group_identifier_value=payload.group_identifier_value,
                group_identifier_period_start=payload.group_identifier_period_start,
                group_identifier_period_end=payload.group_identifier_period_end,
                group_identifier_assigner_reference=payload.group_identifier_assigner,
                group_identifier_assigner_type=grp_a_type,
                group_identifier_assigner_id=grp_a_id,
                group_identifier_assigner_display=payload.group_identifier_assigner_display,
                restriction_repetitions=restr_rep,
                restriction_period_start=restr_p_start,
                restriction_period_end=restr_p_end,
            )
            session.add(model)
            await session.flush()

            # Add child rows
            await _add_identifiers(
                session, model.id, org_id, payload.identifier, created_by
            )
            _add_codings(
                session, TaskCodeCoding, model.id, org_id, payload.code_coding, created_by
            )
            _add_codings(
                session,
                TaskStatusReasonCoding,
                model.id,
                org_id,
                payload.status_reason_coding,
                created_by,
            )
            _add_codings(
                session,
                TaskBusinessStatusCoding,
                model.id,
                org_id,
                payload.business_status_coding,
                created_by,
            )
            _add_codings(
                session,
                TaskReasonCodeCoding,
                model.id,
                org_id,
                payload.reason_code_coding,
                created_by,
            )
            await _add_based_on(
                session, model.id, org_id, payload.based_on, created_by
            )
            await _add_part_of(
                session, model.id, org_id, payload.part_of, created_by
            )
            await _add_insurance(
                session, model.id, org_id, payload.insurance, created_by
            )
            await _add_relevant_history(
                session, model.id, org_id, payload.relevant_history, created_by
            )
            if payload.restriction and payload.restriction.recipient:
                await _add_restriction_recipients(
                    session,
                    model.id,
                    org_id,
                    payload.restriction.recipient,
                    created_by,
                )
            await _add_performer_types(
                session, model.id, org_id, payload.performer_type, created_by
            )
            _add_notes(session, model.id, org_id, payload.note, created_by)
            await _add_inputs(
                session, model.id, org_id, payload.input, created_by
            )
            await _add_outputs(
                session, model.id, org_id, payload.output, created_by
            )

            await session.commit()

            stmt = _with_relationships(
                select(TaskModel).where(TaskModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def patch_full(
        self,
        task_id: int,
        payload: TaskPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> TaskModel:
        async with self.session_factory() as session:
            stmt = select(TaskModel).where(
                TaskModel.task_id == task_id,
                TaskModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                raise ValueError(f"Task {task_id} not found in org {org_id}")

            provided = payload.model_fields_set

            if "status" in provided:
                model.status = payload.status
            if "intent" in provided:
                model.intent = payload.intent
            if "priority" in provided:
                model.priority = payload.priority
            if "description" in provided:
                model.description = payload.description
            if "instantiates_canonical" in provided:
                model.instantiates_canonical = payload.instantiates_canonical
            if "instantiates_uri" in provided:
                model.instantiates_uri = payload.instantiates_uri
            if "authored_on" in provided:
                model.authored_on = payload.authored_on
            if "last_modified" in provided:
                model.last_modified = payload.last_modified
            if "code_text" in provided:
                model.code_text = payload.code_text
            if "status_reason_text" in provided:
                model.status_reason_text = payload.status_reason_text
            if "business_status_text" in provided:
                model.business_status_text = payload.business_status_text
            if "reason_code_text" in provided:
                model.reason_code_text = payload.reason_code_text

            if "focus" in provided or "focus_display" in provided:
                foc_ref = payload.focus
                foc_type, foc_id = (
                    _parse_generic_ref(foc_ref) if foc_ref else (None, None)
                )
                if foc_type and foc_id:
                    await _validate_ref(session, org_id, foc_type, foc_id, "focus")
                model.focus_reference = foc_ref
                model.focus_type = foc_type
                model.focus_id = foc_id
                model.focus_display = payload.focus_display

            if "for_" in provided or "for" in provided or "for_display" in provided:
                for_ref = payload.for_
                for_type, for_id = (
                    _parse_generic_ref(for_ref) if for_ref else (None, None)
                )
                if for_type and for_id:
                    await _validate_ref(session, org_id, for_type, for_id, "for")
                model.for_reference = for_ref
                model.for_type = for_type
                model.for_id = for_id
                model.for_display = payload.for_display

            if "encounter" in provided or "encounter_display" in provided:
                enc_ref = payload.encounter
                enc_type, enc_id = (
                    _parse_encounter_ref(enc_ref) if enc_ref else (None, None)
                )
                if enc_type and enc_id:
                    await _validate_ref(session, org_id, enc_type, enc_id, "encounter")
                model.encounter_reference = enc_ref
                model.encounter_type = enc_type
                model.encounter_id = enc_id
                model.encounter_display = payload.encounter_display

            if "execution_period_start" in provided:
                model.execution_period_start = payload.execution_period_start
            if "execution_period_end" in provided:
                model.execution_period_end = payload.execution_period_end

            if "requester" in provided or "requester_display" in provided:
                req_ref = payload.requester
                req_type, req_id = (
                    _parse_requester_ref(req_ref) if req_ref else (None, None)
                )
                if req_type and req_id:
                    await _validate_ref(session, org_id, req_type, req_id, "requester")
                model.requester_reference = req_ref
                model.requester_type = req_type
                model.requester_id = req_id
                model.requester_display = payload.requester_display

            if "owner" in provided or "owner_display" in provided:
                owner_ref = payload.owner
                owner_type, owner_id = (
                    _parse_owner_ref(owner_ref) if owner_ref else (None, None)
                )
                if owner_type and owner_id:
                    await _validate_ref(session, org_id, owner_type, owner_id, "owner")
                model.owner_reference = owner_ref
                model.owner_type = owner_type
                model.owner_id = owner_id
                model.owner_display = payload.owner_display

            if "location" in provided or "location_display" in provided:
                loc_ref = payload.location
                loc_type, loc_id = (
                    _parse_location_ref(loc_ref) if loc_ref else (None, None)
                )
                if loc_type and loc_id:
                    await _validate_ref(session, org_id, loc_type, loc_id, "location")
                model.location_reference = loc_ref
                model.location_type = loc_type
                model.location_id = loc_id
                model.location_display = payload.location_display

            if "reason_reference" in provided or "reason_reference_display" in provided:
                rr_ref = payload.reason_reference
                rr_type, rr_id = (
                    _parse_generic_ref(rr_ref) if rr_ref else (None, None)
                )
                if rr_type and rr_id:
                    await _validate_ref(
                        session, org_id, rr_type, rr_id, "reason_reference"
                    )
                model.reason_reference_reference = rr_ref
                model.reason_reference_type = rr_type
                model.reason_reference_id = rr_id
                model.reason_reference_display = payload.reason_reference_display

            # Group identifier fields
            for f in (
                "group_identifier_use",
                "group_identifier_system",
                "group_identifier_value",
                "group_identifier_period_start",
                "group_identifier_period_end",
                "group_identifier_assigner_display",
            ):
                if f in provided:
                    setattr(model, f, getattr(payload, f))

            if "group_identifier_assigner" in provided:
                grp_a_ref = payload.group_identifier_assigner
                grp_a_type, grp_a_id = (
                    _parse_assigner_ref(grp_a_ref) if grp_a_ref else (None, None)
                )
                if grp_a_type and grp_a_id:
                    await _validate_ref(
                        session, org_id, grp_a_type, grp_a_id, "group_identifier.assigner"
                    )
                model.group_identifier_assigner_reference = grp_a_ref
                model.group_identifier_assigner_type = grp_a_type
                model.group_identifier_assigner_id = grp_a_id

            if "restriction" in provided:
                if payload.restriction is not None:
                    model.restriction_repetitions = payload.restriction.repetitions
                    model.restriction_period_start = payload.restriction.period_start
                    model.restriction_period_end = payload.restriction.period_end
                    # Replace recipients
                    await session.execute(
                        delete(TaskRestrictionRecipient).where(
                            TaskRestrictionRecipient.task_pk == model.id
                        )
                    )
                    if payload.restriction.recipient:
                        await _add_restriction_recipients(
                            session,
                            model.id,
                            org_id,
                            payload.restriction.recipient,
                            updated_by,
                        )
                else:
                    model.restriction_repetitions = None
                    model.restriction_period_start = None
                    model.restriction_period_end = None
                    await session.execute(
                        delete(TaskRestrictionRecipient).where(
                            TaskRestrictionRecipient.task_pk == model.id
                        )
                    )

            model.updated_by = updated_by

            # Child collections replacement
            if "identifier" in provided:
                await session.execute(
                    delete(TaskIdentifierTypeCoding).where(
                        TaskIdentifierTypeCoding.task_identifier_id.in_(
                            select(TaskIdentifier.id).where(
                                TaskIdentifier.task_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(TaskIdentifier).where(
                        TaskIdentifier.task_pk == model.id
                    )
                )
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, updated_by
                )

            if "code_coding" in provided:
                await session.execute(
                    delete(TaskCodeCoding).where(
                        TaskCodeCoding.task_pk == model.id
                    )
                )
                _add_codings(
                    session, TaskCodeCoding, model.id, org_id, payload.code_coding, updated_by
                )

            if "status_reason_coding" in provided:
                await session.execute(
                    delete(TaskStatusReasonCoding).where(
                        TaskStatusReasonCoding.task_pk == model.id
                    )
                )
                _add_codings(
                    session,
                    TaskStatusReasonCoding,
                    model.id,
                    org_id,
                    payload.status_reason_coding,
                    updated_by,
                )

            if "business_status_coding" in provided:
                await session.execute(
                    delete(TaskBusinessStatusCoding).where(
                        TaskBusinessStatusCoding.task_pk == model.id
                    )
                )
                _add_codings(
                    session,
                    TaskBusinessStatusCoding,
                    model.id,
                    org_id,
                    payload.business_status_coding,
                    updated_by,
                )

            if "reason_code_coding" in provided:
                await session.execute(
                    delete(TaskReasonCodeCoding).where(
                        TaskReasonCodeCoding.task_pk == model.id
                    )
                )
                _add_codings(
                    session,
                    TaskReasonCodeCoding,
                    model.id,
                    org_id,
                    payload.reason_code_coding,
                    updated_by,
                )

            if "based_on" in provided:
                await session.execute(
                    delete(TaskBasedOn).where(TaskBasedOn.task_pk == model.id)
                )
                await _add_based_on(
                    session, model.id, org_id, payload.based_on, updated_by
                )

            if "part_of" in provided:
                await session.execute(
                    delete(TaskPartOf).where(TaskPartOf.task_pk == model.id)
                )
                await _add_part_of(
                    session, model.id, org_id, payload.part_of, updated_by
                )

            if "insurance" in provided:
                await session.execute(
                    delete(TaskInsurance).where(TaskInsurance.task_pk == model.id)
                )
                await _add_insurance(
                    session, model.id, org_id, payload.insurance, updated_by
                )

            if "relevant_history" in provided:
                await session.execute(
                    delete(TaskRelevantHistory).where(
                        TaskRelevantHistory.task_pk == model.id
                    )
                )
                await _add_relevant_history(
                    session, model.id, org_id, payload.relevant_history, updated_by
                )

            if "performer_type" in provided:
                await session.execute(
                    delete(TaskPerformerTypeCoding).where(
                        TaskPerformerTypeCoding.task_performer_type_id.in_(
                            select(TaskPerformerType.id).where(
                                TaskPerformerType.task_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(TaskPerformerType).where(
                        TaskPerformerType.task_pk == model.id
                    )
                )
                await _add_performer_types(
                    session, model.id, org_id, payload.performer_type, updated_by
                )

            if "note" in provided:
                await session.execute(
                    delete(TaskNote).where(TaskNote.task_pk == model.id)
                )
                _add_notes(session, model.id, org_id, payload.note, updated_by)

            if "input" in provided:
                await session.execute(
                    delete(TaskInputTypeCoding).where(
                        TaskInputTypeCoding.task_input_id.in_(
                            select(TaskInput.id).where(
                                TaskInput.task_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(TaskInput).where(TaskInput.task_pk == model.id)
                )
                await _add_inputs(
                    session, model.id, org_id, payload.input, updated_by
                )

            if "output" in provided:
                await session.execute(
                    delete(TaskOutputTypeCoding).where(
                        TaskOutputTypeCoding.task_output_id.in_(
                            select(TaskOutput.id).where(
                                TaskOutput.task_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(TaskOutput).where(TaskOutput.task_pk == model.id)
                )
                await _add_outputs(
                    session, model.id, org_id, payload.output, updated_by
                )

            await session.commit()

            stmt = _with_relationships(
                select(TaskModel).where(TaskModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def list(
        self,
        org_id: str,
        status: str | None = None,
        intent: str | None = None,
        priority: str | None = None,
        focus: str | None = None,
        for_: str | None = None,
        owner: str | None = None,
        requester: str | None = None,
        encounter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[TaskModel], int]:
        async with self.session_factory() as session:
            stmt = select(TaskModel).where(TaskModel.tenant_id == org_id)

            if status:
                stmt = stmt.where(TaskModel.status == status)

            if intent:
                stmt = stmt.where(TaskModel.intent == intent)

            if priority:
                stmt = stmt.where(TaskModel.priority == priority)

            if focus:
                foc_type, foc_id = _parse_generic_ref(focus)
                if foc_id is not None:
                    stmt = stmt.where(
                        TaskModel.focus_type == foc_type,
                        TaskModel.focus_id == foc_id,
                    )
                else:
                    stmt = stmt.where(TaskModel.focus_reference == focus)

            if for_:
                for_type, for_id = _parse_generic_ref(for_)
                if for_id is not None:
                    stmt = stmt.where(
                        TaskModel.for_type == for_type,
                        TaskModel.for_id == for_id,
                    )
                else:
                    stmt = stmt.where(TaskModel.for_reference == for_)

            if owner:
                owner_type, owner_id = _parse_owner_ref(owner)
                if owner_id is not None:
                    stmt = stmt.where(
                        TaskModel.owner_type == owner_type,
                        TaskModel.owner_id == owner_id,
                    )
                else:
                    stmt = stmt.where(TaskModel.owner_reference == owner)

            if requester:
                req_type, req_id = _parse_requester_ref(requester)
                if req_id is not None:
                    stmt = stmt.where(
                        TaskModel.requester_type == req_type,
                        TaskModel.requester_id == req_id,
                    )
                else:
                    stmt = stmt.where(TaskModel.requester_reference == requester)

            if encounter:
                enc_type, enc_id = _parse_encounter_ref(encounter)
                if enc_id is not None:
                    stmt = stmt.where(
                        TaskModel.encounter_type == enc_type,
                        TaskModel.encounter_id == enc_id,
                    )
                else:
                    stmt = stmt.where(TaskModel.encounter_reference == encounter)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await session.execute(count_stmt)).scalar() or 0

            sort_col, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, TaskModel.id, default_desc=True
            )
            data_stmt = (
                _with_relationships(stmt)
                .order_by(sort_col.desc() if sort_desc else sort_col.asc())
                .limit(limit)
                .offset(offset)
            )
            items = list((await session.execute(data_stmt)).scalars().all())
            return items, total

    async def delete(self, task_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(TaskModel).where(
                TaskModel.task_id == task_id,
                TaskModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True

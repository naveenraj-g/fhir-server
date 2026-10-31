from sqlalchemy import delete, func, select

from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.goal import (
    GoalAchievementStatusCoding,
    GoalAddresses,
    GoalCategory,
    GoalCategoryCoding,
    GoalDescriptionCoding,
    GoalIdentifier,
    GoalIdentifierTypeCoding,
    GoalModel,
    GoalNote,
    GoalOutcomeCode,
    GoalOutcomeCodeCoding,
    GoalOutcomeReference,
    GoalPriorityCoding,
    GoalStartCoding,
    GoalTarget,
    GoalTargetDetailCoding,
    GoalTargetMeasureCoding,
)
from app.schemas.goal import GoalCreateSchema, GoalPatchSchema

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_assigner_ref,
    _parse_expressed_by_ref,
    _parse_generic_ref,
    _parse_outcome_ref,
    _parse_subject_ref,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    if isinstance(coding, dict):
        return {
            "tenant_id": org_id,
            "system": coding.get("system"),
            "version": coding.get("version"),
            "code": coding.get("code"),
            "display": coding.get("display"),
            "user_selected": coding.get("user_selected") or coding.get("userSelected"),
            "created_by": created_by,
        }
    return {
        "tenant_id": org_id,
        "system": getattr(coding, "system", None),
        "version": getattr(coding, "version", None),
        "code": getattr(coding, "code", None),
        "display": getattr(coding, "display", None),
        "user_selected": getattr(coding, "user_selected", None),
        "created_by": created_by,
    }


async def _add_identifiers(
    session, goal_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = GoalIdentifier(
            goal_pk=goal_pk,
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
                GoalIdentifierTypeCoding(
                    goal_identifier_id=ident.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_codings(session, model_cls, goal_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            model_cls(
                goal_pk=goal_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_categories(
    session, goal_pk: int, org_id: str, categories, created_by: str
) -> None:
    for c in categories or []:
        cat = GoalCategory(
            goal_pk=goal_pk,
            tenant_id=org_id,
            text=c.text,
            created_by=created_by,
        )
        session.add(cat)
        await session.flush()

        for coding in c.coding or []:
            session.add(
                GoalCategoryCoding(
                    goal_category_id=cat.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


async def _add_outcome_codes(
    session, goal_pk: int, org_id: str, outcome_codes, created_by: str
) -> None:
    for oc in outcome_codes or []:
        code_row = GoalOutcomeCode(
            goal_pk=goal_pk,
            tenant_id=org_id,
            text=oc.text,
            created_by=created_by,
        )
        session.add(code_row)
        await session.flush()

        for coding in oc.coding or []:
            session.add(
                GoalOutcomeCodeCoding(
                    goal_outcome_code_id=code_row.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


async def _add_targets(
    session, goal_pk: int, org_id: str, targets, created_by: str
) -> None:
    for t in targets or []:
        target = GoalTarget(
            goal_pk=goal_pk,
            tenant_id=org_id,
            created_by=created_by,
            measure_text=t.measure_text,
            detail_string=t.detail_string,
            detail_boolean=t.detail_boolean,
            detail_integer=t.detail_integer,
            detail_quantity_value=t.detail_quantity_value,
            detail_quantity_unit=t.detail_quantity_unit,
            detail_quantity_system=t.detail_quantity_system,
            detail_quantity_code=t.detail_quantity_code,
            detail_quantity_comparator=t.detail_quantity_comparator,
            detail_range_low_value=t.detail_range_low_value,
            detail_range_low_unit=t.detail_range_low_unit,
            detail_range_low_system=t.detail_range_low_system,
            detail_range_low_code=t.detail_range_low_code,
            detail_range_high_value=t.detail_range_high_value,
            detail_range_high_unit=t.detail_range_high_unit,
            detail_range_high_system=t.detail_range_high_system,
            detail_range_high_code=t.detail_range_high_code,
            detail_ratio_numerator_value=t.detail_ratio_numerator_value,
            detail_ratio_numerator_unit=t.detail_ratio_numerator_unit,
            detail_ratio_numerator_system=t.detail_ratio_numerator_system,
            detail_ratio_numerator_code=t.detail_ratio_numerator_code,
            detail_ratio_denominator_value=t.detail_ratio_denominator_value,
            detail_ratio_denominator_unit=t.detail_ratio_denominator_unit,
            detail_ratio_denominator_system=t.detail_ratio_denominator_system,
            detail_ratio_denominator_code=t.detail_ratio_denominator_code,
            detail_codeable_concept_text=t.detail_codeable_concept_text,
            due_date=t.due_date,
            due_duration_value=t.due_duration_value,
            due_duration_unit=t.due_duration_unit,
            due_duration_system=t.due_duration_system,
            due_duration_code=t.due_duration_code,
        )
        session.add(target)
        await session.flush()

        for c in t.measure_coding or []:
            session.add(
                GoalTargetMeasureCoding(
                    goal_target_id=target.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )

        for c in t.detail_codeable_concept_coding or []:
            session.add(
                GoalTargetDetailCoding(
                    goal_target_id=target.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_addresses(
    session, goal_pk: int, org_id: str, addresses, created_by: str
) -> None:
    for a in addresses or []:
        ref_str = a if isinstance(a, str) else (a.reference if a else None)
        disp = None if isinstance(a, str) else (a.display if a else None)
        r_type, r_id = _parse_generic_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "addresses")
        session.add(
            GoalAddresses(
                goal_pk=goal_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
                created_by=created_by,
            )
        )


async def _add_outcome_references(
    session, goal_pk: int, org_id: str, outcome_references, created_by: str
) -> None:
    for o in outcome_references or []:
        ref_str = o if isinstance(o, str) else (o.reference if o else None)
        disp = None if isinstance(o, str) else (o.display if o else None)
        r_type, r_id = _parse_outcome_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "outcomeReference")
        session.add(
            GoalOutcomeReference(
                goal_pk=goal_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
                created_by=created_by,
            )
        )


async def _add_notes(
    session, goal_pk: int, org_id: str, notes, created_by: str
) -> None:
    for n in notes or []:
        if isinstance(n, str):
            session.add(
                GoalNote(
                    goal_pk=goal_pk,
                    tenant_id=org_id,
                    text=n,
                    created_by=created_by,
                )
            )
        else:
            auth_type, auth_id = (
                _parse_generic_ref(n.author_reference)
                if n.author_reference
                else (None, None)
            )
            if auth_type and auth_id:
                await _validate_ref(
                    session, org_id, auth_type, auth_id, "note.author"
                )
            session.add(
                GoalNote(
                    goal_pk=goal_pk,
                    tenant_id=org_id,
                    author_string=n.author_string,
                    author_reference=n.author_reference,
                    author_type=auth_type,
                    author_id=auth_id,
                    author_display=n.author_display,
                    time=n.time,
                    text=n.text,
                    created_by=created_by,
                )
            )


class GoalRepository:
    """Repository handling all Goal persistence."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_goal_id(self, goal_id: int) -> GoalModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(GoalModel).where(GoalModel.goal_id == goal_id)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_goal_id_in_org(
        self, goal_id: int, org_id: str
    ) -> GoalModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(GoalModel).where(
                    GoalModel.goal_id == goal_id,
                    GoalModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def goal_belongs_to_org(self, goal_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(func.count()).select_from(GoalModel).where(
                GoalModel.goal_id == goal_id,
                GoalModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            return bool(res.scalar() or 0)

    async def create_full(
        self, payload: GoalCreateSchema, org_id: str, created_by: str
    ) -> GoalModel:
        async with self.session_factory() as session:
            # Validate subject
            sub_type, sub_id = _parse_subject_ref(payload.subject)
            if sub_type and sub_id:
                await _validate_ref(session, org_id, sub_type, sub_id, "subject")

            # Validate expressedBy
            exp_type, exp_id = (
                _parse_expressed_by_ref(payload.expressed_by)
                if payload.expressed_by
                else (None, None)
            )
            if exp_type and exp_id:
                await _validate_ref(
                    session, org_id, exp_type, exp_id, "expressedBy"
                )

            model = GoalModel(
                tenant_id=org_id,
                created_by=created_by,
                lifecycle_status=payload.lifecycle_status,
                achievement_status_text=payload.achievement_status_text,
                priority_text=payload.priority_text,
                description_text=payload.description_text,
                subject_reference=payload.subject,
                subject_type=sub_type,
                subject_id=sub_id,
                subject_display=payload.subject_display,
                start_date=payload.start_date,
                start_codeable_concept_text=payload.start_codeable_concept_text,
                status_date=payload.status_date,
                status_reason=payload.status_reason,
                expressed_by_reference=payload.expressed_by,
                expressed_by_type=exp_type,
                expressed_by_id=exp_id,
                expressed_by_display=payload.expressed_by_display,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            # Add child tables
            if payload.identifier:
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, created_by
                )
            if payload.achievement_status_coding:
                _add_codings(
                    session,
                    GoalAchievementStatusCoding,
                    model.id,
                    org_id,
                    payload.achievement_status_coding,
                    created_by,
                )
            if payload.category:
                await _add_categories(
                    session, model.id, org_id, payload.category, created_by
                )
            if payload.priority_coding:
                _add_codings(
                    session,
                    GoalPriorityCoding,
                    model.id,
                    org_id,
                    payload.priority_coding,
                    created_by,
                )
            if payload.description_coding:
                _add_codings(
                    session,
                    GoalDescriptionCoding,
                    model.id,
                    org_id,
                    payload.description_coding,
                    created_by,
                )
            if payload.start_codeable_concept_coding:
                _add_codings(
                    session,
                    GoalStartCoding,
                    model.id,
                    org_id,
                    payload.start_codeable_concept_coding,
                    created_by,
                )
            if payload.target:
                await _add_targets(
                    session, model.id, org_id, payload.target, created_by
                )
            if payload.addresses:
                await _add_addresses(
                    session, model.id, org_id, payload.addresses, created_by
                )
            if payload.note:
                await _add_notes(
                    session, model.id, org_id, payload.note, created_by
                )
            if payload.outcome_code:
                await _add_outcome_codes(
                    session, model.id, org_id, payload.outcome_code, created_by
                )
            if payload.outcome_reference:
                await _add_outcome_references(
                    session, model.id, org_id, payload.outcome_reference, created_by
                )

            await session.commit()
            return await self.get_by_goal_id(model.goal_id)

    async def patch_full(
        self,
        goal_id: int,
        payload: GoalPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> GoalModel:
        async with self.session_factory() as session:
            stmt = select(GoalModel).where(
                GoalModel.goal_id == goal_id,
                GoalModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                raise ValueError(f"Goal {goal_id} not found in org {org_id}")

            provided = payload.model_fields_set

            if "lifecycle_status" in provided:
                model.lifecycle_status = payload.lifecycle_status
            if "achievement_status_text" in provided:
                model.achievement_status_text = payload.achievement_status_text
            if "priority_text" in provided:
                model.priority_text = payload.priority_text
            if "description_text" in provided:
                model.description_text = payload.description_text
            if "start_date" in provided:
                model.start_date = payload.start_date
            if "start_codeable_concept_text" in provided:
                model.start_codeable_concept_text = payload.start_codeable_concept_text
            if "status_date" in provided:
                model.status_date = payload.status_date
            if "status_reason" in provided:
                model.status_reason = payload.status_reason
            if "extension" in provided:
                model.extension = payload.extension or []

            if "subject" in provided or "subject_display" in provided:
                sub_ref = payload.subject or model.subject_reference
                sub_type, sub_id = _parse_subject_ref(sub_ref)
                if sub_type and sub_id:
                    await _validate_ref(session, org_id, sub_type, sub_id, "subject")
                model.subject_reference = sub_ref
                model.subject_type = sub_type
                model.subject_id = sub_id
                if "subject_display" in provided:
                    model.subject_display = payload.subject_display

            if "expressed_by" in provided or "expressed_by_display" in provided:
                exp_ref = payload.expressed_by
                exp_type, exp_id = (
                    _parse_expressed_by_ref(exp_ref) if exp_ref else (None, None)
                )
                if exp_type and exp_id:
                    await _validate_ref(
                        session, org_id, exp_type, exp_id, "expressedBy"
                    )
                model.expressed_by_reference = exp_ref
                model.expressed_by_type = exp_type
                model.expressed_by_id = exp_id
                if "expressed_by_display" in provided:
                    model.expressed_by_display = payload.expressed_by_display

            model.updated_by = updated_by

            # Replace child tables when provided in patch
            if "identifier" in provided:
                await session.execute(
                    delete(GoalIdentifier).where(GoalIdentifier.goal_pk == model.id)
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, model.id, org_id, payload.identifier, updated_by
                    )

            if "achievement_status_coding" in provided:
                await session.execute(
                    delete(GoalAchievementStatusCoding).where(
                        GoalAchievementStatusCoding.goal_pk == model.id
                    )
                )
                if payload.achievement_status_coding:
                    _add_codings(
                        session,
                        GoalAchievementStatusCoding,
                        model.id,
                        org_id,
                        payload.achievement_status_coding,
                        updated_by,
                    )

            if "category" in provided:
                await session.execute(
                    delete(GoalCategory).where(GoalCategory.goal_pk == model.id)
                )
                if payload.category:
                    await _add_categories(
                        session, model.id, org_id, payload.category, updated_by
                    )

            if "priority_coding" in provided:
                await session.execute(
                    delete(GoalPriorityCoding).where(
                        GoalPriorityCoding.goal_pk == model.id
                    )
                )
                if payload.priority_coding:
                    _add_codings(
                        session,
                        GoalPriorityCoding,
                        model.id,
                        org_id,
                        payload.priority_coding,
                        updated_by,
                    )

            if "description_coding" in provided:
                await session.execute(
                    delete(GoalDescriptionCoding).where(
                        GoalDescriptionCoding.goal_pk == model.id
                    )
                )
                if payload.description_coding:
                    _add_codings(
                        session,
                        GoalDescriptionCoding,
                        model.id,
                        org_id,
                        payload.description_coding,
                        updated_by,
                    )

            if "start_codeable_concept_coding" in provided:
                await session.execute(
                    delete(GoalStartCoding).where(
                        GoalStartCoding.goal_pk == model.id
                    )
                )
                if payload.start_codeable_concept_coding:
                    _add_codings(
                        session,
                        GoalStartCoding,
                        model.id,
                        org_id,
                        payload.start_codeable_concept_coding,
                        updated_by,
                    )

            if "target" in provided:
                await session.execute(
                    delete(GoalTarget).where(GoalTarget.goal_pk == model.id)
                )
                if payload.target:
                    await _add_targets(
                        session, model.id, org_id, payload.target, updated_by
                    )

            if "addresses" in provided:
                await session.execute(
                    delete(GoalAddresses).where(GoalAddresses.goal_pk == model.id)
                )
                if payload.addresses:
                    await _add_addresses(
                        session, model.id, org_id, payload.addresses, updated_by
                    )

            if "note" in provided:
                await session.execute(
                    delete(GoalNote).where(GoalNote.goal_pk == model.id)
                )
                if payload.note:
                    await _add_notes(
                        session, model.id, org_id, payload.note, updated_by
                    )

            if "outcome_code" in provided:
                await session.execute(
                    delete(GoalOutcomeCode).where(GoalOutcomeCode.goal_pk == model.id)
                )
                if payload.outcome_code:
                    await _add_outcome_codes(
                        session, model.id, org_id, payload.outcome_code, updated_by
                    )

            if "outcome_reference" in provided:
                await session.execute(
                    delete(GoalOutcomeReference).where(
                        GoalOutcomeReference.goal_pk == model.id
                    )
                )
                if payload.outcome_reference:
                    await _add_outcome_references(
                        session, model.id, org_id, payload.outcome_reference, updated_by
                    )

            await session.commit()
            return await self.get_by_goal_id(model.goal_id)

    async def list(
        self,
        org_id: str,
        subject: str | None = None,
        lifecycle_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[GoalModel], int]:
        async with self.session_factory() as session:
            stmt = select(GoalModel).where(GoalModel.tenant_id == org_id)

            if subject:
                s_type, s_id = _parse_subject_ref(subject)
                if s_type and s_id:
                    stmt = stmt.where(
                        GoalModel.subject_type == s_type,
                        GoalModel.subject_id == s_id,
                    )
                else:
                    stmt = stmt.where(GoalModel.subject_reference == subject)

            if lifecycle_status:
                stmt = stmt.where(GoalModel.lifecycle_status == lifecycle_status)

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_res = await session.execute(count_stmt)
            total = total_res.scalar() or 0

            # Sorting
            sort_col, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, GoalModel.goal_id, default_desc=True
            )
            stmt = stmt.order_by(sort_col.desc() if sort_desc else sort_col.asc()).limit(limit).offset(offset)
            stmt = _with_relationships(stmt)

            res = await session.execute(stmt)
            items = list(res.scalars().all())
            return items, total

    async def delete(self, goal_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = delete(GoalModel).where(
                GoalModel.goal_id == goal_id,
                GoalModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            await session.commit()
            return (res.rowcount or 0) > 0

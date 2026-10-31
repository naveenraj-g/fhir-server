from typing import Any

from sqlalchemy import delete, select, update

from app.models.enums import IdentifierUse
from app.schemas.enums import ContactPointSystem, ContactPointUse
from app.models.plan_definition import (
    PlanDefinitionAction,
    PlanDefinitionActionCardinalityBehavior,
    PlanDefinitionActionGroupingBehavior,
    PlanDefinitionActionPrecheckBehavior,
    PlanDefinitionActionPriority,
    PlanDefinitionActionRequiredBehavior,
    PlanDefinitionActionSelectionBehavior,
    PlanDefinitionActionTypeCoding,
    PlanDefinitionContact,
    PlanDefinitionContactRole,
    PlanDefinitionContactTelecom,
    PlanDefinitionGoal,
    PlanDefinitionGoalCategoryCoding,
    PlanDefinitionGoalDescriptionCoding,
    PlanDefinitionGoalPriorityCoding,
    PlanDefinitionGoalStartCoding,
    PlanDefinitionIdentifier,
    PlanDefinitionIdentifierTypeCoding,
    PlanDefinitionJurisdiction,
    PlanDefinitionJurisdictionCoding,
    PlanDefinitionModel,
    PlanDefinitionQuantityComparator,
    PlanDefinitionRelatedArtifact,
    PlanDefinitionRelatedArtifactType,
    PlanDefinitionStatus,
    PlanDefinitionSubjectCoding,
    PlanDefinitionTopic,
    PlanDefinitionTopicCoding,
    PlanDefinitionTypeCoding,
    PlanDefinitionUseContext,
    PlanDefinitionUseContextValueCoding,
)
from app.repository.plan_definition._shared import (
    _parse_assigner_ref,
    _parse_subject_ref,
    _parse_use_context_value_ref,
    _validate_ref,
    _with_relationships,
)


def _coding_kwargs(c, org_id: str, created_by: str) -> dict:
    if isinstance(c, dict):
        return {
            "tenant_id": org_id,
            "system": c.get("system"),
            "version": c.get("version"),
            "code": c.get("code"),
            "display": c.get("display"),
            "user_selected": c.get("user_selected") or c.get("userSelected"),
            "created_by": created_by,
        }
    return {
        "tenant_id": org_id,
        "system": getattr(c, "system", None),
        "version": getattr(c, "version", None),
        "code": getattr(c, "code", None),
        "display": getattr(c, "display", None),
        "user_selected": getattr(c, "user_selected", None),
        "created_by": created_by,
    }


async def _add_identifiers(
    session, plan_definition_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = PlanDefinitionIdentifier(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            use=(
                IdentifierUse(i.use.value)
                if (i.use and hasattr(i.use, "value"))
                else IdentifierUse(i.use)
                if i.use
                else None
            ),
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

        if i.type_coding:
            for c in i.type_coding:
                session.add(
                    PlanDefinitionIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_contacts(
    session, plan_definition_pk: int, org_id: str, contacts, role: PlanDefinitionContactRole, created_by: str
) -> None:
    for c in contacts or []:
        contact_row = PlanDefinitionContact(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            role=role,
            name=c.name,
            created_by=created_by,
        )
        session.add(contact_row)
        await session.flush()

        if c.telecom:
            for t in c.telecom:
                t_sys = (
                    ContactPointSystem(t.system.value)
                    if (t.system and hasattr(t.system, "value"))
                    else ContactPointSystem(t.system)
                    if t.system
                    else None
                )
                t_use = (
                    ContactPointUse(t.use.value)
                    if (t.use and hasattr(t.use, "value"))
                    else ContactPointUse(t.use)
                    if t.use
                    else None
                )
                session.add(
                    PlanDefinitionContactTelecom(
                        plan_definition_contact_id=contact_row.id,
                        tenant_id=org_id,
                        system=t_sys,
                        value=t.value,
                        use=t_use,
                        rank=t.rank,
                        period_start=t.period_start,
                        period_end=t.period_end,
                        created_by=created_by,
                    )
                )


async def _add_use_contexts(
    session, plan_definition_pk: int, org_id: str, use_contexts, created_by: str
) -> None:
    for uc in use_contexts or []:
        val_ref_type, val_ref_id = (
            _parse_use_context_value_ref(uc.value_reference)
            if uc.value_reference
            else (None, None)
        )
        if val_ref_type and val_ref_id:
            await _validate_ref(
                session, org_id, val_ref_type, val_ref_id, "use_context.value_reference"
            )

        q_comp = (
            PlanDefinitionQuantityComparator(uc.value_quantity_comparator.value)
            if (uc.value_quantity_comparator and hasattr(uc.value_quantity_comparator, "value"))
            else PlanDefinitionQuantityComparator(uc.value_quantity_comparator)
            if uc.value_quantity_comparator
            else None
        )

        vcc_text = uc.value_codeable_concept_text

        uc_row = PlanDefinitionUseContext(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            system=uc.code_system,
            version=uc.code_version,
            code=uc.code_code,
            display=uc.code_display,
            user_selected=uc.code_user_selected,
            value_codeable_concept_text=vcc_text,
            value_quantity_value=uc.value_quantity_value,
            value_quantity_comparator=q_comp,
            value_quantity_unit=uc.value_quantity_unit,
            value_quantity_system=uc.value_quantity_system,
            value_quantity_code=uc.value_quantity_code,
            value_range_low_value=uc.value_range_low_value,
            value_range_low_unit=uc.value_range_low_unit,
            value_range_low_system=uc.value_range_low_system,
            value_range_low_code=uc.value_range_low_code,
            value_range_high_value=uc.value_range_high_value,
            value_range_high_unit=uc.value_range_high_unit,
            value_range_high_system=uc.value_range_high_system,
            value_range_high_code=uc.value_range_high_code,
            value_reference_reference=uc.value_reference,
            value_reference_type=val_ref_type,
            value_reference_id=val_ref_id,
            value_reference_display=uc.value_reference_display,
            created_by=created_by,
        )
        session.add(uc_row)
        await session.flush()

        if uc.value_codeable_concept_coding:
            for c in uc.value_codeable_concept_coding:
                session.add(
                    PlanDefinitionUseContextValueCoding(
                        plan_definition_use_context_id=uc_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_jurisdictions(
    session, plan_definition_pk: int, org_id: str, jurisdictions, created_by: str
) -> None:
    for j in jurisdictions or []:
        j_row = PlanDefinitionJurisdiction(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            text=j.text,
            created_by=created_by,
        )
        session.add(j_row)
        await session.flush()
        if j.coding:
            for c in j.coding:
                session.add(
                    PlanDefinitionJurisdictionCoding(
                        plan_definition_jurisdiction_id=j_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_topics(
    session, plan_definition_pk: int, org_id: str, topics, created_by: str
) -> None:
    for t in topics or []:
        t_row = PlanDefinitionTopic(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            text=t.text,
            created_by=created_by,
        )
        session.add(t_row)
        await session.flush()
        if t.coding:
            for c in t.coding:
                session.add(
                    PlanDefinitionTopicCoding(
                        plan_definition_topic_id=t_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_type_codings(
    session, plan_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            PlanDefinitionTypeCoding(
                plan_definition_pk=plan_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_subject_codings(
    session, plan_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            PlanDefinitionSubjectCoding(
                plan_definition_pk=plan_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_related_artifacts(
    session, plan_definition_pk: int, org_id: str, artifacts, created_by: str
) -> None:
    for ra in artifacts or []:
        ra_type = (
            PlanDefinitionRelatedArtifactType(ra.type.value)
            if (ra.type and hasattr(ra.type, "value"))
            else PlanDefinitionRelatedArtifactType(ra.type)
            if ra.type
            else None
        )
        session.add(
            PlanDefinitionRelatedArtifact(
                plan_definition_pk=plan_definition_pk,
                tenant_id=org_id,
                type=ra_type,
                label=ra.label,
                display=ra.display,
                citation=ra.citation,
                url=ra.url,
                document=ra.document,
                resource=ra.resource,
                created_by=created_by,
            )
        )


async def _add_goals(
    session, plan_definition_pk: int, org_id: str, goals, created_by: str
) -> None:
    for g in goals or []:
        goal_row = PlanDefinitionGoal(
            plan_definition_pk=plan_definition_pk,
            tenant_id=org_id,
            goal_id=g.id or g.goal_id,
            category_text=g.category.text if g.category else None,
            description_text=g.description.text if g.description else None,
            priority_text=g.priority.text if g.priority else None,
            start_text=g.start.text if g.start else None,
            addresses=[
                a.model_dump(exclude_unset=True) if hasattr(a, "model_dump") else a
                for a in g.addresses
            ]
            if g.addresses
            else None,
            documentation=g.documentation,
            target=g.target,
            created_by=created_by,
        )
        session.add(goal_row)
        await session.flush()

        if g.category and g.category.coding:
            for c in g.category.coding:
                session.add(
                    PlanDefinitionGoalCategoryCoding(
                        goal_id=goal_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if g.description and g.description.coding:
            for c in g.description.coding:
                session.add(
                    PlanDefinitionGoalDescriptionCoding(
                        goal_id=goal_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if g.priority and g.priority.coding:
            for c in g.priority.coding:
                session.add(
                    PlanDefinitionGoalPriorityCoding(
                        goal_id=goal_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if g.start and g.start.coding:
            for c in g.start.coding:
                session.add(
                    PlanDefinitionGoalStartCoding(
                        goal_id=goal_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_actions(
    session,
    plan_definition_pk: int,
    org_id: str,
    actions,
    created_by: str,
    parent_action_id: int | None = None,
) -> None:
    for act in actions or []:
        sub_type, sub_id = (
            _parse_subject_ref(act.subject_reference)
            if act.subject_reference
            else (None, None)
        )
        if sub_type and sub_id:
            await _validate_ref(
                session, org_id, sub_type, sub_id, "action.subject_reference"
            )

        prio = (
            PlanDefinitionActionPriority(act.priority.value)
            if (act.priority and hasattr(act.priority, "value"))
            else PlanDefinitionActionPriority(act.priority)
            if act.priority
            else None
        )
        grp = (
            PlanDefinitionActionGroupingBehavior(act.grouping_behavior.value)
            if (act.grouping_behavior and hasattr(act.grouping_behavior, "value"))
            else PlanDefinitionActionGroupingBehavior(act.grouping_behavior)
            if act.grouping_behavior
            else None
        )
        sel = (
            PlanDefinitionActionSelectionBehavior(act.selection_behavior.value)
            if (act.selection_behavior and hasattr(act.selection_behavior, "value"))
            else PlanDefinitionActionSelectionBehavior(act.selection_behavior)
            if act.selection_behavior
            else None
        )
        req = (
            PlanDefinitionActionRequiredBehavior(act.required_behavior.value)
            if (act.required_behavior and hasattr(act.required_behavior, "value"))
            else PlanDefinitionActionRequiredBehavior(act.required_behavior)
            if act.required_behavior
            else None
        )
        pre = (
            PlanDefinitionActionPrecheckBehavior(act.precheck_behavior.value)
            if (act.precheck_behavior and hasattr(act.precheck_behavior, "value"))
            else PlanDefinitionActionPrecheckBehavior(act.precheck_behavior)
            if act.precheck_behavior
            else None
        )
        card = (
            PlanDefinitionActionCardinalityBehavior(act.cardinality_behavior.value)
            if (act.cardinality_behavior and hasattr(act.cardinality_behavior, "value"))
            else PlanDefinitionActionCardinalityBehavior(act.cardinality_behavior)
            if act.cardinality_behavior
            else None
        )

        sub_text = (
            act.subject_codeable_concept.text
            if act.subject_codeable_concept
            else None
        )
        type_text = act.type.text if act.type else None

        action_row = PlanDefinitionAction(
            plan_definition_pk=plan_definition_pk,
            parent_action_id=parent_action_id,
            tenant_id=org_id,
            action_id_str=act.id or act.action_id_str,
            prefix=act.prefix,
            title=act.title,
            description=act.description,
            text_equivalent=act.text_equivalent,
            priority=prio,
            code=act.code,
            reason=act.reason,
            documentation=act.documentation,
            goal_id=act.goal_id,
            subject_codeable_concept_text=sub_text,
            subject_reference=act.subject_reference,
            subject_type=sub_type,
            subject_id=sub_id,
            subject_display=act.subject_display,
            trigger=act.trigger,
            condition=act.condition,
            input=act.input,
            output=act.output,
            related_action=act.related_action,
            timing_date_time=act.timing_date_time,
            timing_age=act.timing_age,
            timing_period_start=act.timing_period_start,
            timing_period_end=act.timing_period_end,
            timing_duration=act.timing_duration,
            timing_range=act.timing_range,
            timing_timing=act.timing_timing,
            participant=act.participant,
            type_text=type_text,
            grouping_behavior=grp,
            selection_behavior=sel,
            required_behavior=req,
            precheck_behavior=pre,
            cardinality_behavior=card,
            definition_canonical=act.definition_canonical,
            definition_uri=act.definition_uri,
            transform=act.transform,
            dynamic_value=act.dynamic_value,
            created_by=created_by,
        )
        session.add(action_row)
        await session.flush()

        if act.type and act.type.coding:
            for c in act.type.coding:
                session.add(
                    PlanDefinitionActionTypeCoding(
                        action_id=action_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if act.action:
            await _add_actions(
                session,
                plan_definition_pk,
                org_id,
                act.action,
                created_by,
                parent_action_id=action_row.id,
            )


async def create_full(session, payload, org_id: str, created_by: str) -> PlanDefinitionModel:
    sub_type, sub_id = (
        _parse_subject_ref(payload.subject_reference)
        if payload.subject_reference
        else (None, None)
    )
    if sub_type and sub_id:
        await _validate_ref(session, org_id, sub_type, sub_id, "subject_reference")

    status_val = (
        PlanDefinitionStatus(payload.status.value)
        if hasattr(payload.status, "value")
        else PlanDefinitionStatus(payload.status)
    )

    type_text = payload.type.text if payload.type else None
    sub_cc_text = (
        payload.subject_codeable_concept.text
        if payload.subject_codeable_concept
        else None
    )

    model = PlanDefinitionModel(
        tenant_id=org_id,
        created_by=created_by,
        url=payload.url,
        version=payload.version,
        name=payload.name,
        title=payload.title,
        subtitle=payload.subtitle,
        type_text=type_text,
        status=status_val,
        experimental=payload.experimental,
        subject_codeable_concept_text=sub_cc_text,
        subject_reference=payload.subject_reference,
        subject_type=sub_type,
        subject_id=sub_id,
        subject_display=payload.subject_display,
        date=payload.date,
        publisher=payload.publisher,
        description=payload.description,
        purpose=payload.purpose,
        usage=payload.usage,
        copyright=payload.copyright,
        approval_date=payload.approval_date,
        last_review_date=payload.last_review_date,
        effective_period_start=payload.effective_period_start,
        effective_period_end=payload.effective_period_end,
        library=payload.library,
        extension=payload.extension or [],
    )
    session.add(model)
    await session.flush()

    if payload.type and payload.type.coding:
        await _add_type_codings(session, model.id, org_id, payload.type.coding, created_by)
    if payload.subject_codeable_concept and payload.subject_codeable_concept.coding:
        await _add_subject_codings(session, model.id, org_id, payload.subject_codeable_concept.coding, created_by)

    if payload.identifier:
        await _add_identifiers(session, model.id, org_id, payload.identifier, created_by)
    if payload.contact:
        await _add_contacts(session, model.id, org_id, payload.contact, PlanDefinitionContactRole.contact, created_by)
    if payload.author:
        await _add_contacts(session, model.id, org_id, payload.author, PlanDefinitionContactRole.author, created_by)
    if payload.editor:
        await _add_contacts(session, model.id, org_id, payload.editor, PlanDefinitionContactRole.editor, created_by)
    if payload.reviewer:
        await _add_contacts(session, model.id, org_id, payload.reviewer, PlanDefinitionContactRole.reviewer, created_by)
    if payload.endorser:
        await _add_contacts(session, model.id, org_id, payload.endorser, PlanDefinitionContactRole.endorser, created_by)
    if payload.use_context:
        await _add_use_contexts(session, model.id, org_id, payload.use_context, created_by)
    if payload.jurisdiction:
        await _add_jurisdictions(session, model.id, org_id, payload.jurisdiction, created_by)
    if payload.topic:
        await _add_topics(session, model.id, org_id, payload.topic, created_by)
    if payload.related_artifact:
        await _add_related_artifacts(session, model.id, org_id, payload.related_artifact, created_by)
    if payload.goal:
        await _add_goals(session, model.id, org_id, payload.goal, created_by)
    if payload.action:
        await _add_actions(session, model.id, org_id, payload.action, created_by)

    await session.commit()

    stmt = select(PlanDefinitionModel).where(PlanDefinitionModel.id == model.id)
    stmt = _with_relationships(stmt)
    result = await session.execute(stmt)
    return result.scalar_one()


async def _apply_patch(
    session, model: PlanDefinitionModel, payload, org_id: str, updated_by: str
) -> PlanDefinitionModel:
    fields_set = payload.model_fields_set

    # Scalar updates
    scalar_fields = [
        "url", "version", "name", "title", "subtitle", "experimental",
        "date", "publisher", "description", "purpose", "usage", "copyright",
        "approval_date", "last_review_date", "effective_period_start",
        "effective_period_end", "library", "extension",
    ]
    for field in scalar_fields:
        if field in fields_set:
            setattr(model, field, getattr(payload, field))

    if "status" in fields_set and payload.status is not None:
        model.status = (
            PlanDefinitionStatus(payload.status.value)
            if hasattr(payload.status, "value")
            else PlanDefinitionStatus(payload.status)
        )

    if "type" in fields_set:
        await session.execute(
            delete(PlanDefinitionTypeCoding).where(
                PlanDefinitionTypeCoding.plan_definition_pk == model.id
            )
        )
        if payload.type is not None:
            model.type_text = payload.type.text
            if payload.type.coding:
                await _add_type_codings(session, model.id, org_id, payload.type.coding, updated_by)
        else:
            model.type_text = None

    if "subject_codeable_concept" in fields_set or "subject_reference" in fields_set:
        if "subject_codeable_concept" in fields_set:
            await session.execute(
                delete(PlanDefinitionSubjectCoding).where(
                    PlanDefinitionSubjectCoding.plan_definition_pk == model.id
                )
            )
            if payload.subject_codeable_concept is not None:
                model.subject_codeable_concept_text = payload.subject_codeable_concept.text
                if payload.subject_codeable_concept.coding:
                    await _add_subject_codings(
                        session, model.id, org_id, payload.subject_codeable_concept.coding, updated_by
                    )
            else:
                model.subject_codeable_concept_text = None

        if "subject_reference" in fields_set:
            if payload.subject_reference is not None:
                sub_type, sub_id = _parse_subject_ref(payload.subject_reference)
                if sub_type and sub_id:
                    await _validate_ref(session, org_id, sub_type, sub_id, "subject_reference")
                model.subject_reference = payload.subject_reference
                model.subject_type = sub_type
                model.subject_id = sub_id
                model.subject_display = payload.subject_display
            else:
                model.subject_reference = None
                model.subject_type = None
                model.subject_id = None
                model.subject_display = None

    # Sub-resources replacement
    if "identifier" in fields_set:
        id_sub = select(PlanDefinitionIdentifier.id).where(
            PlanDefinitionIdentifier.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionIdentifierTypeCoding).where(
                PlanDefinitionIdentifierTypeCoding.identifier_id.in_(id_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionIdentifier).where(
                PlanDefinitionIdentifier.plan_definition_pk == model.id
            )
        )
        if payload.identifier:
            await _add_identifiers(session, model.id, org_id, payload.identifier, updated_by)

    for role_attr, role_enum in [
        ("contact", PlanDefinitionContactRole.contact),
        ("author", PlanDefinitionContactRole.author),
        ("editor", PlanDefinitionContactRole.editor),
        ("reviewer", PlanDefinitionContactRole.reviewer),
        ("endorser", PlanDefinitionContactRole.endorser),
    ]:
        if role_attr in fields_set:
            c_sub = select(PlanDefinitionContact.id).where(
                PlanDefinitionContact.plan_definition_pk == model.id,
                PlanDefinitionContact.role == role_enum,
            )
            await session.execute(
                delete(PlanDefinitionContactTelecom).where(
                    PlanDefinitionContactTelecom.plan_definition_contact_id.in_(c_sub)
                )
            )
            await session.execute(
                delete(PlanDefinitionContact).where(
                    PlanDefinitionContact.plan_definition_pk == model.id,
                    PlanDefinitionContact.role == role_enum,
                )
            )
            items = getattr(payload, role_attr)
            if items:
                await _add_contacts(session, model.id, org_id, items, role_enum, updated_by)

    if "use_context" in fields_set:
        uc_sub = select(PlanDefinitionUseContext.id).where(
            PlanDefinitionUseContext.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionUseContextValueCoding).where(
                PlanDefinitionUseContextValueCoding.plan_definition_use_context_id.in_(uc_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionUseContext).where(
                PlanDefinitionUseContext.plan_definition_pk == model.id
            )
        )
        if payload.use_context:
            await _add_use_contexts(session, model.id, org_id, payload.use_context, updated_by)

    if "jurisdiction" in fields_set:
        j_sub = select(PlanDefinitionJurisdiction.id).where(
            PlanDefinitionJurisdiction.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionJurisdictionCoding).where(
                PlanDefinitionJurisdictionCoding.plan_definition_jurisdiction_id.in_(j_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionJurisdiction).where(
                PlanDefinitionJurisdiction.plan_definition_pk == model.id
            )
        )
        if payload.jurisdiction:
            await _add_jurisdictions(session, model.id, org_id, payload.jurisdiction, updated_by)

    if "topic" in fields_set:
        t_sub = select(PlanDefinitionTopic.id).where(
            PlanDefinitionTopic.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionTopicCoding).where(
                PlanDefinitionTopicCoding.plan_definition_topic_id.in_(t_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionTopic).where(
                PlanDefinitionTopic.plan_definition_pk == model.id
            )
        )
        if payload.topic:
            await _add_topics(session, model.id, org_id, payload.topic, updated_by)

    if "related_artifact" in fields_set:
        await session.execute(
            delete(PlanDefinitionRelatedArtifact).where(
                PlanDefinitionRelatedArtifact.plan_definition_pk == model.id
            )
        )
        if payload.related_artifact:
            await _add_related_artifacts(session, model.id, org_id, payload.related_artifact, updated_by)

    if "goal" in fields_set:
        g_sub = select(PlanDefinitionGoal.id).where(
            PlanDefinitionGoal.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionGoalCategoryCoding).where(
                PlanDefinitionGoalCategoryCoding.goal_id.in_(g_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionGoalDescriptionCoding).where(
                PlanDefinitionGoalDescriptionCoding.goal_id.in_(g_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionGoalPriorityCoding).where(
                PlanDefinitionGoalPriorityCoding.goal_id.in_(g_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionGoalStartCoding).where(
                PlanDefinitionGoalStartCoding.goal_id.in_(g_sub)
            )
        )
        await session.execute(
            delete(PlanDefinitionGoal).where(
                PlanDefinitionGoal.plan_definition_pk == model.id
            )
        )
        if payload.goal:
            await _add_goals(session, model.id, org_id, payload.goal, updated_by)

    if "action" in fields_set:
        act_sub = select(PlanDefinitionAction.id).where(
            PlanDefinitionAction.plan_definition_pk == model.id
        )
        await session.execute(
            delete(PlanDefinitionActionTypeCoding).where(
                PlanDefinitionActionTypeCoding.action_id.in_(act_sub)
            )
        )
        # Break recursive FK before bulk delete
        await session.execute(
            update(PlanDefinitionAction)
            .where(PlanDefinitionAction.plan_definition_pk == model.id)
            .values(parent_action_id=None)
        )
        await session.execute(
            delete(PlanDefinitionAction).where(
                PlanDefinitionAction.plan_definition_pk == model.id
            )
        )
        if payload.action:
            await _add_actions(session, model.id, org_id, payload.action, updated_by)

    model.updated_by = updated_by
    await session.commit()

    stmt = select(PlanDefinitionModel).where(PlanDefinitionModel.id == model.id)
    stmt = _with_relationships(stmt)
    result = await session.execute(stmt)
    return result.scalar_one()


class _FullMixin:
    """Full create and patch operations for PlanDefinition."""

    async def create_full(
        self,
        payload: Any,
        org_id: str,
        created_by: str,
    ) -> PlanDefinitionModel:
        async with self.session_factory() as session:
            return await create_full(session, payload, org_id, created_by)

    async def patch_full(
        self,
        plan_definition_id: int,
        payload: Any,
        org_id: str,
        updated_by: str | None = None,
    ) -> PlanDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(PlanDefinitionModel).where(
                PlanDefinitionModel.plan_definition_id == plan_definition_id,
                PlanDefinitionModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None
            return await _apply_patch(
                session, model, payload, org_id, updated_by or model.created_by
            )


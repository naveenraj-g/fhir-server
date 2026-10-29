from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.questionnaire import (
    QuestionnaireContact,
    QuestionnaireContactTelecom,
    QuestionnaireCoding,
    QuestionnaireEnableBehavior as QuestionnaireEnableBehaviorModel,
    QuestionnaireIdentifier,
    QuestionnaireIdentifierTypeCoding,
    QuestionnaireItem,
    QuestionnaireItemAnswerOption,
    QuestionnaireItemCoding,
    QuestionnaireItemEnableWhen,
    QuestionnaireItemInitial,
    QuestionnaireItemOperator as QuestionnaireItemOperatorModel,
    QuestionnaireItemType as QuestionnaireItemTypeModel,
    QuestionnaireJurisdiction,
    QuestionnaireJurisdictionCoding,
    QuestionnaireModel,
    QuestionnaireQuantityComparator as QuestionnaireQuantityComparatorModel,
    QuestionnaireStatus as QuestionnaireStatusModel,
    QuestionnaireUseContext,
    QuestionnaireUseContextValueCoding,
)
from app.schemas.questionnaire import QuestionnaireCreateSchema, QuestionnairePatchSchema

from ._shared import (
    _any_ref_kwargs,
    _org_ref_kwargs,
    _parse_org_ref,
    _parse_use_context_value_ref,
    _reference_kwargs,
    _use_context_value_ref_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource list fields on the create/patch payloads. A supplied list
# (even `[]`) replaces the corresponding rows wholesale; an omitted one is
# untouched.
_SUB = {"identifier", "contact", "use_context", "jurisdiction", "code", "item"}

# Handled by hand rather than the generic setattr loop, since they need
# conversion/promotion, not a plain column assignment.
_SPECIAL = {"status"}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput
    entry, targeting any of the dedicated coding[] child tables."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _model_status(status) -> QuestionnaireStatusModel:
    return QuestionnaireStatusModel[status.name]


def _model_item_type(item_type) -> QuestionnaireItemTypeModel:
    return QuestionnaireItemTypeModel[item_type.name]


def _model_enable_behavior(eb) -> QuestionnaireEnableBehaviorModel:
    return QuestionnaireEnableBehaviorModel[eb.name]


def _model_operator(op) -> QuestionnaireItemOperatorModel:
    return QuestionnaireItemOperatorModel[op.name]


def _model_comparator(c) -> QuestionnaireQuantityComparatorModel:
    return QuestionnaireQuantityComparatorModel[c.name]


async def _insert_items(session, questionnaire_pk: int, items_payload, parent_item_id, org_id, created_by):
    """Recursively inserts QuestionnaireItemInput rows (and their own
    grandchildren) — every row gets BOTH `questionnaire_pk` (denormalized
    straight to the root) and `parent_item_id` (the actual tree edge). See
    QuestionnaireModel's docstring for why. Parents are always flushed
    before their children are inserted, since `parent_item_id` is a real
    FK that must already exist."""
    for item_payload in items_payload:
        item = QuestionnaireItem(
            questionnaire_pk=questionnaire_pk,
            parent_item_id=parent_item_id,
            tenant_id=org_id,
            created_by=created_by,
            link_id=item_payload.link_id,
            definition=item_payload.definition,
            prefix=item_payload.prefix,
            text=item_payload.text,
            type=_model_item_type(item_payload.type),
            enable_behavior=_model_enable_behavior(item_payload.enable_behavior)
            if item_payload.enable_behavior
            else None,
            required=item_payload.required,
            repeats=item_payload.repeats,
            read_only=item_payload.read_only,
            max_length=item_payload.max_length,
            answer_value_set=item_payload.answer_value_set,
        )
        session.add(item)
        await session.flush()

        for coding in item_payload.code or []:
            session.add(
                QuestionnaireItemCoding(
                    questionnaire_item_id=item.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)
                )
            )

        for ew in item_payload.enable_when or []:
            session.add(
                QuestionnaireItemEnableWhen(
                    questionnaire_item_id=item.id,
                    tenant_id=org_id,
                    created_by=created_by,
                    question=ew.question,
                    operator=_model_operator(ew.operator),
                    answer_boolean=ew.answer_boolean,
                    answer_decimal=ew.answer_decimal,
                    answer_integer=ew.answer_integer,
                    answer_date=ew.answer_date,
                    answer_date_time=ew.answer_date_time,
                    answer_time=ew.answer_time,
                    answer_string=ew.answer_string,
                    # FhirCodingMixin's bare attribute names — _coding_prefix
                    # only renames the DB column, never the Python attribute
                    # (see CLAUDE.md's FhirCodingMixin invariant).
                    system=ew.answer_coding_system,
                    version=ew.answer_coding_version,
                    code=ew.answer_coding_code,
                    display=ew.answer_coding_display,
                    user_selected=ew.answer_coding_user_selected,
                    answer_quantity_value=ew.answer_quantity_value,
                    answer_quantity_comparator=_model_comparator(ew.answer_quantity_comparator)
                    if ew.answer_quantity_comparator
                    else None,
                    answer_quantity_unit=ew.answer_quantity_unit,
                    answer_quantity_system=ew.answer_quantity_system,
                    answer_quantity_code=ew.answer_quantity_code,
                    answer_reference_reference=ew.answer_reference,
                    **_any_ref_kwargs("answer_reference", ew.answer_reference, ew.answer_reference_display),
                )
            )

        for ao in item_payload.answer_option or []:
            session.add(
                QuestionnaireItemAnswerOption(
                    questionnaire_item_id=item.id,
                    tenant_id=org_id,
                    created_by=created_by,
                    value_integer=ao.value_integer,
                    value_date=ao.value_date,
                    value_time=ao.value_time,
                    value_string=ao.value_string,
                    # FhirCodingMixin's bare attribute names — see the
                    # enable_when block above for why.
                    system=ao.value_coding_system,
                    version=ao.value_coding_version,
                    code=ao.value_coding_code,
                    display=ao.value_coding_display,
                    user_selected=ao.value_coding_user_selected,
                    value_reference_reference=ao.value_reference,
                    **_any_ref_kwargs("value_reference", ao.value_reference, ao.value_reference_display),
                    initial_selected=ao.initial_selected,
                )
            )

        for ini in item_payload.initial or []:
            a = ini.value_attachment
            session.add(
                QuestionnaireItemInitial(
                    questionnaire_item_id=item.id,
                    tenant_id=org_id,
                    created_by=created_by,
                    value_boolean=ini.value_boolean,
                    value_decimal=ini.value_decimal,
                    value_integer=ini.value_integer,
                    value_date=ini.value_date,
                    value_date_time=ini.value_date_time,
                    value_time=ini.value_time,
                    value_string=ini.value_string,
                    value_uri=ini.value_uri,
                    # FhirAttachmentMixin's bare attribute names — see the
                    # enable_when block above for why (same invariant).
                    content_type=a.content_type if a else None,
                    language=a.language if a else None,
                    data=a.data if a else None,
                    url=a.url if a else None,
                    size=a.size if a else None,
                    hash=a.hash if a else None,
                    title=a.title if a else None,
                    creation=a.creation if a else None,
                    # FhirCodingMixin's bare attribute names.
                    system=ini.value_coding_system,
                    version=ini.value_coding_version,
                    code=ini.value_coding_code,
                    display=ini.value_coding_display,
                    user_selected=ini.value_coding_user_selected,
                    value_quantity_value=ini.value_quantity_value,
                    value_quantity_comparator=_model_comparator(ini.value_quantity_comparator)
                    if ini.value_quantity_comparator
                    else None,
                    value_quantity_unit=ini.value_quantity_unit,
                    value_quantity_system=ini.value_quantity_system,
                    value_quantity_code=ini.value_quantity_code,
                    value_reference_reference=ini.value_reference,
                    **_any_ref_kwargs("value_reference", ini.value_reference, ini.value_reference_display),
                )
            )

        if item_payload.item:
            await _insert_items(session, questionnaire_pk, item_payload.item, item.id, org_id, created_by)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(
        self,
        payload: QuestionnaireCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> QuestionnaireModel:
        async with self.session_factory() as session:
            q = QuestionnaireModel(
                tenant_id=org_id,
                user_id=payload.user_id,
                created_by=created_by,
                extension=payload.extension or [],
                url=payload.url,
                version=payload.version,
                name=payload.name,
                title=payload.title,
                derived_from=payload.derived_from,
                status=_model_status(payload.status),
                experimental=payload.experimental,
                subject_type=payload.subject_type,
                date=payload.date,
                publisher=payload.publisher,
                description=payload.description,
                purpose=payload.purpose,
                copyright=payload.copyright,
                approval_date=payload.approval_date,
                last_review_date=payload.last_review_date,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
            )
            session.add(q)
            await session.flush()

            for coding in payload.code or []:
                session.add(
                    QuestionnaireCoding(questionnaire_pk=q.id, tenant_id=org_id, **_coding_kwargs(coding, created_by))
                )

            for i in payload.identifier or []:
                a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
                identifier = QuestionnaireIdentifier(
                    questionnaire_pk=q.id,
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
                            QuestionnaireIdentifierTypeCoding(
                                questionnaire_identifier_id=identifier.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for c in payload.contact or []:
                contact = QuestionnaireContact(
                    questionnaire_pk=q.id, tenant_id=org_id, name=c.name, created_by=created_by
                )
                session.add(contact)
                if c.telecom:
                    await session.flush()
                    for t in c.telecom:
                        session.add(
                            QuestionnaireContactTelecom(
                                questionnaire_contact_id=contact.id,
                                tenant_id=org_id,
                                system=t.system,
                                value=t.value,
                                use=t.use,
                                rank=t.rank,
                                period_start=t.period_start,
                                period_end=t.period_end,
                                created_by=created_by,
                            )
                        )

            for uc in payload.use_context or []:
                vref_type, vref_id = (
                    _parse_use_context_value_ref(uc.value_reference) if uc.value_reference else (None, None)
                )
                await _validate_reference(session, org_id, vref_type, vref_id, "useContext.valueReference")
                use_context = QuestionnaireUseContext(
                    questionnaire_pk=q.id,
                    tenant_id=org_id,
                    system=uc.code_system,
                    version=uc.code_version,
                    code=uc.code_code,
                    display=uc.code_display,
                    user_selected=uc.code_user_selected,
                    value_codeable_concept_text=uc.value_codeable_concept_text,
                    value_quantity_value=uc.value_quantity_value,
                    value_quantity_comparator=_model_comparator(uc.value_quantity_comparator)
                    if uc.value_quantity_comparator
                    else None,
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
                    **_use_context_value_ref_kwargs(uc.value_reference, uc.value_reference_display),
                    created_by=created_by,
                )
                session.add(use_context)
                if uc.value_codeable_concept_coding:
                    await session.flush()
                    for coding in uc.value_codeable_concept_coding:
                        session.add(
                            QuestionnaireUseContextValueCoding(
                                questionnaire_use_context_id=use_context.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            for j in payload.jurisdiction or []:
                jurisdiction = QuestionnaireJurisdiction(
                    questionnaire_pk=q.id, tenant_id=org_id, text=j.text, created_by=created_by
                )
                session.add(jurisdiction)
                if j.coding:
                    await session.flush()
                    for coding in j.coding:
                        session.add(
                            QuestionnaireJurisdictionCoding(
                                questionnaire_jurisdiction_id=jurisdiction.id,
                                tenant_id=org_id,
                                **_coding_kwargs(coding, created_by),
                            )
                        )

            if payload.item:
                await _insert_items(session, q.id, payload.item, None, org_id, created_by)

            try:
                await session.commit()
                await session.refresh(q)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_questionnaire_id(q.questionnaire_id)

    async def patch_full(
        self,
        questionnaire_id: int,
        payload: QuestionnairePatchSchema,
        updated_by: str | None = None,
    ) -> QuestionnaireModel | None:
        """Patches core scalar fields and, for each sub-resource list that
        is supplied — even `[]` — atomically deletes all existing rows and
        inserts the new ones. `item`'s delete order deliberately does NOT
        follow the plain child-then-parent subquery pattern used by every
        other list here — see the inline comment above that block."""
        async with self.session_factory() as session:
            stmt = select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            q = (await session.execute(stmt)).scalars().first()
            if not q:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(q, field, value)

            if "status" in provided and payload.status is not None:
                q.status = _model_status(payload.status)

            # updated_by is itself a plain payload field for this default-
            # pattern resource (see QuestionnairePatchSchema) — the generic
            # setattr loop above already applied it when provided; no
            # separate actor-derived override needed, unlike an auth-
            # rollout resource's patch_full().
            #
            # updated_by is also OPTIONAL here (unlike an auth-rollout
            # resource's actor.sub, which is always present once
            # authenticated) — a PATCH that replaces a sub-resource list
            # still inserts genuinely NEW child rows, and
            # TenantAuditMixin.created_by is NOT NULL on every one of
            # them, so a None updated_by falls back to the parent
            # questionnaire's own original created_by rather than
            # violating that constraint.
            sub_created_by = updated_by if updated_by is not None else q.created_by

            if payload.code is not None:
                await session.execute(delete(QuestionnaireCoding).where(QuestionnaireCoding.questionnaire_pk == q.id))
                for coding in payload.code:
                    session.add(
                        QuestionnaireCoding(
                            questionnaire_pk=q.id, tenant_id=q.tenant_id, **_coding_kwargs(coding, sub_created_by)
                        )
                    )

            if payload.identifier is not None:
                await session.execute(
                    delete(QuestionnaireIdentifierTypeCoding).where(
                        QuestionnaireIdentifierTypeCoding.questionnaire_identifier_id.in_(
                            select(QuestionnaireIdentifier.id).where(
                                QuestionnaireIdentifier.questionnaire_pk == q.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(QuestionnaireIdentifier).where(QuestionnaireIdentifier.questionnaire_pk == q.id)
                )
                for i in payload.identifier:
                    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    await _validate_reference(session, q.tenant_id, a_type, a_id, "identifier.assigner")
                    identifier = QuestionnaireIdentifier(
                        questionnaire_pk=q.id,
                        tenant_id=q.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=sub_created_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                QuestionnaireIdentifierTypeCoding(
                                    questionnaire_identifier_id=identifier.id,
                                    tenant_id=q.tenant_id,
                                    **_coding_kwargs(coding, sub_created_by),
                                )
                            )

            if payload.contact is not None:
                await session.execute(
                    delete(QuestionnaireContactTelecom).where(
                        QuestionnaireContactTelecom.questionnaire_contact_id.in_(
                            select(QuestionnaireContact.id).where(QuestionnaireContact.questionnaire_pk == q.id)
                        )
                    )
                )
                await session.execute(delete(QuestionnaireContact).where(QuestionnaireContact.questionnaire_pk == q.id))
                for c in payload.contact:
                    contact = QuestionnaireContact(
                        questionnaire_pk=q.id, tenant_id=q.tenant_id, name=c.name, created_by=sub_created_by
                    )
                    session.add(contact)
                    if c.telecom:
                        await session.flush()
                        for t in c.telecom:
                            session.add(
                                QuestionnaireContactTelecom(
                                    questionnaire_contact_id=contact.id,
                                    tenant_id=q.tenant_id,
                                    system=t.system,
                                    value=t.value,
                                    use=t.use,
                                    rank=t.rank,
                                    period_start=t.period_start,
                                    period_end=t.period_end,
                                    created_by=sub_created_by,
                                )
                            )

            if payload.use_context is not None:
                await session.execute(
                    delete(QuestionnaireUseContextValueCoding).where(
                        QuestionnaireUseContextValueCoding.questionnaire_use_context_id.in_(
                            select(QuestionnaireUseContext.id).where(
                                QuestionnaireUseContext.questionnaire_pk == q.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(QuestionnaireUseContext).where(QuestionnaireUseContext.questionnaire_pk == q.id)
                )
                for uc in payload.use_context:
                    vref_type, vref_id = (
                        _parse_use_context_value_ref(uc.value_reference) if uc.value_reference else (None, None)
                    )
                    await _validate_reference(session, q.tenant_id, vref_type, vref_id, "useContext.valueReference")
                    use_context = QuestionnaireUseContext(
                        questionnaire_pk=q.id,
                        tenant_id=q.tenant_id,
                        system=uc.code_system,
                        version=uc.code_version,
                        code=uc.code_code,
                        display=uc.code_display,
                        user_selected=uc.code_user_selected,
                        value_codeable_concept_text=uc.value_codeable_concept_text,
                        value_quantity_value=uc.value_quantity_value,
                        value_quantity_comparator=_model_comparator(uc.value_quantity_comparator)
                        if uc.value_quantity_comparator
                        else None,
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
                        **_use_context_value_ref_kwargs(uc.value_reference, uc.value_reference_display),
                        created_by=sub_created_by,
                    )
                    session.add(use_context)
                    if uc.value_codeable_concept_coding:
                        await session.flush()
                        for coding in uc.value_codeable_concept_coding:
                            session.add(
                                QuestionnaireUseContextValueCoding(
                                    questionnaire_use_context_id=use_context.id,
                                    tenant_id=q.tenant_id,
                                    **_coding_kwargs(coding, sub_created_by),
                                )
                            )

            if payload.jurisdiction is not None:
                await session.execute(
                    delete(QuestionnaireJurisdictionCoding).where(
                        QuestionnaireJurisdictionCoding.questionnaire_jurisdiction_id.in_(
                            select(QuestionnaireJurisdiction.id).where(
                                QuestionnaireJurisdiction.questionnaire_pk == q.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(QuestionnaireJurisdiction).where(QuestionnaireJurisdiction.questionnaire_pk == q.id)
                )
                for j in payload.jurisdiction:
                    jurisdiction = QuestionnaireJurisdiction(
                        questionnaire_pk=q.id, tenant_id=q.tenant_id, text=j.text, created_by=sub_created_by
                    )
                    session.add(jurisdiction)
                    if j.coding:
                        await session.flush()
                        for coding in j.coding:
                            session.add(
                                QuestionnaireJurisdictionCoding(
                                    questionnaire_jurisdiction_id=jurisdiction.id,
                                    tenant_id=q.tenant_id,
                                    **_coding_kwargs(coding, sub_created_by),
                                )
                            )

            if payload.item is not None:
                # item's tree has unbounded depth, so this does NOT follow
                # the plain "subquery over this list's own parent" pattern
                # above — every QuestionnaireItem row, at every depth,
                # already carries questionnaire_pk denormalized straight
                # to this row (see QuestionnaireModel's docstring), so a
                # single `WHERE questionnaire_pk = q.id` on each of item's
                # 4 grandchild tables (themselves only ever one level below
                # a specific item, never further nested) plus one more on
                # `questionnaire_item` itself removes the entire tree in 5
                # statements regardless of how deep it was — no recursive
                # CTE, no per-level subquery chaining needed.
                item_ids_subq = select(QuestionnaireItem.id).where(QuestionnaireItem.questionnaire_pk == q.id)
                await session.execute(
                    delete(QuestionnaireItemCoding).where(QuestionnaireItemCoding.questionnaire_item_id.in_(item_ids_subq))
                )
                await session.execute(
                    delete(QuestionnaireItemEnableWhen).where(
                        QuestionnaireItemEnableWhen.questionnaire_item_id.in_(item_ids_subq)
                    )
                )
                await session.execute(
                    delete(QuestionnaireItemAnswerOption).where(
                        QuestionnaireItemAnswerOption.questionnaire_item_id.in_(item_ids_subq)
                    )
                )
                await session.execute(
                    delete(QuestionnaireItemInitial).where(
                        QuestionnaireItemInitial.questionnaire_item_id.in_(item_ids_subq)
                    )
                )
                await session.execute(delete(QuestionnaireItem).where(QuestionnaireItem.questionnaire_pk == q.id))

                if payload.item:
                    await _insert_items(session, q.id, payload.item, None, q.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Questionnaire sub-resource lists replaced",
                    extra={
                        "event": "questionnaire.sublists_replaced",
                        "questionnaire_id": questionnaire_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_questionnaire_id(questionnaire_id)

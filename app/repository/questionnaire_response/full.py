from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.questionnaire_response import (
    QuestionnaireResponseAnswer,
    QuestionnaireResponseBasedOn,
    QuestionnaireResponseIdentifierTypeCoding,
    QuestionnaireResponseItem,
    QuestionnaireResponseModel,
    QuestionnaireResponsePartOf,
    QuestionnaireResponseQuantityComparator as QuestionnaireResponseQuantityComparatorModel,
    QuestionnaireResponseStatus as QuestionnaireResponseStatusModel,
)
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _any_ref_kwargs,
    _author_ref_kwargs,
    _based_on_ref_kwargs,
    _encounter_ref_kwargs,
    _org_ref_kwargs,
    _parse_org_ref,
    _part_of_ref_kwargs,
    _source_ref_kwargs,
    _validate_author_reference,
    _validate_reference,
    _validate_source_reference,
)

logger = get_logger(__name__)

# Sub-resource fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is
# untouched. `identifier`/`subject`/`encounter`/`author`/`source` are 0..1
# nested objects flattened onto the main row rather than child-table
# lists, but behave the same way re: tri-state PATCH semantics.
_SUB = {"based_on", "part_of", "item"}
_SINGLE_OBJECT_FIELDS = {"identifier", "subject", "encounter", "author", "source"}
_SPECIAL = {"status"} | _SINGLE_OBJECT_FIELDS


def _model_status(status) -> QuestionnaireResponseStatusModel:
    return QuestionnaireResponseStatusModel[status.name]


def _model_comparator(c) -> QuestionnaireResponseQuantityComparatorModel:
    return QuestionnaireResponseQuantityComparatorModel[c.name]


def _identifier_kwargs(i) -> dict:
    """Full `identifier_*` column set for QuestionnaireResponse.identifier
    (0..1, flattened) — always returns every column, `None` where `i`
    itself is `None` or a given sub-field is absent, so the same helper
    works for CREATE (every field considered present) and PATCH's
    explicit-clear semantics (payload.identifier provided as `null`)."""
    a_type, a_id = (_parse_org_ref(i.assigner) if i and i.assigner else (None, None))
    return {
        "identifier_use": i.use if i else None,
        "identifier_type_text": i.type_text if i else None,
        "identifier_system": i.system if i else None,
        "identifier_value": i.value if i else None,
        "identifier_period_start": i.period_start if i else None,
        "identifier_period_end": i.period_end if i else None,
        "identifier_assigner_reference": i.assigner if i else None,
        "identifier_assigner_type": a_type,
        "identifier_assigner_id": a_id,
        "identifier_assigner_display": i.assigner_display if i else None,
        "identifier_assigner_identifier_use": i.assigner_identifier_use if i else None,
        "identifier_assigner_identifier_type_system": i.assigner_identifier_type_system if i else None,
        "identifier_assigner_identifier_type_version": i.assigner_identifier_type_version if i else None,
        "identifier_assigner_identifier_type_code": i.assigner_identifier_type_code if i else None,
        "identifier_assigner_identifier_type_display": i.assigner_identifier_type_display if i else None,
        "identifier_assigner_identifier_type_text": i.assigner_identifier_type_text if i else None,
        "identifier_assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected if i else None,
        "identifier_assigner_identifier_system": i.assigner_identifier_system if i else None,
        "identifier_assigner_identifier_value": i.assigner_identifier_value if i else None,
        "identifier_assigner_identifier_period_start": i.assigner_identifier_period_start if i else None,
        "identifier_assigner_identifier_period_end": i.assigner_identifier_period_end if i else None,
    }


def _identifier_type_coding_kwargs(coding, created_by: str | None) -> dict:
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _single_reference_kwargs(prefix: str, obj, ref_kwargs_fn) -> dict:
    """Full `{prefix}_*` column set for one of subject/encounter/author/
    source (each 0..1, flattened) — always returns every column, `None`
    where `obj` itself is `None` or a sub-field is absent. `ref_kwargs_fn`
    is whichever of `_any_ref_kwargs`/`_encounter_ref_kwargs`/
    `_author_ref_kwargs`/`_source_ref_kwargs` matches this field's target-
    type rules."""
    ref = obj.reference if obj else None
    display = obj.reference_display if obj else None
    kwargs = {f"{prefix}_reference": ref, **ref_kwargs_fn(prefix, ref, display)}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"{prefix}_{suffix}"] = getattr(obj, f"reference_{suffix}") if obj else None
    return kwargs


async def _validate_single_reference(session, tenant_id, prefix: str, kwargs: dict) -> None:
    """Runs the matching existence check (only `encounter` and the
    modeled subsets of `author`/`source` ever actually check anything —
    see `_shared`'s `_validate_author_reference`/`_validate_source_reference`)."""
    ref_type, ref_id = kwargs.get(f"{prefix}_type"), kwargs.get(f"{prefix}_id")
    if prefix == "encounter":
        await _validate_reference(session, tenant_id, ref_type, ref_id, "encounter")
    elif prefix == "author":
        await _validate_author_reference(session, tenant_id, ref_type, ref_id)
    elif prefix == "source":
        await _validate_source_reference(session, tenant_id, ref_type, ref_id)
    # subject is genuinely Reference(Any) — never validated.


async def _insert_items(
    session,
    qr_pk: int,
    items_payload,
    parent_item_id: int | None,
    parent_answer_id: int | None,
    tenant_id: str,
    created_by: str | None,
):
    """Recursively inserts QuestionnaireResponseItemInput rows (and their
    own answers, and any further-nested items under either path) — see
    QuestionnaireResponseItem's docstring for the two-table mutual
    recursion this walks. Parents are always flushed before their
    children are inserted, since `parent_item_id` (a real FK) and
    `item_id` (also a real FK) must already exist."""
    for item_payload in items_payload:
        item = QuestionnaireResponseItem(
            questionnaire_response_pk=qr_pk,
            parent_item_id=parent_item_id,
            parent_answer_id=parent_answer_id,
            tenant_id=tenant_id,
            created_by=created_by,
            link_id=item_payload.link_id,
            definition=item_payload.definition,
            text=item_payload.text,
        )
        session.add(item)
        await session.flush()

        for ans_payload in item_payload.answer or []:
            at = ans_payload.value_attachment
            answer = QuestionnaireResponseAnswer(
                questionnaire_response_pk=qr_pk,
                item_id=item.id,
                tenant_id=tenant_id,
                created_by=created_by,
                value_boolean=ans_payload.value_boolean,
                value_decimal=ans_payload.value_decimal,
                value_integer=ans_payload.value_integer,
                value_date=ans_payload.value_date,
                value_date_time=ans_payload.value_date_time,
                value_time=ans_payload.value_time,
                value_string=ans_payload.value_string,
                value_uri=ans_payload.value_uri,
                # FhirAttachmentMixin's bare attribute names — _attachment_prefix
                # only renames the DB column, never the Python attribute.
                content_type=at.content_type if at else None,
                language=at.language if at else None,
                data=at.data if at else None,
                url=at.url if at else None,
                size=at.size if at else None,
                hash=at.hash if at else None,
                title=at.title if at else None,
                creation=at.creation if at else None,
                # FhirCodingMixin's bare attribute names.
                system=ans_payload.value_coding_system,
                version=ans_payload.value_coding_version,
                code=ans_payload.value_coding_code,
                display=ans_payload.value_coding_display,
                user_selected=ans_payload.value_coding_user_selected,
                value_quantity_value=ans_payload.value_quantity_value,
                value_quantity_comparator=_model_comparator(ans_payload.value_quantity_comparator)
                if ans_payload.value_quantity_comparator
                else None,
                value_quantity_unit=ans_payload.value_quantity_unit,
                value_quantity_system=ans_payload.value_quantity_system,
                value_quantity_code=ans_payload.value_quantity_code,
                value_reference_reference=ans_payload.value_reference,
                **_any_ref_kwargs(
                    "value_reference", ans_payload.value_reference, ans_payload.value_reference_display
                ),
            )
            session.add(answer)
            await session.flush()

            if ans_payload.item:
                await _insert_items(session, qr_pk, ans_payload.item, None, answer.id, tenant_id, created_by)

        if item_payload.item:
            await _insert_items(session, qr_pk, item_payload.item, item.id, None, tenant_id, created_by)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(
        self,
        payload: QuestionnaireResponseCreateSchema,
    ) -> QuestionnaireResponseModel:
        """Default (gateway-trusted) pattern: `tenant_id`/`user_id`/
        `created_by` all come straight off the validated payload, not a
        verified JWT — see QuestionnaireResponseCreateSchema's docstring."""
        async with self.session_factory() as session:
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, _any_ref_kwargs)
            encounter_kwargs = _single_reference_kwargs("encounter", payload.encounter, _encounter_ref_kwargs)
            author_kwargs = _single_reference_kwargs("author", payload.author, _author_ref_kwargs)
            source_kwargs = _single_reference_kwargs("source", payload.source, _source_ref_kwargs)

            await _validate_single_reference(session, payload.tenant_id, "encounter", encounter_kwargs)
            await _validate_single_reference(session, payload.tenant_id, "author", author_kwargs)
            await _validate_single_reference(session, payload.tenant_id, "source", source_kwargs)

            qr = QuestionnaireResponseModel(
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                created_by=payload.created_by,
                extension=payload.extension or [],
                **_identifier_kwargs(payload.identifier),
                questionnaire=payload.questionnaire,
                status=_model_status(payload.status),
                authored=payload.authored,
                **subject_kwargs,
                **encounter_kwargs,
                **author_kwargs,
                **source_kwargs,
            )
            session.add(qr)
            await session.flush()

            if payload.identifier and payload.identifier.type_coding:
                for coding in payload.identifier.type_coding:
                    session.add(
                        QuestionnaireResponseIdentifierTypeCoding(
                            questionnaire_response_pk=qr.id,
                            tenant_id=payload.tenant_id,
                            **_identifier_type_coding_kwargs(coding, payload.created_by),
                        )
                    )

            for b in payload.based_on or []:
                session.add(
                    QuestionnaireResponseBasedOn(
                        questionnaire_response_pk=qr.id,
                        tenant_id=payload.tenant_id,
                        created_by=payload.created_by,
                        reference_reference=b.reference,
                        **_based_on_ref_kwargs("reference", b.reference, b.reference_display),
                        **{
                            f"reference_{suffix}": getattr(b, f"reference_{suffix}")
                            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
                        },
                    )
                )

            for p in payload.part_of or []:
                session.add(
                    QuestionnaireResponsePartOf(
                        questionnaire_response_pk=qr.id,
                        tenant_id=payload.tenant_id,
                        created_by=payload.created_by,
                        reference_reference=p.reference,
                        **_part_of_ref_kwargs("reference", p.reference, p.reference_display),
                        **{
                            f"reference_{suffix}": getattr(p, f"reference_{suffix}")
                            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
                        },
                    )
                )

            if payload.item:
                await _insert_items(session, qr.id, payload.item, None, None, payload.tenant_id, payload.created_by)

            try:
                await session.commit()
                await session.refresh(qr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_questionnaire_response_id(qr.questionnaire_response_id)

    async def patch_full(
        self,
        questionnaire_response_id: int,
        payload: QuestionnaireResponsePatchSchema,
    ) -> QuestionnaireResponseModel | None:
        """Patches core scalar fields and, for each sub-resource list that
        is supplied — even `[]` — atomically deletes all existing rows and
        inserts the new ones. `item`'s delete order deliberately does NOT
        follow the plain child-then-parent subquery pattern used by
        based_on/part_of — see the inline comment above that block, and
        QuestionnaireResponseItem's own docstring for why `answer` must be
        deleted before `item`."""
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id
            )
            qr = (await session.execute(stmt)).scalars().first()
            if not qr:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(qr, field, value)

            # updated_by is itself a plain payload field for this default-
            # pattern resource — the generic setattr loop above already
            # applied it when provided.
            sub_created_by = payload.updated_by if payload.updated_by is not None else qr.created_by

            if "status" in provided and payload.status is not None:
                qr.status = _model_status(payload.status)

            if "identifier" in provided:
                for col, value in _identifier_kwargs(payload.identifier).items():
                    setattr(qr, col, value)
                await session.execute(
                    delete(QuestionnaireResponseIdentifierTypeCoding).where(
                        QuestionnaireResponseIdentifierTypeCoding.questionnaire_response_pk == qr.id
                    )
                )
                if payload.identifier and payload.identifier.type_coding:
                    for coding in payload.identifier.type_coding:
                        session.add(
                            QuestionnaireResponseIdentifierTypeCoding(
                                questionnaire_response_pk=qr.id,
                                tenant_id=qr.tenant_id,
                                **_identifier_type_coding_kwargs(coding, sub_created_by),
                            )
                        )

            for prefix, ref_kwargs_fn in (
                ("subject", _any_ref_kwargs),
                ("encounter", _encounter_ref_kwargs),
                ("author", _author_ref_kwargs),
                ("source", _source_ref_kwargs),
            ):
                if prefix in provided:
                    kwargs = _single_reference_kwargs(prefix, getattr(payload, prefix), ref_kwargs_fn)
                    await _validate_single_reference(session, qr.tenant_id, prefix, kwargs)
                    for col, value in kwargs.items():
                        setattr(qr, col, value)

            if payload.based_on is not None:
                await session.execute(
                    delete(QuestionnaireResponseBasedOn).where(
                        QuestionnaireResponseBasedOn.questionnaire_response_pk == qr.id
                    )
                )
                for b in payload.based_on:
                    session.add(
                        QuestionnaireResponseBasedOn(
                            questionnaire_response_pk=qr.id,
                            tenant_id=qr.tenant_id,
                            created_by=sub_created_by,
                            reference_reference=b.reference,
                            **_based_on_ref_kwargs("reference", b.reference, b.reference_display),
                            **{
                                f"reference_{suffix}": getattr(b, f"reference_{suffix}")
                                for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
                            },
                        )
                    )

            if payload.part_of is not None:
                await session.execute(
                    delete(QuestionnaireResponsePartOf).where(
                        QuestionnaireResponsePartOf.questionnaire_response_pk == qr.id
                    )
                )
                for p in payload.part_of:
                    session.add(
                        QuestionnaireResponsePartOf(
                            questionnaire_response_pk=qr.id,
                            tenant_id=qr.tenant_id,
                            created_by=sub_created_by,
                            reference_reference=p.reference,
                            **_part_of_ref_kwargs("reference", p.reference, p.reference_display),
                            **{
                                f"reference_{suffix}": getattr(p, f"reference_{suffix}")
                                for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
                            },
                        )
                    )

            if payload.item is not None:
                # item/answer's combined tree has unbounded depth and is
                # mutually recursive across two tables — every row of
                # both already carries questionnaire_response_pk
                # denormalized straight to this row (see
                # QuestionnaireResponseModel's docstring), so a single
                # `WHERE questionnaire_response_pk = qr.id` on each table
                # removes the entire tree regardless of how deep it was.
                # `answer` MUST be deleted before `item` — see
                # QuestionnaireResponseItem's own docstring for why
                # `parent_answer_id` deliberately isn't a real FK: this
                # ordering is what makes that safe.
                await session.execute(
                    delete(QuestionnaireResponseAnswer).where(
                        QuestionnaireResponseAnswer.questionnaire_response_pk == qr.id
                    )
                )
                await session.execute(
                    delete(QuestionnaireResponseItem).where(
                        QuestionnaireResponseItem.questionnaire_response_pk == qr.id
                    )
                )

                if payload.item:
                    await _insert_items(session, qr.id, payload.item, None, None, qr.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted((_SUB | _SINGLE_OBJECT_FIELDS) & set(data.keys()))
            if replaced:
                logger.debug(
                    "QuestionnaireResponse sub-resource lists replaced",
                    extra={
                        "event": "questionnaire_response.sublists_replaced",
                        "questionnaire_response_id": questionnaire_response_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_questionnaire_response_id(questionnaire_response_id)

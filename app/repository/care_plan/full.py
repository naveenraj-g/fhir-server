from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.care_plan import (
    CarePlanActivity,
    CarePlanActivityDetailCodeCoding,
    CarePlanActivityDetailGoal,
    CarePlanActivityDetailPerformer,
    CarePlanActivityDetailProductCoding,
    CarePlanActivityDetailReasonCode,
    CarePlanActivityDetailReasonCodeCoding,
    CarePlanActivityDetailReasonReference,
    CarePlanActivityDetailStatusReasonCoding,
    CarePlanActivityOutcomeCC,
    CarePlanActivityOutcomeCCCoding,
    CarePlanActivityOutcomeReference,
    CarePlanActivityProgress,
    CarePlanAddresses,
    CarePlanBasedOn,
    CarePlanCareTeam,
    CarePlanCategory,
    CarePlanCategoryCoding,
    CarePlanContributor,
    CarePlanGoal,
    CarePlanIdentifier,
    CarePlanIdentifierTypeCoding,
    CarePlanModel,
    CarePlanNote,
    CarePlanPartOf,
    CarePlanReplaces,
)
from app.schemas.care_plan import CarePlanCreateSchema, CarePlanPatchSchema

from ._shared import (
    _parse_activity_detail_location_ref,
    _parse_activity_detail_performer_ref,
    _parse_activity_detail_product_ref,
    _parse_activity_detail_reason_ref,
    _parse_activity_ref,
    _parse_addresses_ref,
    _parse_assigner_ref,
    _parse_author_ref,
    _parse_based_on_ref,
    _parse_care_team_ref,
    _parse_contributor_ref,
    _parse_encounter_ref,
    _parse_goal_ref,
    _parse_open_ref,
    _parse_part_of_ref,
    _parse_replaces_ref,
    _parse_subject_ref,
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


async def _add_identifiers(session, care_plan_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = CarePlanIdentifier(
            care_plan_pk=care_plan_pk,
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
            assigner_identifier_use=i.assigner_identifier_use,
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()
        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    CarePlanIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_categories(session, care_plan_pk: int, org_id: str, categories, created_by: str) -> None:
    for c in categories or []:
        cat = CarePlanCategory(
            care_plan_pk=care_plan_pk,
            tenant_id=org_id,
            text=c.text,
            created_by=created_by,
        )
        session.add(cat)
        await session.flush()
        if c.coding:
            for coding in c.coding:
                session.add(
                    CarePlanCategoryCoding(
                        category_id=cat.id,
                        **_coding_kwargs(coding, org_id, created_by),
                    )
                )


async def _add_based_on(session, care_plan_pk: int, org_id: str, based_on, created_by: str) -> None:
    for ref_str in based_on or []:
        ref_type, ref_id = _parse_based_on_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "basedOn")
        session.add(
            CarePlanBasedOn(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_replaces(session, care_plan_pk: int, org_id: str, replaces, created_by: str) -> None:
    for ref_str in replaces or []:
        ref_type, ref_id = _parse_replaces_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "replaces")
        session.add(
            CarePlanReplaces(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_part_of(session, care_plan_pk: int, org_id: str, part_of, created_by: str) -> None:
    for ref_str in part_of or []:
        ref_type, ref_id = _parse_part_of_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "partOf")
        session.add(
            CarePlanPartOf(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_contributors(session, care_plan_pk: int, org_id: str, contributors, created_by: str) -> None:
    for ref_str in contributors or []:
        ref_type, ref_id = _parse_contributor_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "contributor")
        session.add(
            CarePlanContributor(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_care_teams(session, care_plan_pk: int, org_id: str, care_teams, created_by: str) -> None:
    for ref_str in care_teams or []:
        ref_type, ref_id = _parse_care_team_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "careTeam")
        session.add(
            CarePlanCareTeam(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_addresses(session, care_plan_pk: int, org_id: str, addresses, created_by: str) -> None:
    for ref_str in addresses or []:
        ref_type, ref_id = _parse_addresses_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "addresses")
        session.add(
            CarePlanAddresses(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_goals(session, care_plan_pk: int, org_id: str, goals, created_by: str) -> None:
    for ref_str in goals or []:
        ref_type, ref_id = _parse_goal_ref(ref_str)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "goal")
        session.add(
            CarePlanGoal(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_notes(session, care_plan_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        a_type, a_id = _parse_author_ref(n.author_reference) if n.author_reference else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "note.author")
        session.add(
            CarePlanNote(
                care_plan_pk=care_plan_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference_reference=n.author_reference,
                author_reference_type=a_type,
                author_reference_id=a_id,
                author_reference_display=n.author_reference_display,
                created_by=created_by,
            )
        )


async def _add_activities(session, care_plan_pk: int, org_id: str, activities, created_by: str) -> None:
    for act in activities or []:
        ref_type, ref_id = _parse_activity_ref(act.reference) if act.reference else (None, None)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "activity.reference")

        det = act.detail
        loc_type, loc_id = _parse_activity_detail_location_ref(det.location) if (det and det.location) else (None, None)
        if loc_type and loc_id:
            await _validate_ref(session, org_id, loc_type, loc_id, "activity.detail.location")

        prod_type, prod_id = _parse_activity_detail_product_ref(det.product_reference) if (det and det.product_reference) else (None, None)
        if prod_type and prod_id:
            await _validate_ref(session, org_id, prod_type, prod_id, "activity.detail.productReference")

        activity_row = CarePlanActivity(
            care_plan_pk=care_plan_pk,
            tenant_id=org_id,
            reference_reference=act.reference,
            reference_type=ref_type,
            reference_id=ref_id,
            reference_display=act.reference_display,
            # detail
            detail_kind=det.kind if det else None,
            detail_instantiates_canonical=det.instantiates_canonical if det else None,
            detail_instantiates_uri=det.instantiates_uri if det else None,
            detail_code_text=det.code.text if (det and det.code) else None,
            detail_status=det.status if det else None,
            detail_status_reason_text=det.status_reason.text if (det and det.status_reason) else None,
            detail_do_not_perform=det.do_not_perform if det else None,
            detail_scheduled_timing=det.scheduled_timing if det else None,
            detail_scheduled_period_start=det.scheduled_period_start if det else None,
            detail_scheduled_period_end=det.scheduled_period_end if det else None,
            detail_scheduled_string=det.scheduled_string if det else None,
            detail_location_reference=det.location if det else None,
            detail_location_type=loc_type,
            detail_location_id=loc_id,
            detail_location_display=det.location_display if det else None,
            detail_product_codeable_concept_text=det.product_codeable_concept.text if (det and det.product_codeable_concept) else None,
            detail_product_reference=det.product_reference if det else None,
            detail_product_type=prod_type,
            detail_product_id=prod_id,
            detail_product_display=det.product_display if det else None,
            detail_daily_amount_value=det.daily_amount.value if (det and det.daily_amount) else None,
            detail_daily_amount_comparator=det.daily_amount.comparator if (det and det.daily_amount) else None,
            detail_daily_amount_unit=det.daily_amount.unit if (det and det.daily_amount) else None,
            detail_daily_amount_system=det.daily_amount.system if (det and det.daily_amount) else None,
            detail_daily_amount_code=det.daily_amount.code if (det and det.daily_amount) else None,
            detail_quantity_value=det.quantity.value if (det and det.quantity) else None,
            detail_quantity_comparator=det.quantity.comparator if (det and det.quantity) else None,
            detail_quantity_unit=det.quantity.unit if (det and det.quantity) else None,
            detail_quantity_system=det.quantity.system if (det and det.quantity) else None,
            detail_quantity_code=det.quantity.code if (det and det.quantity) else None,
            detail_description=det.description if det else None,
            created_by=created_by,
        )
        session.add(activity_row)
        await session.flush()

        # Outcome CodeableConcepts
        if act.outcome_codeable_concept:
            for occ in act.outcome_codeable_concept:
                occ_row = CarePlanActivityOutcomeCC(
                    activity_id=activity_row.id,
                    tenant_id=org_id,
                    text=occ.text,
                    created_by=created_by,
                )
                session.add(occ_row)
                await session.flush()
                if occ.coding:
                    for c in occ.coding:
                        session.add(
                            CarePlanActivityOutcomeCCCoding(
                                outcome_cc_id=occ_row.id,
                                **_coding_kwargs(c, org_id, created_by),
                            )
                        )

        # Outcome References
        if act.outcome_reference:
            for oref in act.outcome_reference:
                _, oref_type, oref_id, _ = _parse_open_ref(oref)
                session.add(
                    CarePlanActivityOutcomeReference(
                        activity_id=activity_row.id,
                        tenant_id=org_id,
                        reference_reference=oref,
                        reference_type=oref_type,
                        reference_id=oref_id,
                        created_by=created_by,
                    )
                )

        # Progress annotations
        if act.progress:
            for p in act.progress:
                pa_type, pa_id = _parse_author_ref(p.author_reference) if p.author_reference else (None, None)
                if pa_type and pa_id:
                    await _validate_ref(session, org_id, pa_type, pa_id, "activity.progress.author")
                session.add(
                    CarePlanActivityProgress(
                        activity_id=activity_row.id,
                        tenant_id=org_id,
                        text=p.text,
                        time=p.time,
                        author_string=p.author_string,
                        author_reference_reference=p.author_reference,
                        author_reference_type=pa_type,
                        author_reference_id=pa_id,
                        author_reference_display=p.author_reference_display,
                        created_by=created_by,
                    )
                )

        # Detail code codings
        if det and det.code and det.code.coding:
            for c in det.code.coding:
                session.add(
                    CarePlanActivityDetailCodeCoding(
                        activity_id=activity_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        # Detail reason codes
        if det and det.reason_code:
            for rc in det.reason_code:
                rc_row = CarePlanActivityDetailReasonCode(
                    activity_id=activity_row.id,
                    tenant_id=org_id,
                    text=rc.text,
                    created_by=created_by,
                )
                session.add(rc_row)
                await session.flush()
                if rc.coding:
                    for c in rc.coding:
                        session.add(
                            CarePlanActivityDetailReasonCodeCoding(
                                reason_code_id=rc_row.id,
                                **_coding_kwargs(c, org_id, created_by),
                            )
                        )

        # Detail reason references
        if det and det.reason_reference:
            for rr in det.reason_reference:
                rr_type, rr_id = _parse_activity_detail_reason_ref(rr)
                if rr_type and rr_id:
                    await _validate_ref(session, org_id, rr_type, rr_id, "activity.detail.reasonReference")
                session.add(
                    CarePlanActivityDetailReasonReference(
                        activity_id=activity_row.id,
                        tenant_id=org_id,
                        reference_reference=rr,
                        reference_type=rr_type,
                        reference_id=rr_id,
                        created_by=created_by,
                    )
                )

        # Detail goals
        if det and det.goal:
            for g in det.goal:
                g_type, g_id = _parse_goal_ref(g)
                if g_type and g_id:
                    await _validate_ref(session, org_id, g_type, g_id, "activity.detail.goal")
                session.add(
                    CarePlanActivityDetailGoal(
                        activity_id=activity_row.id,
                        tenant_id=org_id,
                        reference_reference=g,
                        reference_type=g_type,
                        reference_id=g_id,
                        created_by=created_by,
                    )
                )

        # Detail status reason codings
        if det and det.status_reason and det.status_reason.coding:
            for c in det.status_reason.coding:
                session.add(
                    CarePlanActivityDetailStatusReasonCoding(
                        activity_id=activity_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        # Detail performers
        if det and det.performer:
            for perf in det.performer:
                p_type, p_id = _parse_activity_detail_performer_ref(perf)
                if p_type and p_id:
                    await _validate_ref(session, org_id, p_type, p_id, "activity.detail.performer")
                session.add(
                    CarePlanActivityDetailPerformer(
                        activity_id=activity_row.id,
                        tenant_id=org_id,
                        reference_reference=perf,
                        reference_type=p_type,
                        reference_id=p_id,
                        created_by=created_by,
                    )
                )

        # Detail product codings
        if det and det.product_codeable_concept and det.product_codeable_concept.coding:
            for c in det.product_codeable_concept.coding:
                session.add(
                    CarePlanActivityDetailProductCoding(
                        activity_id=activity_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


class _FullMixin:
    """Full atomic CRUD operations for CarePlan."""

    async def create_full(
        self,
        payload: CarePlanCreateSchema,
        org_id: str,
        created_by: str,
    ) -> CarePlanModel:
        async with self.session_factory() as session:
            # Parse references
            s_type, s_id = _parse_subject_ref(payload.subject)
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            e_type, e_id = _parse_encounter_ref(payload.encounter) if payload.encounter else (None, None)
            if e_type and e_id:
                await _validate_ref(session, org_id, e_type, e_id, "encounter")

            a_type, a_id = _parse_author_ref(payload.author) if payload.author else (None, None)
            if a_type and a_id:
                await _validate_ref(session, org_id, a_type, a_id, "author")

            care_plan = CarePlanModel(
                tenant_id=org_id,
                created_by=created_by,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                status=payload.status,
                intent=payload.intent,
                title=payload.title,
                description=payload.description,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject_display,
                encounter_reference=payload.encounter,
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=payload.encounter_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created=payload.created,
                author_reference=payload.author,
                author_type=a_type,
                author_id=a_id,
                author_display=payload.author_display,
            )
            session.add(care_plan)
            await session.flush()

            # Add collections
            await _add_identifiers(session, care_plan.id, org_id, payload.identifier, created_by)
            await _add_categories(session, care_plan.id, org_id, payload.category, created_by)
            await _add_based_on(session, care_plan.id, org_id, payload.based_on, created_by)
            await _add_replaces(session, care_plan.id, org_id, payload.replaces, created_by)
            await _add_part_of(session, care_plan.id, org_id, payload.part_of, created_by)
            await _add_contributors(session, care_plan.id, org_id, payload.contributor, created_by)
            await _add_care_teams(session, care_plan.id, org_id, payload.care_team, created_by)
            await _add_addresses(session, care_plan.id, org_id, payload.addresses, created_by)
            await _add_goals(session, care_plan.id, org_id, payload.goal, created_by)
            await _add_activities(session, care_plan.id, org_id, payload.activity, created_by)
            await _add_notes(session, care_plan.id, org_id, payload.note, created_by)

            await session.commit()

        return await self.get_by_care_plan_id_in_org(care_plan.care_plan_id, org_id)

    async def patch_full(
        self,
        care_plan_id: int,
        payload: CarePlanPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> CarePlanModel | None:
        async with self.session_factory() as session:
            stmt = select(CarePlanModel).where(
                CarePlanModel.care_plan_id == care_plan_id,
                CarePlanModel.tenant_id == org_id,
            )
            care_plan = (await session.execute(stmt)).scalars().first()
            if not care_plan:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set:
                care_plan.status = payload.status
            if "intent" in fields_set:
                care_plan.intent = payload.intent
            if "title" in fields_set:
                care_plan.title = payload.title
            if "description" in fields_set:
                care_plan.description = payload.description
            if "instantiates_canonical" in fields_set:
                care_plan.instantiates_canonical = payload.instantiates_canonical
            if "instantiates_uri" in fields_set:
                care_plan.instantiates_uri = payload.instantiates_uri
            if "period_start" in fields_set:
                care_plan.period_start = payload.period_start
            if "period_end" in fields_set:
                care_plan.period_end = payload.period_end
            if "created" in fields_set:
                care_plan.created = payload.created

            if "subject" in fields_set or "subject_display" in fields_set:
                if payload.subject:
                    s_type, s_id = _parse_subject_ref(payload.subject)
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                    care_plan.subject_reference = payload.subject
                    care_plan.subject_type = s_type
                    care_plan.subject_id = s_id
                elif "subject" in fields_set and payload.subject is None:
                    care_plan.subject_reference = None
                    care_plan.subject_type = None
                    care_plan.subject_id = None
                if "subject_display" in fields_set:
                    care_plan.subject_display = payload.subject_display

            if "encounter" in fields_set or "encounter_display" in fields_set:
                if payload.encounter:
                    e_type, e_id = _parse_encounter_ref(payload.encounter)
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                    care_plan.encounter_reference = payload.encounter
                    care_plan.encounter_type = e_type
                    care_plan.encounter_id = e_id
                elif "encounter" in fields_set and payload.encounter is None:
                    care_plan.encounter_reference = None
                    care_plan.encounter_type = None
                    care_plan.encounter_id = None
                if "encounter_display" in fields_set:
                    care_plan.encounter_display = payload.encounter_display

            if "author" in fields_set or "author_display" in fields_set:
                if payload.author:
                    a_type, a_id = _parse_author_ref(payload.author)
                    await _validate_ref(session, org_id, a_type, a_id, "author")
                    care_plan.author_reference = payload.author
                    care_plan.author_type = a_type
                    care_plan.author_id = a_id
                elif "author" in fields_set and payload.author is None:
                    care_plan.author_reference = None
                    care_plan.author_type = None
                    care_plan.author_id = None
                if "author_display" in fields_set:
                    care_plan.author_display = payload.author_display

            # Sub-resource replacements
            if "identifier" in fields_set:
                await session.execute(
                    delete(CarePlanIdentifier).where(CarePlanIdentifier.care_plan_pk == care_plan.id)
                )
                if payload.identifier:
                    await _add_identifiers(session, care_plan.id, org_id, payload.identifier, updated_by)

            if "category" in fields_set:
                await session.execute(
                    delete(CarePlanCategory).where(CarePlanCategory.care_plan_pk == care_plan.id)
                )
                if payload.category:
                    await _add_categories(session, care_plan.id, org_id, payload.category, updated_by)

            if "based_on" in fields_set:
                await session.execute(
                    delete(CarePlanBasedOn).where(CarePlanBasedOn.care_plan_pk == care_plan.id)
                )
                if payload.based_on:
                    await _add_based_on(session, care_plan.id, org_id, payload.based_on, updated_by)

            if "replaces" in fields_set:
                await session.execute(
                    delete(CarePlanReplaces).where(CarePlanReplaces.care_plan_pk == care_plan.id)
                )
                if payload.replaces:
                    await _add_replaces(session, care_plan.id, org_id, payload.replaces, updated_by)

            if "part_of" in fields_set:
                await session.execute(
                    delete(CarePlanPartOf).where(CarePlanPartOf.care_plan_pk == care_plan.id)
                )
                if payload.part_of:
                    await _add_part_of(session, care_plan.id, org_id, payload.part_of, updated_by)

            if "contributor" in fields_set:
                await session.execute(
                    delete(CarePlanContributor).where(CarePlanContributor.care_plan_pk == care_plan.id)
                )
                if payload.contributor:
                    await _add_contributors(session, care_plan.id, org_id, payload.contributor, updated_by)

            if "care_team" in fields_set:
                await session.execute(
                    delete(CarePlanCareTeam).where(CarePlanCareTeam.care_plan_pk == care_plan.id)
                )
                if payload.care_team:
                    await _add_care_teams(session, care_plan.id, org_id, payload.care_team, updated_by)

            if "addresses" in fields_set:
                await session.execute(
                    delete(CarePlanAddresses).where(CarePlanAddresses.care_plan_pk == care_plan.id)
                )
                if payload.addresses:
                    await _add_addresses(session, care_plan.id, org_id, payload.addresses, updated_by)

            if "goal" in fields_set:
                await session.execute(
                    delete(CarePlanGoal).where(CarePlanGoal.care_plan_pk == care_plan.id)
                )
                if payload.goal:
                    await _add_goals(session, care_plan.id, org_id, payload.goal, updated_by)

            if "activity" in fields_set:
                await session.execute(
                    delete(CarePlanActivity).where(CarePlanActivity.care_plan_pk == care_plan.id)
                )
                if payload.activity:
                    await _add_activities(session, care_plan.id, org_id, payload.activity, updated_by)

            if "note" in fields_set:
                await session.execute(
                    delete(CarePlanNote).where(CarePlanNote.care_plan_pk == care_plan.id)
                )
                if payload.note:
                    await _add_notes(session, care_plan.id, org_id, payload.note, updated_by)

            care_plan.updated_by = updated_by

            await session.commit()

        return await self.get_by_care_plan_id_in_org(care_plan_id, org_id)

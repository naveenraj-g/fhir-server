from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.risk_assessment import (
    RiskAssessmentBasisModel,
    RiskAssessmentCodeCodingModel,
    RiskAssessmentConditionReferenceType,
    RiskAssessmentIdentifierModel,
    RiskAssessmentIdentifierTypeCodingModel,
    RiskAssessmentMethodCodingModel,
    RiskAssessmentModel,
    RiskAssessmentNoteAuthorReferenceType,
    RiskAssessmentNoteModel,
    RiskAssessmentPerformerReferenceType,
    RiskAssessmentPredictionModel,
    RiskAssessmentPredOutcomeCodingModel,
    RiskAssessmentPredQualRiskCodingModel,
    RiskAssessmentReasonCodeCodingModel,
    RiskAssessmentReasonCodeModel,
    RiskAssessmentReasonReferenceModel,
    RiskAssessmentReasonReferenceType,
    RiskAssessmentStatus,
)
from app.schemas.risk_assessment import (
    RiskAssessmentCreateSchema,
    RiskAssessmentPatchSchema,
)

from ._shared import (
    _list_reference_kwargs,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _FullMixin:
    """Full-model write operations (create, patch) for RiskAssessment."""

    async def create(
        self,
        payload: RiskAssessmentCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> RiskAssessmentModel:
        async with self.session_factory() as session:
            # 1. Validate references
            subj_kwargs = _single_reference_kwargs(
                "subject", payload.subject, SubjectReferenceType
            )
            await _validate_ref(
                session,
                subj_kwargs["subject_type"],
                subj_kwargs["subject_id"],
                org_id,
                "subject",
            )

            based_on_kwargs = _single_reference_kwargs(
                "based_on", payload.based_on, None
            )
            if payload.based_on:
                await _validate_ref(
                    session,
                    based_on_kwargs["based_on_type"],
                    based_on_kwargs["based_on_id"],
                    org_id,
                    "based_on",
                )

            parent_kwargs = _single_reference_kwargs(
                "parent", payload.parent, None
            )
            if payload.parent:
                await _validate_ref(
                    session,
                    parent_kwargs["parent_type"],
                    parent_kwargs["parent_id"],
                    org_id,
                    "parent",
                )

            enc_kwargs = _single_reference_kwargs(
                "encounter", payload.encounter, EncounterReferenceType
            )
            if payload.encounter:
                await _validate_ref(
                    session,
                    enc_kwargs["encounter_type"],
                    enc_kwargs["encounter_id"],
                    org_id,
                    "encounter",
                )

            cond_kwargs = _single_reference_kwargs(
                "condition", payload.condition, RiskAssessmentConditionReferenceType
            )
            if payload.condition:
                await _validate_ref(
                    session,
                    cond_kwargs["condition_type"],
                    cond_kwargs["condition_id"],
                    org_id,
                    "condition",
                )

            perf_kwargs = _single_reference_kwargs(
                "performer", payload.performer, RiskAssessmentPerformerReferenceType
            )
            if payload.performer:
                await _validate_ref(
                    session,
                    perf_kwargs["performer_type"],
                    perf_kwargs["performer_id"],
                    org_id,
                    "performer",
                )

            # 2. Instantiate main model
            status_val = (
                RiskAssessmentStatus(payload.status.value)
                if hasattr(payload.status, "value")
                else RiskAssessmentStatus(payload.status)
            )

            model = RiskAssessmentModel(
                tenant_id=org_id,
                created_by=actor_id,
                status=status_val,
                method_text=payload.method.text if payload.method else None,
                code_text=payload.code.text if payload.code else None,
                occurrence_date_time=payload.occurrence_date_time,
                occurrence_period_start=payload.occurrence_period_start,
                occurrence_period_end=payload.occurrence_period_end,
                mitigation=payload.mitigation,
                extension=payload.extension or [],
                **subj_kwargs,
                **based_on_kwargs,
                **parent_kwargs,
                **enc_kwargs,
                **cond_kwargs,
                **perf_kwargs,
            )
            session.add(model)
            await session.flush()

            # 3. Method codings
            if payload.method and payload.method.coding:
                for c in payload.method.coding:
                    session.add(
                        RiskAssessmentMethodCodingModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                        )
                    )

            # 4. Code codings
            if payload.code and payload.code.coding:
                for c in payload.code.coding:
                    session.add(
                        RiskAssessmentCodeCodingModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                        )
                    )

            # 5. Reason codes
            if payload.reason_code:
                for rc in payload.reason_code:
                    rc_m = RiskAssessmentReasonCodeModel(
                        risk_assessment_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        text=rc.text,
                    )
                    session.add(rc_m)
                    await session.flush()
                    if rc.coding:
                        for c in rc.coding:
                            session.add(
                                RiskAssessmentReasonCodeCodingModel(
                                    risk_assessment_reason_code_id=rc_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            # 6. Reason references
            if payload.reason_reference:
                for rr in payload.reason_reference:
                    rr_kwargs = _list_reference_kwargs(
                        rr, RiskAssessmentReasonReferenceType
                    )
                    await _validate_ref(
                        session,
                        rr_kwargs["reference_type"],
                        rr_kwargs["reference_id"],
                        org_id,
                        "reasonReference",
                    )
                    session.add(
                        RiskAssessmentReasonReferenceModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **rr_kwargs,
                        )
                    )

            # 7. Basis
            if payload.basis:
                for b in payload.basis:
                    b_kwargs = _list_reference_kwargs(b, None)
                    await _validate_ref(
                        session,
                        b_kwargs["reference_type"],
                        b_kwargs["reference_id"],
                        org_id,
                        "basis",
                    )
                    session.add(
                        RiskAssessmentBasisModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **b_kwargs,
                        )
                    )

            # 8. Prediction
            if payload.prediction:
                for p in payload.prediction:
                    # extract range fields
                    prob_range = p.probability_range
                    when_range = p.when_range
                    when_period = p.when_period

                    pred_m = RiskAssessmentPredictionModel(
                        risk_assessment_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        outcome_text=p.outcome.text if p.outcome else None,
                        probability_decimal=p.probability_decimal,
                        probability_range_low_value=prob_range.low.value if prob_range and prob_range.low else None,
                        probability_range_low_unit=prob_range.low.unit if prob_range and prob_range.low else None,
                        probability_range_low_system=prob_range.low.system if prob_range and prob_range.low else None,
                        probability_range_low_code=prob_range.low.code if prob_range and prob_range.low else None,
                        probability_range_high_value=prob_range.high.value if prob_range and prob_range.high else None,
                        probability_range_high_unit=prob_range.high.unit if prob_range and prob_range.high else None,
                        probability_range_high_system=prob_range.high.system if prob_range and prob_range.high else None,
                        probability_range_high_code=prob_range.high.code if prob_range and prob_range.high else None,
                        qualitative_risk_text=p.qualitative_risk.text if p.qualitative_risk else None,
                        relative_risk=p.relative_risk,
                        when_period_start=when_period.start if when_period else None,
                        when_period_end=when_period.end if when_period else None,
                        when_range_low_value=when_range.low.value if when_range and when_range.low else None,
                        when_range_low_unit=when_range.low.unit if when_range and when_range.low else None,
                        when_range_low_system=when_range.low.system if when_range and when_range.low else None,
                        when_range_low_code=when_range.low.code if when_range and when_range.low else None,
                        when_range_high_value=when_range.high.value if when_range and when_range.high else None,
                        when_range_high_unit=when_range.high.unit if when_range and when_range.high else None,
                        when_range_high_system=when_range.high.system if when_range and when_range.high else None,
                        when_range_high_code=when_range.high.code if when_range and when_range.high else None,
                        rationale=p.rationale,
                    )
                    session.add(pred_m)
                    await session.flush()

                    if p.outcome and p.outcome.coding:
                        for c in p.outcome.coding:
                            session.add(
                                RiskAssessmentPredOutcomeCodingModel(
                                    risk_assessment_prediction_id=pred_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )
                    if p.qualitative_risk and p.qualitative_risk.coding:
                        for c in p.qualitative_risk.coding:
                            session.add(
                                RiskAssessmentPredQualRiskCodingModel(
                                    risk_assessment_prediction_id=pred_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            # 9. Mitigation
            # (stored directly on model.mitigation)

            # 10. Notes
            if payload.note:
                for n in payload.note:
                    author_type, author_id = None, None
                    if n.author_reference:
                        author_type, author_id = parse_reference(
                            n.author_reference, RiskAssessmentNoteAuthorReferenceType
                        )
                        await _validate_ref(session, author_type, author_id, org_id, "note.author")

                    use_val = (
                        IdentifierUseModel[n.author_identifier_use.name]
                        if n.author_identifier_use and hasattr(n.author_identifier_use, "name")
                        else n.author_identifier_use
                    )

                    session.add(
                        RiskAssessmentNoteModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            author_string=n.author_string,
                            author_reference=n.author_reference,
                            author_type=author_type,
                            author_id=author_id,
                            author_display=n.author_display,
                            author_identifier_use=use_val,
                            author_identifier_type_system=n.author_identifier_type_system,
                            author_identifier_type_version=n.author_identifier_type_version,
                            author_identifier_type_code=n.author_identifier_type_code,
                            author_identifier_type_display=n.author_identifier_type_display,
                            author_identifier_type_user_selected=n.author_identifier_type_user_selected,
                            author_identifier_type_text=n.author_identifier_type_text,
                            author_identifier_system=n.author_identifier_system,
                            author_identifier_value=n.author_identifier_value,
                            author_identifier_period_start=n.author_identifier_period_start,
                            author_identifier_period_end=n.author_identifier_period_end,
                            time=n.time,
                            text=n.text,
                        )
                    )

            # 11. Identifiers
            if payload.identifier:
                for i in payload.identifier:
                    assigner_type, assigner_id = None, None
                    if i.assigner:
                        assigner_type, assigner_id = parse_reference(
                            i.assigner, OrganizationReferenceType
                        )
                        await _validate_ref(
                            session, assigner_type, assigner_id, org_id, "identifier.assigner"
                        )

                    use_val = (
                        IdentifierUseModel[i.use.name]
                        if i.use and hasattr(i.use, "name")
                        else i.use
                    )
                    assigner_use_val = (
                        IdentifierUseModel[i.assigner_identifier_use.name]
                        if i.assigner_identifier_use and hasattr(i.assigner_identifier_use, "name")
                        else i.assigner_identifier_use
                    )

                    ident_m = RiskAssessmentIdentifierModel(
                        risk_assessment_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        use=use_val,
                        type_text=i.type.text if i.type else None,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        assigner_type=assigner_type,
                        assigner_id=assigner_id,
                        assigner_display=i.assigner_display,
                        assigner_identifier_use=assigner_use_val,
                        assigner_identifier_type_system=i.assigner_identifier_type_system,
                        assigner_identifier_type_version=i.assigner_identifier_type_version,
                        assigner_identifier_type_code=i.assigner_identifier_type_code,
                        assigner_identifier_type_display=i.assigner_identifier_type_display,
                        assigner_identifier_type_user_selected=i.assigner_identifier_type_user_selected,
                        assigner_identifier_type_text=i.assigner_identifier_type_text,
                        assigner_identifier_system=i.assigner_identifier_system,
                        assigner_identifier_value=i.assigner_identifier_value,
                        assigner_identifier_period_start=i.assigner_identifier_period_start,
                        assigner_identifier_period_end=i.assigner_identifier_period_end,
                    )
                    session.add(ident_m)
                    await session.flush()

                    if i.type and i.type.coding:
                        for c in i.type.coding:
                            session.add(
                                RiskAssessmentIdentifierTypeCodingModel(
                                    risk_assessment_identifier_id=ident_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            await session.commit()
            return await self.get_by_risk_assessment_id_in_org(
                model.risk_assessment_id, org_id
            )

    async def patch(
        self,
        risk_assessment_id: int,
        payload: RiskAssessmentPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> RiskAssessmentModel | None:
        async with self.session_factory() as session:
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.risk_assessment_id == risk_assessment_id,
                RiskAssessmentModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set
            model.updated_by = actor_id

            if "status" in provided and payload.status is not None:
                status_val = (
                    RiskAssessmentStatus(payload.status.value)
                    if hasattr(payload.status, "value")
                    else RiskAssessmentStatus(payload.status)
                )
                model.status = status_val

            if "subject" in provided:
                subj_kwargs = _single_reference_kwargs(
                    "subject", payload.subject, SubjectReferenceType
                )
                await _validate_ref(
                    session,
                    subj_kwargs["subject_type"],
                    subj_kwargs["subject_id"],
                    org_id,
                    "subject",
                )
                for k, v in subj_kwargs.items():
                    setattr(model, k, v)

            if "based_on" in provided:
                based_on_kwargs = _single_reference_kwargs(
                    "based_on", payload.based_on, None
                )
                if payload.based_on:
                    await _validate_ref(
                        session,
                        based_on_kwargs["based_on_type"],
                        based_on_kwargs["based_on_id"],
                        org_id,
                        "based_on",
                    )
                for k, v in based_on_kwargs.items():
                    setattr(model, k, v)

            if "parent" in provided:
                parent_kwargs = _single_reference_kwargs(
                    "parent", payload.parent, None
                )
                if payload.parent:
                    await _validate_ref(
                        session,
                        parent_kwargs["parent_type"],
                        parent_kwargs["parent_id"],
                        org_id,
                        "parent",
                    )
                for k, v in parent_kwargs.items():
                    setattr(model, k, v)

            if "encounter" in provided:
                enc_kwargs = _single_reference_kwargs(
                    "encounter", payload.encounter, EncounterReferenceType
                )
                if payload.encounter:
                    await _validate_ref(
                        session,
                        enc_kwargs["encounter_type"],
                        enc_kwargs["encounter_id"],
                        org_id,
                        "encounter",
                    )
                for k, v in enc_kwargs.items():
                    setattr(model, k, v)

            if "condition" in provided:
                cond_kwargs = _single_reference_kwargs(
                    "condition", payload.condition, RiskAssessmentConditionReferenceType
                )
                if payload.condition:
                    await _validate_ref(
                        session,
                        cond_kwargs["condition_type"],
                        cond_kwargs["condition_id"],
                        org_id,
                        "condition",
                    )
                for k, v in cond_kwargs.items():
                    setattr(model, k, v)

            if "performer" in provided:
                perf_kwargs = _single_reference_kwargs(
                    "performer", payload.performer, RiskAssessmentPerformerReferenceType
                )
                if payload.performer:
                    await _validate_ref(
                        session,
                        perf_kwargs["performer_type"],
                        perf_kwargs["performer_id"],
                        org_id,
                        "performer",
                    )
                for k, v in perf_kwargs.items():
                    setattr(model, k, v)

            if "occurrence_date_time" in provided:
                model.occurrence_date_time = payload.occurrence_date_time
            if "occurrence_period_start" in provided:
                model.occurrence_period_start = payload.occurrence_period_start
            if "occurrence_period_end" in provided:
                model.occurrence_period_end = payload.occurrence_period_end

            if "mitigation" in provided:
                model.mitigation = payload.mitigation

            if "extension" in provided:
                model.extension = list(payload.extension) if payload.extension is not None else []

            # Method
            if "method" in provided:
                await session.execute(
                    delete(RiskAssessmentMethodCodingModel).where(
                        RiskAssessmentMethodCodingModel.risk_assessment_pk == model.id
                    )
                )
                if payload.method:
                    model.method_text = payload.method.text
                    if payload.method.coding:
                        for c in payload.method.coding:
                            session.add(
                                RiskAssessmentMethodCodingModel(
                                    risk_assessment_pk=model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )
                else:
                    model.method_text = None

            # Code
            if "code" in provided:
                await session.execute(
                    delete(RiskAssessmentCodeCodingModel).where(
                        RiskAssessmentCodeCodingModel.risk_assessment_pk == model.id
                    )
                )
                if payload.code:
                    model.code_text = payload.code.text
                    if payload.code.coding:
                        for c in payload.code.coding:
                            session.add(
                                RiskAssessmentCodeCodingModel(
                                    risk_assessment_pk=model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )
                else:
                    model.code_text = None

            # Reason codes
            if "reason_code" in provided:
                rc_ids = (
                    await session.execute(
                        select(RiskAssessmentReasonCodeModel.id).where(
                            RiskAssessmentReasonCodeModel.risk_assessment_pk == model.id
                        )
                    )
                ).scalars().all()
                if rc_ids:
                    await session.execute(
                        delete(RiskAssessmentReasonCodeCodingModel).where(
                            RiskAssessmentReasonCodeCodingModel.risk_assessment_reason_code_id.in_(rc_ids)
                        )
                    )
                await session.execute(
                    delete(RiskAssessmentReasonCodeModel).where(
                        RiskAssessmentReasonCodeModel.risk_assessment_pk == model.id
                    )
                )
                if payload.reason_code:
                    for rc in payload.reason_code:
                        rc_m = RiskAssessmentReasonCodeModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            text=rc.text,
                        )
                        session.add(rc_m)
                        await session.flush()
                        if rc.coding:
                            for c in rc.coding:
                                session.add(
                                    RiskAssessmentReasonCodeCodingModel(
                                        risk_assessment_reason_code_id=rc_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            # Reason references
            if "reason_reference" in provided:
                await session.execute(
                    delete(RiskAssessmentReasonReferenceModel).where(
                        RiskAssessmentReasonReferenceModel.risk_assessment_pk == model.id
                    )
                )
                if payload.reason_reference:
                    for rr in payload.reason_reference:
                        rr_kwargs = _list_reference_kwargs(
                            rr, RiskAssessmentReasonReferenceType
                        )
                        await _validate_ref(
                            session,
                            rr_kwargs["reference_type"],
                            rr_kwargs["reference_id"],
                            org_id,
                            "reasonReference",
                        )
                        session.add(
                            RiskAssessmentReasonReferenceModel(
                                risk_assessment_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                **rr_kwargs,
                            )
                        )

            # Basis
            if "basis" in provided:
                await session.execute(
                    delete(RiskAssessmentBasisModel).where(
                        RiskAssessmentBasisModel.risk_assessment_pk == model.id
                    )
                )
                if payload.basis:
                    for b in payload.basis:
                        b_kwargs = _list_reference_kwargs(b, None)
                        await _validate_ref(
                            session,
                            b_kwargs["reference_type"],
                            b_kwargs["reference_id"],
                            org_id,
                            "basis",
                        )
                        session.add(
                            RiskAssessmentBasisModel(
                                risk_assessment_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                **b_kwargs,
                            )
                        )

            # Predictions
            if "prediction" in provided:
                pred_ids = (
                    await session.execute(
                        select(RiskAssessmentPredictionModel.id).where(
                            RiskAssessmentPredictionModel.risk_assessment_pk == model.id
                        )
                    )
                ).scalars().all()
                if pred_ids:
                    await session.execute(
                        delete(RiskAssessmentPredOutcomeCodingModel).where(
                            RiskAssessmentPredOutcomeCodingModel.risk_assessment_prediction_id.in_(pred_ids)
                        )
                    )
                    await session.execute(
                        delete(RiskAssessmentPredQualRiskCodingModel).where(
                            RiskAssessmentPredQualRiskCodingModel.risk_assessment_prediction_id.in_(pred_ids)
                        )
                    )
                await session.execute(
                    delete(RiskAssessmentPredictionModel).where(
                        RiskAssessmentPredictionModel.risk_assessment_pk == model.id
                    )
                )
                if payload.prediction:
                    for p in payload.prediction:
                        prob_range = p.probability_range
                        when_range = p.when_range
                        when_period = p.when_period

                        pred_m = RiskAssessmentPredictionModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            outcome_text=p.outcome.text if p.outcome else None,
                            probability_decimal=p.probability_decimal,
                            probability_range_low_value=prob_range.low.value if prob_range and prob_range.low else None,
                            probability_range_low_unit=prob_range.low.unit if prob_range and prob_range.low else None,
                            probability_range_low_system=prob_range.low.system if prob_range and prob_range.low else None,
                            probability_range_low_code=prob_range.low.code if prob_range and prob_range.low else None,
                            probability_range_high_value=prob_range.high.value if prob_range and prob_range.high else None,
                            probability_range_high_unit=prob_range.high.unit if prob_range and prob_range.high else None,
                            probability_range_high_system=prob_range.high.system if prob_range and prob_range.high else None,
                            probability_range_high_code=prob_range.high.code if prob_range and prob_range.high else None,
                            qualitative_risk_text=p.qualitative_risk.text if p.qualitative_risk else None,
                            relative_risk=p.relative_risk,
                            when_period_start=when_period.start if when_period else None,
                            when_period_end=when_period.end if when_period else None,
                            when_range_low_value=when_range.low.value if when_range and when_range.low else None,
                            when_range_low_unit=when_range.low.unit if when_range and when_range.low else None,
                            when_range_low_system=when_range.low.system if when_range and when_range.low else None,
                            when_range_low_code=when_range.low.code if when_range and when_range.low else None,
                            when_range_high_value=when_range.high.value if when_range and when_range.high else None,
                            when_range_high_unit=when_range.high.unit if when_range and when_range.high else None,
                            when_range_high_system=when_range.high.system if when_range and when_range.high else None,
                            when_range_high_code=when_range.high.code if when_range and when_range.high else None,
                            rationale=p.rationale,
                        )
                        session.add(pred_m)
                        await session.flush()

                        if p.outcome and p.outcome.coding:
                            for c in p.outcome.coding:
                                session.add(
                                    RiskAssessmentPredOutcomeCodingModel(
                                        risk_assessment_prediction_id=pred_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )
                        if p.qualitative_risk and p.qualitative_risk.coding:
                            for c in p.qualitative_risk.coding:
                                session.add(
                                    RiskAssessmentPredQualRiskCodingModel(
                                        risk_assessment_prediction_id=pred_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            # Notes
            if "note" in provided:
                await session.execute(
                    delete(RiskAssessmentNoteModel).where(
                        RiskAssessmentNoteModel.risk_assessment_pk == model.id
                    )
                )
                if payload.note:
                    for n in payload.note:
                        author_type, author_id = None, None
                        if n.author_reference:
                            author_type, author_id = parse_reference(
                                n.author_reference, RiskAssessmentNoteAuthorReferenceType
                            )
                            await _validate_ref(session, author_type, author_id, org_id, "note.author")

                        use_val = (
                            IdentifierUseModel[n.author_identifier_use.name]
                            if n.author_identifier_use and hasattr(n.author_identifier_use, "name")
                            else n.author_identifier_use
                        )

                        session.add(
                            RiskAssessmentNoteModel(
                                risk_assessment_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                author_string=n.author_string,
                                author_reference=n.author_reference,
                                author_type=author_type,
                                author_id=author_id,
                                author_display=n.author_display,
                                author_identifier_use=use_val,
                                author_identifier_type_system=n.author_identifier_type_system,
                                author_identifier_type_version=n.author_identifier_type_version,
                                author_identifier_type_code=n.author_identifier_type_code,
                                author_identifier_type_display=n.author_identifier_type_display,
                                author_identifier_type_user_selected=n.author_identifier_type_user_selected,
                                author_identifier_type_text=n.author_identifier_type_text,
                                author_identifier_system=n.author_identifier_system,
                                author_identifier_value=n.author_identifier_value,
                                author_identifier_period_start=n.author_identifier_period_start,
                                author_identifier_period_end=n.author_identifier_period_end,
                                time=n.time,
                                text=n.text,
                            )
                        )

            # Identifiers
            if "identifier" in provided:
                id_ids = (
                    await session.execute(
                        select(RiskAssessmentIdentifierModel.id).where(
                            RiskAssessmentIdentifierModel.risk_assessment_pk == model.id
                        )
                    )
                ).scalars().all()
                if id_ids:
                    await session.execute(
                        delete(RiskAssessmentIdentifierTypeCodingModel).where(
                            RiskAssessmentIdentifierTypeCodingModel.risk_assessment_identifier_id.in_(id_ids)
                        )
                    )
                await session.execute(
                    delete(RiskAssessmentIdentifierModel).where(
                        RiskAssessmentIdentifierModel.risk_assessment_pk == model.id
                    )
                )
                if payload.identifier:
                    for i in payload.identifier:
                        assigner_type, assigner_id = None, None
                        if i.assigner:
                            assigner_type, assigner_id = parse_reference(
                                i.assigner, OrganizationReferenceType
                            )
                            await _validate_ref(
                                session, assigner_type, assigner_id, org_id, "identifier.assigner"
                            )

                        use_val = (
                            IdentifierUseModel[i.use.name]
                            if i.use and hasattr(i.use, "name")
                            else i.use
                        )
                        assigner_use_val = (
                            IdentifierUseModel[i.assigner_identifier_use.name]
                            if i.assigner_identifier_use and hasattr(i.assigner_identifier_use, "name")
                            else i.assigner_identifier_use
                        )

                        ident_m = RiskAssessmentIdentifierModel(
                            risk_assessment_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            use=use_val,
                            type_text=i.type.text if i.type else None,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            assigner_reference=i.assigner,
                            assigner_type=assigner_type,
                            assigner_id=assigner_id,
                            assigner_display=i.assigner_display,
                            assigner_identifier_use=assigner_use_val,
                            assigner_identifier_type_system=i.assigner_identifier_type_system,
                            assigner_identifier_type_version=i.assigner_identifier_type_version,
                            assigner_identifier_type_code=i.assigner_identifier_type_code,
                            assigner_identifier_type_display=i.assigner_identifier_type_display,
                            assigner_identifier_type_user_selected=i.assigner_identifier_type_user_selected,
                            assigner_identifier_type_text=i.assigner_identifier_type_text,
                            assigner_identifier_system=i.assigner_identifier_system,
                            assigner_identifier_value=i.assigner_identifier_value,
                            assigner_identifier_period_start=i.assigner_identifier_period_start,
                            assigner_identifier_period_end=i.assigner_identifier_period_end,
                        )
                        session.add(ident_m)
                        await session.flush()

                        if i.type and i.type.coding:
                            for c in i.type.coding:
                                session.add(
                                    RiskAssessmentIdentifierTypeCodingModel(
                                        risk_assessment_identifier_id=ident_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            await session.commit()
            return await self.get_by_risk_assessment_id_in_org(
                risk_assessment_id, org_id
            )

    create_full = create
    patch_full = patch

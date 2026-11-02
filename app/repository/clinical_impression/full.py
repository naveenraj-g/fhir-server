from sqlalchemy import delete, select

from app.core.filters import parse_reference
from app.core.logging import get_logger
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.models.clinical_impression import (
    ClinicalImpressionAssessorReferenceType,
    ClinicalImpressionCodeCodingModel,
    ClinicalImpressionFindingItemCodingModel,
    ClinicalImpressionFindingModel,
    ClinicalImpressionFindingReferenceType,
    ClinicalImpressionIdentifierModel,
    ClinicalImpressionIdentifierTypeCodingModel,
    ClinicalImpressionInvestigationCodeCodingModel,
    ClinicalImpressionInvestigationItemModel,
    ClinicalImpressionInvestigationModel,
    ClinicalImpressionModel,
    ClinicalImpressionNoteAuthorReferenceType,
    ClinicalImpressionNoteModel,
    ClinicalImpressionPreviousReferenceType,
    ClinicalImpressionProblemModel,
    ClinicalImpressionProblemReferenceType,
    ClinicalImpressionPrognosisCodeableConceptModel,
    ClinicalImpressionPrognosisCodingModel,
    ClinicalImpressionPrognosisReferenceModel,
    ClinicalImpressionPrognosisReferenceType,
    ClinicalImpressionProtocolModel,
    ClinicalImpressionStatus,
    ClinicalImpressionStatusReasonCodingModel,
    ClinicalImpressionSupportingInfoModel,
)
from app.schemas.clinical_impression import (
    ClinicalImpressionCreateSchema,
    ClinicalImpressionPatchSchema,
)

from ._shared import (
    _list_reference_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)


class _FullMixin:
    """Atomic full Create & Patch operations for ClinicalImpression."""

    async def create(
        self,
        payload: ClinicalImpressionCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> ClinicalImpressionModel:
        async with self.session_factory() as session:
            # 1. References validation
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

            assessor_kwargs = _single_reference_kwargs(
                "assessor", payload.assessor, ClinicalImpressionAssessorReferenceType
            )
            if payload.assessor:
                await _validate_ref(
                    session,
                    assessor_kwargs["assessor_type"],
                    assessor_kwargs["assessor_id"],
                    org_id,
                    "assessor",
                )

            previous_kwargs = _single_reference_kwargs(
                "previous", payload.previous, ClinicalImpressionPreviousReferenceType
            )
            if payload.previous:
                await _validate_ref(
                    session,
                    previous_kwargs["previous_type"],
                    previous_kwargs["previous_id"],
                    org_id,
                    "previous",
                )

            # 2. Instantiate main model
            status_val = (
                ClinicalImpressionStatus(payload.status.value)
                if hasattr(payload.status, "value")
                else ClinicalImpressionStatus(payload.status)
            )

            model = ClinicalImpressionModel(
                tenant_id=org_id,
                created_by=actor_id,
                status=status_val,
                status_reason_text=payload.status_reason.text if payload.status_reason else None,
                code_text=payload.code.text if payload.code else None,
                description=payload.description,
                effective_date_time=payload.effective_date_time,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                date=payload.date,
                summary=payload.summary,
                extension=payload.extension or [],
                **subj_kwargs,
                **enc_kwargs,
                **assessor_kwargs,
                **previous_kwargs,
            )
            session.add(model)
            await session.flush()

            # 3. StatusReason codings
            if payload.status_reason and payload.status_reason.coding:
                for c in payload.status_reason.coding:
                    session.add(
                        ClinicalImpressionStatusReasonCodingModel(
                            clinical_impression_pk=model.id,
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
                        ClinicalImpressionCodeCodingModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                        )
                    )

            # 5. Problem
            if payload.problem:
                for p in payload.problem:
                    prob_kwargs = _list_reference_kwargs(
                        p, ClinicalImpressionProblemReferenceType, prefix="problem"
                    )
                    await _validate_ref(
                        session,
                        prob_kwargs["problem_type"],
                        prob_kwargs["problem_id"],
                        org_id,
                        "problem",
                    )
                    session.add(
                        ClinicalImpressionProblemModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **prob_kwargs,
                        )
                    )

            # 6. Investigation
            if payload.investigation:
                for inv in payload.investigation:
                    inv_m = ClinicalImpressionInvestigationModel(
                        clinical_impression_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        code_text=inv.code.text if inv.code else None,
                    )
                    session.add(inv_m)
                    await session.flush()

                    if inv.code and inv.code.coding:
                        for c in inv.code.coding:
                            session.add(
                                ClinicalImpressionInvestigationCodeCodingModel(
                                    clinical_impression_investigation_id=inv_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

                    if inv.item:
                        for it in inv.item:
                            it_kwargs = _list_reference_kwargs(it, None, prefix="item")
                            await _validate_ref(
                                session,
                                it_kwargs["item_type"],
                                it_kwargs["item_id"],
                                org_id,
                                "investigation.item",
                            )
                            session.add(
                                ClinicalImpressionInvestigationItemModel(
                                    clinical_impression_investigation_id=inv_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    **it_kwargs,
                                )
                            )

            # 7. Protocol
            if payload.protocol:
                for pr in payload.protocol:
                    session.add(
                        ClinicalImpressionProtocolModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            uri=pr,
                        )
                    )

            # 8. Finding
            if payload.finding:
                for f in payload.finding:
                    f_kwargs = _list_reference_kwargs(
                        f.item_reference,
                        ClinicalImpressionFindingReferenceType,
                        prefix="item_reference",
                    ) if f.item_reference else {
                        "item_reference": None,
                        "item_reference_type": None,
                        "item_reference_id": None,
                        "item_reference_display": None,
                    }
                    if f.item_reference:
                        await _validate_ref(
                            session,
                            f_kwargs["item_reference_type"],
                            f_kwargs["item_reference_id"],
                            org_id,
                            "finding.itemReference",
                        )

                    find_m = ClinicalImpressionFindingModel(
                        clinical_impression_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        item_codeable_concept_text=f.item_codeable_concept.text if f.item_codeable_concept else None,
                        basis=f.basis,
                        **f_kwargs,
                    )
                    session.add(find_m)
                    await session.flush()

                    if f.item_codeable_concept and f.item_codeable_concept.coding:
                        for c in f.item_codeable_concept.coding:
                            session.add(
                                ClinicalImpressionFindingItemCodingModel(
                                    clinical_impression_finding_id=find_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            # 9. PrognosisCodeableConcept
            if payload.prognosis_codeable_concept:
                for p in payload.prognosis_codeable_concept:
                    prog_m = ClinicalImpressionPrognosisCodeableConceptModel(
                        clinical_impression_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        text=p.text,
                    )
                    session.add(prog_m)
                    await session.flush()

                    if p.coding:
                        for c in p.coding:
                            session.add(
                                ClinicalImpressionPrognosisCodingModel(
                                    clinical_impression_prognosis_id=prog_m.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            # 10. PrognosisReference
            if payload.prognosis_reference:
                for pr in payload.prognosis_reference:
                    pr_kwargs = _list_reference_kwargs(
                        pr, ClinicalImpressionPrognosisReferenceType, prefix="reference"
                    )
                    await _validate_ref(
                        session,
                        pr_kwargs["reference_type"],
                        pr_kwargs["reference_id"],
                        org_id,
                        "prognosisReference",
                    )
                    session.add(
                        ClinicalImpressionPrognosisReferenceModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **pr_kwargs,
                        )
                    )

            # 11. SupportingInfo
            if payload.supporting_info:
                for si in payload.supporting_info:
                    si_kwargs = _list_reference_kwargs(si, None, prefix="reference")
                    await _validate_ref(
                        session,
                        si_kwargs["reference_type"],
                        si_kwargs["reference_id"],
                        org_id,
                        "supportingInfo",
                    )
                    session.add(
                        ClinicalImpressionSupportingInfoModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **si_kwargs,
                        )
                    )

            # 12. Notes
            if payload.note:
                for n in payload.note:
                    author_type, author_id = None, None
                    if n.author_reference:
                        author_type, author_id = parse_reference(
                            n.author_reference, ClinicalImpressionNoteAuthorReferenceType
                        )
                        await _validate_ref(session, author_type, author_id, org_id, "note.author")

                    use_val = (
                        IdentifierUseModel[n.author_identifier_use.name]
                        if n.author_identifier_use and hasattr(n.author_identifier_use, "name")
                        else n.author_identifier_use
                    )

                    session.add(
                        ClinicalImpressionNoteModel(
                            clinical_impression_pk=model.id,
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

            # 13. Identifiers
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

                    ident_m = ClinicalImpressionIdentifierModel(
                        clinical_impression_pk=model.id,
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
                                ClinicalImpressionIdentifierTypeCodingModel(
                                    clinical_impression_identifier_id=ident_m.id,
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
            return await self.get_by_clinical_impression_id_in_org(
                model.clinical_impression_id, org_id
            )

    async def patch(
        self,
        clinical_impression_id: int,
        payload: ClinicalImpressionPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> ClinicalImpressionModel | None:
        async with self.session_factory() as session:
            stmt = select(ClinicalImpressionModel).where(
                ClinicalImpressionModel.clinical_impression_id == clinical_impression_id,
                ClinicalImpressionModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set
            model.updated_by = actor_id

            if "status" in provided and payload.status is not None:
                status_val = (
                    ClinicalImpressionStatus(payload.status.value)
                    if hasattr(payload.status, "value")
                    else ClinicalImpressionStatus(payload.status)
                )
                model.status = status_val

            if "description" in provided:
                model.description = payload.description

            if "summary" in provided:
                model.summary = payload.summary

            if "date" in provided:
                model.date = payload.date

            if "effective_date_time" in provided:
                model.effective_date_time = payload.effective_date_time
            if "effective_period_start" in provided:
                model.effective_period_start = payload.effective_period_start
            if "effective_period_end" in provided:
                model.effective_period_end = payload.effective_period_end

            if "extension" in provided:
                model.extension = payload.extension or []

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

            if "assessor" in provided:
                assessor_kwargs = _single_reference_kwargs(
                    "assessor", payload.assessor, ClinicalImpressionAssessorReferenceType
                )
                if payload.assessor:
                    await _validate_ref(
                        session,
                        assessor_kwargs["assessor_type"],
                        assessor_kwargs["assessor_id"],
                        org_id,
                        "assessor",
                    )
                for k, v in assessor_kwargs.items():
                    setattr(model, k, v)

            if "previous" in provided:
                previous_kwargs = _single_reference_kwargs(
                    "previous", payload.previous, ClinicalImpressionPreviousReferenceType
                )
                if payload.previous:
                    await _validate_ref(
                        session,
                        previous_kwargs["previous_type"],
                        previous_kwargs["previous_id"],
                        org_id,
                        "previous",
                    )
                for k, v in previous_kwargs.items():
                    setattr(model, k, v)

            # Status reason
            if "status_reason" in provided:
                await session.execute(
                    delete(ClinicalImpressionStatusReasonCodingModel).where(
                        ClinicalImpressionStatusReasonCodingModel.clinical_impression_pk == model.id
                    )
                )
                if payload.status_reason:
                    model.status_reason_text = payload.status_reason.text
                    if payload.status_reason.coding:
                        for c in payload.status_reason.coding:
                            session.add(
                                ClinicalImpressionStatusReasonCodingModel(
                                    clinical_impression_pk=model.id,
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
                    model.status_reason_text = None

            # Code
            if "code" in provided:
                await session.execute(
                    delete(ClinicalImpressionCodeCodingModel).where(
                        ClinicalImpressionCodeCodingModel.clinical_impression_pk == model.id
                    )
                )
                if payload.code:
                    model.code_text = payload.code.text
                    if payload.code.coding:
                        for c in payload.code.coding:
                            session.add(
                                ClinicalImpressionCodeCodingModel(
                                    clinical_impression_pk=model.id,
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

            # Problems
            if "problem" in provided:
                await session.execute(
                    delete(ClinicalImpressionProblemModel).where(
                        ClinicalImpressionProblemModel.clinical_impression_pk == model.id
                    )
                )
                if payload.problem:
                    for p in payload.problem:
                        prob_kwargs = _list_reference_kwargs(
                            p, ClinicalImpressionProblemReferenceType, prefix="problem"
                        )
                        await _validate_ref(
                            session,
                            prob_kwargs["problem_type"],
                            prob_kwargs["problem_id"],
                            org_id,
                            "problem",
                        )
                        session.add(
                            ClinicalImpressionProblemModel(
                                clinical_impression_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                **prob_kwargs,
                            )
                        )

            # Investigations
            if "investigation" in provided:
                inv_ids = (
                    await session.execute(
                        select(ClinicalImpressionInvestigationModel.id).where(
                            ClinicalImpressionInvestigationModel.clinical_impression_pk == model.id
                        )
                    )
                ).scalars().all()
                if inv_ids:
                    await session.execute(
                        delete(ClinicalImpressionInvestigationCodeCodingModel).where(
                            ClinicalImpressionInvestigationCodeCodingModel.clinical_impression_investigation_id.in_(inv_ids)
                        )
                    )
                    await session.execute(
                        delete(ClinicalImpressionInvestigationItemModel).where(
                            ClinicalImpressionInvestigationItemModel.clinical_impression_investigation_id.in_(inv_ids)
                        )
                    )
                await session.execute(
                    delete(ClinicalImpressionInvestigationModel).where(
                        ClinicalImpressionInvestigationModel.clinical_impression_pk == model.id
                    )
                )
                if payload.investigation:
                    for inv in payload.investigation:
                        inv_m = ClinicalImpressionInvestigationModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            code_text=inv.code.text if inv.code else None,
                        )
                        session.add(inv_m)
                        await session.flush()

                        if inv.code and inv.code.coding:
                            for c in inv.code.coding:
                                session.add(
                                    ClinicalImpressionInvestigationCodeCodingModel(
                                        clinical_impression_investigation_id=inv_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

                        if inv.item:
                            for it in inv.item:
                                it_kwargs = _list_reference_kwargs(it, None, prefix="item")
                                await _validate_ref(
                                    session,
                                    it_kwargs["item_type"],
                                    it_kwargs["item_id"],
                                    org_id,
                                    "investigation.item",
                                )
                                session.add(
                                    ClinicalImpressionInvestigationItemModel(
                                        clinical_impression_investigation_id=inv_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        **it_kwargs,
                                    )
                                )

            # Protocol
            if "protocol" in provided:
                await session.execute(
                    delete(ClinicalImpressionProtocolModel).where(
                        ClinicalImpressionProtocolModel.clinical_impression_pk == model.id
                    )
                )
                if payload.protocol:
                    for pr in payload.protocol:
                        session.add(
                            ClinicalImpressionProtocolModel(
                                clinical_impression_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                uri=pr,
                            )
                        )

            # Finding
            if "finding" in provided:
                find_ids = (
                    await session.execute(
                        select(ClinicalImpressionFindingModel.id).where(
                            ClinicalImpressionFindingModel.clinical_impression_pk == model.id
                        )
                    )
                ).scalars().all()
                if find_ids:
                    await session.execute(
                        delete(ClinicalImpressionFindingItemCodingModel).where(
                            ClinicalImpressionFindingItemCodingModel.clinical_impression_finding_id.in_(find_ids)
                        )
                    )
                await session.execute(
                    delete(ClinicalImpressionFindingModel).where(
                        ClinicalImpressionFindingModel.clinical_impression_pk == model.id
                    )
                )
                if payload.finding:
                    for f in payload.finding:
                        f_kwargs = _list_reference_kwargs(
                            f.item_reference,
                            ClinicalImpressionFindingReferenceType,
                            prefix="item_reference",
                        ) if f.item_reference else {
                            "item_reference": None,
                            "item_reference_type": None,
                            "item_reference_id": None,
                            "item_reference_display": None,
                        }
                        if f.item_reference:
                            await _validate_ref(
                                session,
                                f_kwargs["item_reference_type"],
                                f_kwargs["item_reference_id"],
                                org_id,
                                "finding.itemReference",
                            )

                        find_m = ClinicalImpressionFindingModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            item_codeable_concept_text=f.item_codeable_concept.text if f.item_codeable_concept else None,
                            basis=f.basis,
                            **f_kwargs,
                        )
                        session.add(find_m)
                        await session.flush()

                        if f.item_codeable_concept and f.item_codeable_concept.coding:
                            for c in f.item_codeable_concept.coding:
                                session.add(
                                    ClinicalImpressionFindingItemCodingModel(
                                        clinical_impression_finding_id=find_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            # PrognosisCodeableConcept
            if "prognosis_codeable_concept" in provided:
                prog_cc_ids = (
                    await session.execute(
                        select(ClinicalImpressionPrognosisCodeableConceptModel.id).where(
                            ClinicalImpressionPrognosisCodeableConceptModel.clinical_impression_pk == model.id
                        )
                    )
                ).scalars().all()
                if prog_cc_ids:
                    await session.execute(
                        delete(ClinicalImpressionPrognosisCodingModel).where(
                            ClinicalImpressionPrognosisCodingModel.clinical_impression_prognosis_id.in_(prog_cc_ids)
                        )
                    )
                await session.execute(
                    delete(ClinicalImpressionPrognosisCodeableConceptModel).where(
                        ClinicalImpressionPrognosisCodeableConceptModel.clinical_impression_pk == model.id
                    )
                )
                if payload.prognosis_codeable_concept:
                    for p in payload.prognosis_codeable_concept:
                        prog_m = ClinicalImpressionPrognosisCodeableConceptModel(
                            clinical_impression_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            text=p.text,
                        )
                        session.add(prog_m)
                        await session.flush()

                        if p.coding:
                            for c in p.coding:
                                session.add(
                                    ClinicalImpressionPrognosisCodingModel(
                                        clinical_impression_prognosis_id=prog_m.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            # PrognosisReference
            if "prognosis_reference" in provided:
                await session.execute(
                    delete(ClinicalImpressionPrognosisReferenceModel).where(
                        ClinicalImpressionPrognosisReferenceModel.clinical_impression_pk == model.id
                    )
                )
                if payload.prognosis_reference:
                    for pr in payload.prognosis_reference:
                        pr_kwargs = _list_reference_kwargs(
                            pr, ClinicalImpressionPrognosisReferenceType, prefix="reference"
                        )
                        await _validate_ref(
                            session,
                            pr_kwargs["reference_type"],
                            pr_kwargs["reference_id"],
                            org_id,
                            "prognosisReference",
                        )
                        session.add(
                            ClinicalImpressionPrognosisReferenceModel(
                                clinical_impression_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                **pr_kwargs,
                            )
                        )

            # SupportingInfo
            if "supporting_info" in provided:
                await session.execute(
                    delete(ClinicalImpressionSupportingInfoModel).where(
                        ClinicalImpressionSupportingInfoModel.clinical_impression_pk == model.id
                    )
                )
                if payload.supporting_info:
                    for si in payload.supporting_info:
                        si_kwargs = _list_reference_kwargs(si, None, prefix="reference")
                        await _validate_ref(
                            session,
                            si_kwargs["reference_type"],
                            si_kwargs["reference_id"],
                            org_id,
                            "supportingInfo",
                        )
                        session.add(
                            ClinicalImpressionSupportingInfoModel(
                                clinical_impression_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                **si_kwargs,
                            )
                        )

            # Notes
            if "note" in provided:
                await session.execute(
                    delete(ClinicalImpressionNoteModel).where(
                        ClinicalImpressionNoteModel.clinical_impression_pk == model.id
                    )
                )
                if payload.note:
                    for n in payload.note:
                        author_type, author_id = None, None
                        if n.author_reference:
                            author_type, author_id = parse_reference(
                                n.author_reference, ClinicalImpressionNoteAuthorReferenceType
                            )
                            await _validate_ref(session, author_type, author_id, org_id, "note.author")

                        use_val = (
                            IdentifierUseModel[n.author_identifier_use.name]
                            if n.author_identifier_use and hasattr(n.author_identifier_use, "name")
                            else n.author_identifier_use
                        )

                        session.add(
                            ClinicalImpressionNoteModel(
                                clinical_impression_pk=model.id,
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
                        select(ClinicalImpressionIdentifierModel.id).where(
                            ClinicalImpressionIdentifierModel.clinical_impression_pk == model.id
                        )
                    )
                ).scalars().all()
                if id_ids:
                    await session.execute(
                        delete(ClinicalImpressionIdentifierTypeCodingModel).where(
                            ClinicalImpressionIdentifierTypeCodingModel.clinical_impression_identifier_id.in_(id_ids)
                        )
                    )
                await session.execute(
                    delete(ClinicalImpressionIdentifierModel).where(
                        ClinicalImpressionIdentifierModel.clinical_impression_pk == model.id
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

                        ident_m = ClinicalImpressionIdentifierModel(
                            clinical_impression_pk=model.id,
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
                                    ClinicalImpressionIdentifierTypeCodingModel(
                                        clinical_impression_identifier_id=ident_m.id,
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
            return await self.get_by_clinical_impression_id_in_org(
                clinical_impression_id, org_id
            )

    create_full = create
    patch_full = patch

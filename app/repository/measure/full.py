from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.datatypes import fhir_enum
from app.models.enums import (
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
)
from app.schemas.enums import ContactPointSystem, ContactPointUse
from app.models.measure import (
    MeasureCompositeScoringCoding,
    MeasureContact,
    MeasureContactRole,
    MeasureContactTelecom,
    MeasureGroup,
    MeasureGroupCodeCoding,
    MeasureGroupPopulation,
    MeasureGroupPopulationCodeCoding,
    MeasureGroupStratifier,
    MeasureGroupStratifierCodeCoding,
    MeasureGroupStratifierComponent,
    MeasureGroupStratifierComponentCodeCoding,
    MeasureIdentifier,
    MeasureIdentifierTypeCoding,
    MeasureImprovementNotationCoding,
    MeasureJurisdiction,
    MeasureJurisdictionCoding,
    MeasureModel,
    MeasureQuantityComparator,
    MeasureRelatedArtifact,
    MeasureRelatedArtifactType,
    MeasureScoringCoding,
    MeasureStatus,
    MeasureSubjectCoding,
    MeasureSubjectReferenceType,
    MeasureSupplementalData,
    MeasureSupplementalDataCodeCoding,
    MeasureSupplementalDataUsage,
    MeasureSupplementalDataUsageCoding,
    MeasureTopic,
    MeasureTopicCoding,
    MeasureType,
    MeasureTypeCoding,
    MeasureUseContext,
    MeasureUseContextValueCoding,
    MeasureUseContextValueReferenceType,
)
from app.schemas.measure import (
    MeasureCreateSchema,
    MeasurePatchSchema,
)

from ._shared import (
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _build_identifiers(identifiers, org_id: str, actor_id: str) -> list[MeasureIdentifier]:
    res = []
    for ident in identifiers or []:
        ass_ref = getattr(ident, "assigner", None) or getattr(ident, "assigner_reference", None)
        if not ass_ref and getattr(ident, "assigner_type", None) and getattr(ident, "assigner_id", None):
            ass_ref = f"{fhir_enum(ident.assigner_type)}/{ident.assigner_id}"
        ass_kwargs = _single_reference_kwargs(
            "assigner", ass_ref, OrganizationReferenceType
        )
        if getattr(ident, "assigner_display", None):
            ass_kwargs["assigner_display"] = ident.assigner_display

        type_codings = []
        tc_list = getattr(ident, "type_coding", None) or getattr(ident, "type_codings", None) or []
        for tc in tc_list:
            type_codings.append(
                MeasureIdentifierTypeCoding(
                    system=tc.system,
                    version=tc.version,
                    code=tc.code,
                    display=tc.display,
                    user_selected=tc.user_selected,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        mi = MeasureIdentifier(
            use=(
                IdentifierUseModel(ident.use.value if hasattr(ident.use, "value") else str(ident.use))
                if ident.use
                else None
            ),
            type_text=ident.type_text,
            type_codings=type_codings,
            system=ident.system,
            value=ident.value,
            period_start=ident.period_start,
            period_end=ident.period_end,
            tenant_id=org_id,
            created_by=actor_id,
            updated_by=actor_id,
            **ass_kwargs,
        )
        res.append(mi)
    return res


def _build_subject_codings(subject_cc, org_id: str, actor_id: str) -> list[MeasureSubjectCoding]:
    res = []
    if subject_cc and subject_cc.coding:
        for c in subject_cc.coding:
            res.append(
                MeasureSubjectCoding(
                    system=c.system,
                    version=c.version,
                    code=c.code,
                    display=c.display,
                    user_selected=c.user_selected,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
    return res


def _build_contacts(contacts, role: str, org_id: str, actor_id: str) -> list[MeasureContact]:
    res = []
    for c in contacts or []:
        telecoms = []
        t_list = getattr(c, "telecom", None) or getattr(c, "telecoms", None) or []
        for t in t_list:
            telecoms.append(
                MeasureContactTelecom(
                    system=(
                        ContactPointSystem(t.system.value if hasattr(t.system, "value") else str(t.system))
                        if t.system
                        else None
                    ),
                    value=t.value,
                    use=(
                        ContactPointUse(t.use.value if hasattr(t.use, "value") else str(t.use))
                        if t.use
                        else None
                    ),
                    rank=t.rank,
                    period_start=t.period_start,
                    period_end=t.period_end,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        mc = MeasureContact(
            role=MeasureContactRole(role),
            name=c.name,
            telecoms=telecoms,
            tenant_id=org_id,
            created_by=actor_id,
            updated_by=actor_id,
        )
        res.append(mc)
    return res


def _build_use_contexts(use_contexts, org_id: str, actor_id: str) -> list[MeasureUseContext]:
    res = []
    for uc in use_contexts or []:
        v_codings = []
        c_list = getattr(uc, "value_codeable_concept_coding", None) or getattr(uc, "value_codings", None) or []
        for c in c_list:
            v_codings.append(
                MeasureUseContextValueCoding(
                    system=c.system,
                    version=c.version,
                    code=c.code,
                    display=c.display,
                    user_selected=c.user_selected,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        v_ref = uc.value_reference
        if not v_ref and getattr(uc, "value_reference_type", None) and getattr(uc, "value_reference_id", None):
            v_ref = f"{fhir_enum(uc.value_reference_type)}/{uc.value_reference_id}"
        val_ref_kwargs = _single_reference_kwargs(
            "value_reference", v_ref, MeasureUseContextValueReferenceType
        )
        if uc.value_reference_display:
            val_ref_kwargs["value_reference_display"] = uc.value_reference_display

        muc = MeasureUseContext(
            system=uc.code_system,
            version=uc.code_version,
            code=uc.code_code,
            display=uc.code_display,
            user_selected=uc.code_user_selected,
            value_codeable_concept_text=uc.value_codeable_concept_text,
            value_codings=v_codings,
            value_quantity_value=uc.value_quantity_value,
            value_quantity_comparator=(
                MeasureQuantityComparator(
                    uc.value_quantity_comparator.value
                    if hasattr(uc.value_quantity_comparator, "value")
                    else str(uc.value_quantity_comparator)
                )
                if uc.value_quantity_comparator
                else None
            ),
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
            tenant_id=org_id,
            created_by=actor_id,
            updated_by=actor_id,
            **val_ref_kwargs,
        )
        res.append(muc)
    return res


def _build_jurisdictions(items, org_id: str, actor_id: str) -> list[MeasureJurisdiction]:
    res = []
    for item in items or []:
        codings = [
            MeasureJurisdictionCoding(
                system=c.system,
                version=c.version,
                code=c.code,
                display=c.display,
                user_selected=c.user_selected,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
            for c in (item.coding or [])
        ]
        res.append(
            MeasureJurisdiction(
                text=item.text,
                codings=codings,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    return res


def _build_topics(items, org_id: str, actor_id: str) -> list[MeasureTopic]:
    res = []
    for item in items or []:
        codings = [
            MeasureTopicCoding(
                system=c.system,
                version=c.version,
                code=c.code,
                display=c.display,
                user_selected=c.user_selected,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
            for c in (item.coding or [])
        ]
        res.append(
            MeasureTopic(
                text=item.text,
                codings=codings,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    return res


def _build_types(items, org_id: str, actor_id: str) -> list[MeasureType]:
    res = []
    for item in items or []:
        codings = [
            MeasureTypeCoding(
                system=c.system,
                version=c.version,
                code=c.code,
                display=c.display,
                user_selected=c.user_selected,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
            for c in (item.coding or [])
        ]
        res.append(
            MeasureType(
                text=item.text,
                codings=codings,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    return res


def _build_related_artifacts(items, org_id: str, actor_id: str) -> list[MeasureRelatedArtifact]:
    res = []
    for ra in items or []:
        res.append(
            MeasureRelatedArtifact(
                type=MeasureRelatedArtifactType(
                    ra.type.value if hasattr(ra.type, "value") else str(ra.type)
                ),
                label=ra.label,
                display=ra.display,
                citation=ra.citation,
                url=ra.url,
                document=ra.document,
                resource=ra.resource,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    return res


def _build_single_concept_codings(cc, coding_cls, org_id: str, actor_id: str):
    res = []
    if cc and cc.coding:
        for c in cc.coding:
            res.append(
                coding_cls(
                    system=c.system,
                    version=c.version,
                    code=c.code,
                    display=c.display,
                    user_selected=c.user_selected,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
    return res


def _build_groups(groups, org_id: str, actor_id: str) -> list[MeasureGroup]:
    res = []
    for g in groups or []:
        g_codings = []
        if g.code and g.code.coding:
            for c in g.code.coding:
                g_codings.append(
                    MeasureGroupCodeCoding(
                        system=c.system,
                        version=c.version,
                        code=c.code,
                        display=c.display,
                        user_selected=c.user_selected,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )

        pops = []
        for p in g.population or []:
            p_codings = []
            if p.code and p.code.coding:
                for c in p.code.coding:
                    p_codings.append(
                        MeasureGroupPopulationCodeCoding(
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                        )
                    )
            pops.append(
                MeasureGroupPopulation(
                    code_text=p.code.text if p.code else None,
                    code_codings=p_codings,
                    description=p.description,
                    criteria_description=p.criteria.description if p.criteria else None,
                    criteria_name=p.criteria.name if p.criteria else None,
                    criteria_language=p.criteria.language if p.criteria else None,
                    criteria_expression=p.criteria.expression if p.criteria else None,
                    criteria_reference=p.criteria.reference if p.criteria else None,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        strats = []
        for s in g.stratifier or []:
            s_codings = []
            if s.code and s.code.coding:
                for c in s.code.coding:
                    s_codings.append(
                        MeasureGroupStratifierCodeCoding(
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                        )
                    )
            comps = []
            for comp in s.component or []:
                comp_codings = []
                if comp.code and comp.code.coding:
                    for c in comp.code.coding:
                        comp_codings.append(
                            MeasureGroupStratifierComponentCodeCoding(
                                system=c.system,
                                version=c.version,
                                code=c.code,
                                display=c.display,
                                user_selected=c.user_selected,
                                tenant_id=org_id,
                                created_by=actor_id,
                                updated_by=actor_id,
                            )
                        )
                comps.append(
                    MeasureGroupStratifierComponent(
                        code_text=comp.code.text if comp.code else None,
                        code_codings=comp_codings,
                        description=comp.description,
                        criteria_description=comp.criteria.description if comp.criteria else None,
                        criteria_name=comp.criteria.name if comp.criteria else None,
                        criteria_language=comp.criteria.language if comp.criteria else None,
                        criteria_expression=comp.criteria.expression if comp.criteria else None,
                        criteria_reference=comp.criteria.reference if comp.criteria else None,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )
            strats.append(
                MeasureGroupStratifier(
                    code_text=s.code.text if s.code else None,
                    code_codings=s_codings,
                    description=s.description,
                    criteria_description=s.criteria.description if s.criteria else None,
                    criteria_name=s.criteria.name if s.criteria else None,
                    criteria_language=s.criteria.language if s.criteria else None,
                    criteria_expression=s.criteria.expression if s.criteria else None,
                    criteria_reference=s.criteria.reference if s.criteria else None,
                    components=comps,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        mg = MeasureGroup(
            code_text=g.code.text if g.code else None,
            code_codings=g_codings,
            description=g.description,
            populations=pops,
            stratifiers=strats,
            tenant_id=org_id,
            created_by=actor_id,
            updated_by=actor_id,
        )
        res.append(mg)
    return res


def _build_supplemental_data(supp_data, org_id: str, actor_id: str) -> list[MeasureSupplementalData]:
    res = []
    for sd in supp_data or []:
        sd_codings = []
        if sd.code and sd.code.coding:
            for c in sd.code.coding:
                sd_codings.append(
                    MeasureSupplementalDataCodeCoding(
                        system=c.system,
                        version=c.version,
                        code=c.code,
                        display=c.display,
                        user_selected=c.user_selected,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )
        usages = []
        for u in sd.usage or []:
            u_codings = []
            if u.coding:
                for c in u.coding:
                    u_codings.append(
                        MeasureSupplementalDataUsageCoding(
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                        )
                    )
            usages.append(
                MeasureSupplementalDataUsage(
                    text=u.text,
                    codings=u_codings,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        msd = MeasureSupplementalData(
            code_text=sd.code.text if sd.code else None,
            code_codings=sd_codings,
            usages=usages,
            description=sd.description,
            criteria_description=sd.criteria.description if sd.criteria else None,
            criteria_name=sd.criteria.name if sd.criteria else None,
            criteria_language=sd.criteria.language if sd.criteria else None,
            criteria_expression=sd.criteria.expression if sd.criteria else None,
            criteria_reference=sd.criteria.reference if sd.criteria else None,
            tenant_id=org_id,
            created_by=actor_id,
            updated_by=actor_id,
        )
        res.append(msd)
    return res


class _FullMixin:
    """Atomic full Create & Patch operations for Measure."""

    async def create(
        self,
        payload: MeasureCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> MeasureModel:
        async with self.session_factory() as session:
            # 1. References validation
            subject_kwargs = _single_reference_kwargs(
                "subject", payload.subject_reference, MeasureSubjectReferenceType
            )
            if payload.subject_reference_display:
                subject_kwargs["subject_display"] = payload.subject_reference_display
            if payload.subject_reference:
                await _validate_ref(
                    session,
                    subject_kwargs["subject_type"],
                    subject_kwargs["subject_id"],
                    org_id,
                    "subject_reference",
                )

            if payload.identifier:
                for ident in payload.identifier:
                    assigner_ref = getattr(ident, "assigner", None) or getattr(ident, "assigner_reference", None)
                    if not assigner_ref and getattr(ident, "assigner_type", None) and getattr(ident, "assigner_id", None):
                        assigner_ref = f"{fhir_enum(ident.assigner_type)}/{ident.assigner_id}"
                    if assigner_ref:
                        ass_kwargs = _single_reference_kwargs(
                            "assigner", assigner_ref, OrganizationReferenceType
                        )
                        await _validate_ref(
                            session,
                            ass_kwargs["assigner_type"],
                            ass_kwargs["assigner_id"],
                            org_id,
                            "identifier.assigner",
                        )

            if payload.use_context:
                for uc in payload.use_context:
                    v_ref = uc.value_reference
                    if not v_ref and getattr(uc, "value_reference_type", None) and getattr(uc, "value_reference_id", None):
                        v_ref = f"{fhir_enum(uc.value_reference_type)}/{uc.value_reference_id}"
                    if v_ref:
                        v_kwargs = _single_reference_kwargs(
                            "value_reference", v_ref, MeasureUseContextValueReferenceType
                        )
                        await _validate_ref(
                            session,
                            v_kwargs["value_reference_type"],
                            v_kwargs["value_reference_id"],
                            org_id,
                            "use_context.value_reference",
                        )

            # 2. Build model
            model = MeasureModel(
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                extension=list(payload.extension) if payload.extension else None,
                url=payload.url,
                version=payload.version,
                name=payload.name,
                title=payload.title,
                subtitle=payload.subtitle,
                status=MeasureStatus(
                    payload.status.value if hasattr(payload.status, "value") else str(payload.status)
                ),
                experimental=payload.experimental,
                subject_codeable_concept_text=(
                    payload.subject_codeable_concept.text if payload.subject_codeable_concept else None
                ),
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
                library=list(payload.library) if payload.library else None,
                disclaimer=payload.disclaimer,
                scoring_text=payload.scoring.text if payload.scoring else None,
                composite_scoring_text=(
                    payload.composite_scoring.text if payload.composite_scoring else None
                ),
                risk_adjustment=payload.risk_adjustment,
                rate_aggregation=payload.rate_aggregation,
                rationale=payload.rationale,
                clinical_recommendation_statement=payload.clinical_recommendation_statement,
                improvement_notation_text=(
                    payload.improvement_notation.text if payload.improvement_notation else None
                ),
                definition=list(payload.definition) if payload.definition else None,
                guidance=payload.guidance,
                **subject_kwargs,
            )

            # 3. Attach children
            model.identifiers = _build_identifiers(payload.identifier, org_id, actor_id)
            model.subject_codings = _build_subject_codings(
                payload.subject_codeable_concept, org_id, actor_id
            )

            contacts = []
            for role_name in ("contact", "author", "editor", "reviewer", "endorser"):
                contacts.extend(
                    _build_contacts(getattr(payload, role_name), role_name, org_id, actor_id)
                )
            model.contacts = contacts

            model.use_contexts = _build_use_contexts(payload.use_context, org_id, actor_id)
            model.jurisdictions = _build_jurisdictions(payload.jurisdiction, org_id, actor_id)
            model.topics = _build_topics(payload.topic, org_id, actor_id)
            model.types = _build_types(payload.type, org_id, actor_id)
            model.related_artifacts = _build_related_artifacts(
                payload.related_artifact, org_id, actor_id
            )
            model.scoring_codings = _build_single_concept_codings(
                payload.scoring, MeasureScoringCoding, org_id, actor_id
            )
            model.composite_scoring_codings = _build_single_concept_codings(
                payload.composite_scoring, MeasureCompositeScoringCoding, org_id, actor_id
            )
            model.improvement_notation_codings = _build_single_concept_codings(
                payload.improvement_notation, MeasureImprovementNotationCoding, org_id, actor_id
            )
            model.groups = _build_groups(payload.group, org_id, actor_id)
            model.supplemental_data = _build_supplemental_data(
                payload.supplemental_data, org_id, actor_id
            )

            session.add(model)
            await session.commit()
            await session.refresh(model)
            res_id = model.measure_id

        return await self.get_by_measure_id(res_id)

    async def patch(
        self,
        measure_id: int,
        payload: MeasurePatchSchema,
        org_id: str,
        actor_id: str,
    ) -> MeasureModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureModel).where(
                    MeasureModel.measure_id == measure_id,
                    MeasureModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set

            # Scalars
            if "extension" in provided:
                model.extension = list(payload.extension) if payload.extension else None
            if "url" in provided:
                model.url = payload.url
            if "version" in provided:
                model.version = payload.version
            if "name" in provided:
                model.name = payload.name
            if "title" in provided:
                model.title = payload.title
            if "subtitle" in provided:
                model.subtitle = payload.subtitle
            if "status" in provided:
                model.status = (
                    MeasureStatus(
                        payload.status.value if hasattr(payload.status, "value") else str(payload.status)
                    )
                    if payload.status
                    else None
                )
            if "experimental" in provided:
                model.experimental = payload.experimental
            if "date" in provided:
                model.date = payload.date
            if "publisher" in provided:
                model.publisher = payload.publisher
            if "description" in provided:
                model.description = payload.description
            if "purpose" in provided:
                model.purpose = payload.purpose
            if "usage" in provided:
                model.usage = payload.usage
            if "copyright" in provided:
                model.copyright = payload.copyright
            if "approval_date" in provided:
                model.approval_date = payload.approval_date
            if "last_review_date" in provided:
                model.last_review_date = payload.last_review_date
            if "effective_period_start" in provided:
                model.effective_period_start = payload.effective_period_start
            if "effective_period_end" in provided:
                model.effective_period_end = payload.effective_period_end
            if "library" in provided:
                model.library = list(payload.library) if payload.library else None
            if "disclaimer" in provided:
                model.disclaimer = payload.disclaimer
            if "risk_adjustment" in provided:
                model.risk_adjustment = payload.risk_adjustment
            if "rate_aggregation" in provided:
                model.rate_aggregation = payload.rate_aggregation
            if "rationale" in provided:
                model.rationale = payload.rationale
            if "clinical_recommendation_statement" in provided:
                model.clinical_recommendation_statement = payload.clinical_recommendation_statement
            if "definition" in provided:
                model.definition = list(payload.definition) if payload.definition else None
            if "guidance" in provided:
                model.guidance = payload.guidance

            # subject[x]
            if "subject_codeable_concept" in provided:
                scc = payload.subject_codeable_concept
                model.subject_codeable_concept_text = scc.text if scc else None
                model.subject_codings = _build_subject_codings(scc, org_id, actor_id)
                if scc:
                    model.subject_reference = None
                    model.subject_type = None
                    model.subject_id = None
                    model.subject_display = None
            elif "subject_reference" in provided:
                s_ref = payload.subject_reference
                s_kwargs = _single_reference_kwargs(
                    "subject", s_ref, MeasureSubjectReferenceType
                )
                if "subject_reference_display" in provided:
                    s_kwargs["subject_display"] = payload.subject_reference_display
                if s_ref:
                    await _validate_ref(
                        session,
                        s_kwargs["subject_type"],
                        s_kwargs["subject_id"],
                        org_id,
                        "subject_reference",
                    )
                    model.subject_codeable_concept_text = None
                    model.subject_codings = []
                for k, v in s_kwargs.items():
                    setattr(model, k, v)

            # scoring
            if "scoring" in provided:
                model.scoring_text = payload.scoring.text if payload.scoring else None
                model.scoring_codings = _build_single_concept_codings(
                    payload.scoring, MeasureScoringCoding, org_id, actor_id
                )

            # composite_scoring
            if "composite_scoring" in provided:
                model.composite_scoring_text = (
                    payload.composite_scoring.text if payload.composite_scoring else None
                )
                model.composite_scoring_codings = _build_single_concept_codings(
                    payload.composite_scoring, MeasureCompositeScoringCoding, org_id, actor_id
                )

            # improvement_notation
            if "improvement_notation" in provided:
                model.improvement_notation_text = (
                    payload.improvement_notation.text if payload.improvement_notation else None
                )
                model.improvement_notation_codings = _build_single_concept_codings(
                    payload.improvement_notation, MeasureImprovementNotationCoding, org_id, actor_id
                )

            # Collections
            if "identifier" in provided:
                if payload.identifier:
                    for ident in payload.identifier:
                        assigner_ref = getattr(ident, "assigner", None) or getattr(ident, "assigner_reference", None)
                        if not assigner_ref and getattr(ident, "assigner_type", None) and getattr(ident, "assigner_id", None):
                            assigner_ref = f"{fhir_enum(ident.assigner_type)}/{ident.assigner_id}"
                        if assigner_ref:
                            ass_kwargs = _single_reference_kwargs(
                                "assigner", assigner_ref, OrganizationReferenceType
                            )
                            await _validate_ref(
                                session,
                                ass_kwargs["assigner_type"],
                                ass_kwargs["assigner_id"],
                                org_id,
                                "identifier.assigner",
                            )
                model.identifiers = _build_identifiers(payload.identifier, org_id, actor_id)

            for role_name in ("contact", "author", "editor", "reviewer", "endorser"):
                if role_name in provided:
                    new_contacts = _build_contacts(
                        getattr(payload, role_name), role_name, org_id, actor_id
                    )
                    kept_contacts = [
                        c
                        for c in (model.contacts or [])
                        if (c.role.value if hasattr(c.role, "value") else str(c.role))
                        != role_name
                    ]
                    model.contacts = kept_contacts + new_contacts

            if "use_context" in provided:
                if payload.use_context:
                    for uc in payload.use_context:
                        v_ref = uc.value_reference
                        if not v_ref and getattr(uc, "value_reference_type", None) and getattr(uc, "value_reference_id", None):
                            v_ref = f"{fhir_enum(uc.value_reference_type)}/{uc.value_reference_id}"
                        if v_ref:
                            v_kwargs = _single_reference_kwargs(
                                "value_reference", v_ref, MeasureUseContextValueReferenceType
                            )
                            await _validate_ref(
                                session,
                                v_kwargs["value_reference_type"],
                                v_kwargs["value_reference_id"],
                                org_id,
                                "use_context.value_reference",
                            )
                model.use_contexts = _build_use_contexts(payload.use_context, org_id, actor_id)

            if "jurisdiction" in provided:
                model.jurisdictions = _build_jurisdictions(
                    payload.jurisdiction, org_id, actor_id
                )
            if "topic" in provided:
                model.topics = _build_topics(payload.topic, org_id, actor_id)
            if "type" in provided:
                model.types = _build_types(payload.type, org_id, actor_id)
            if "related_artifact" in provided:
                model.related_artifacts = _build_related_artifacts(
                    payload.related_artifact, org_id, actor_id
                )
            if "group" in provided:
                model.groups = _build_groups(payload.group, org_id, actor_id)
            if "supplemental_data" in provided:
                model.supplemental_data = _build_supplemental_data(
                    payload.supplemental_data, org_id, actor_id
                )

            model.updated_by = actor_id
            await session.commit()
            await session.refresh(model)
            res_id = model.measure_id

        return await self.get_by_measure_id(res_id)

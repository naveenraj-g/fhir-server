from typing import Any

from sqlalchemy.future import select

from app.core.logging import get_logger
from app.fhir.datatypes import fhir_enum
from app.models.enums import (
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
)
from app.models.measure_report import (
    MeasureReportEvaluatedResource,
    MeasureReportGroup,
    MeasureReportGroupCodeCoding,
    MeasureReportGroupPopulation,
    MeasureReportGroupPopulationCodeCoding,
    MeasureReportGroupStratifier,
    MeasureReportGroupStratifierCode,
    MeasureReportGroupStratifierCodeCoding,
    MeasureReportGroupStratifierStratum,
    MeasureReportGroupStratifierStratumComponent,
    MeasureReportGroupStratifierStratumComponentCodeCoding,
    MeasureReportGroupStratifierStratumComponentValueCoding,
    MeasureReportGroupStratifierStratumPopulation,
    MeasureReportGroupStratifierStratumPopulationCodeCoding,
    MeasureReportGroupStratifierStratumValueCoding,
    MeasureReportIdentifier,
    MeasureReportIdentifierTypeCoding,
    MeasureReportImprovementNotationCoding,
    MeasureReportModel,
    MeasureReportQuantityComparator,
    MeasureReportReporterReferenceType,
    MeasureReportStatus,
    MeasureReportSubjectReferenceType,
    MeasureReportSubjectResultsReferenceType,
    MeasureReportType,
)
from app.schemas.measure_report import (
    MeasureReportCreateSchema,
    MeasureReportPatchSchema,
)

from ._shared import (
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _parse_comparator(val: Any) -> MeasureReportQuantityComparator | None:
    if not val:
        return None
    v = val.value if hasattr(val, "value") else str(val)
    try:
        return MeasureReportQuantityComparator(v)
    except (ValueError, KeyError):
        return MeasureReportQuantityComparator[v]


def _build_identifiers(identifiers, org_id: str, actor_id: str) -> list[MeasureReportIdentifier]:
    res = []
    for ident in identifiers or []:
        ass_kwargs = _single_reference_kwargs(
            "assigner", getattr(ident, "assigner", None), OrganizationReferenceType
        )
        if getattr(ident, "assigner_display", None):
            ass_kwargs["assigner_display"] = ident.assigner_display

        type_codings = []
        tc_list = getattr(ident, "type_coding", None) or getattr(ident, "type_codings", None) or []
        for tc in tc_list:
            type_codings.append(
                MeasureReportIdentifierTypeCoding(
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

        mi = MeasureReportIdentifier(
            use=(
                IdentifierUseModel(ident.use.value if hasattr(ident.use, "value") else str(ident.use))
                if ident.use
                else None
            ),
            type_text=ident.type_text,
            type_coding=type_codings,
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


def _build_improvement_notation_codings(
    codings, org_id: str, actor_id: str
) -> list[MeasureReportImprovementNotationCoding]:
    res = []
    for c in codings or []:
        res.append(
            MeasureReportImprovementNotationCoding(
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


def _build_evaluated_resources(
    evaluated_resources, org_id: str, actor_id: str
) -> list[MeasureReportEvaluatedResource]:
    res = []
    for er in evaluated_resources or []:
        er_kwargs = _single_reference_kwargs("evaluated_resource", er, None)
        res.append(
            MeasureReportEvaluatedResource(
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                **er_kwargs,
            )
        )
    return res


def _build_groups(groups, org_id: str, actor_id: str) -> list[MeasureReportGroup]:
    res = []
    for g in groups or []:
        g_codings = []
        tc_list = getattr(g, "code_coding", None) or getattr(g, "code_codings", None) or []
        for c in tc_list:
            g_codings.append(
                MeasureReportGroupCodeCoding(
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
        for p in getattr(g, "population", None) or []:
            p_codings = []
            ptc_list = getattr(p, "code_coding", None) or getattr(p, "code_codings", None) or []
            for c in ptc_list:
                p_codings.append(
                    MeasureReportGroupPopulationCodeCoding(
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
            sr_kwargs = _single_reference_kwargs(
                "subject_results", p, MeasureReportSubjectResultsReferenceType
            )
            pops.append(
                MeasureReportGroupPopulation(
                    code_text=p.code_text,
                    code_coding=p_codings,
                    count=p.count,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                    **sr_kwargs,
                )
            )

        strats = []
        for s in getattr(g, "stratifier", None) or []:
            codes = []
            for sc in getattr(s, "code", None) or []:
                s_codings = []
                stc_list = getattr(sc, "coding", None) or getattr(sc, "codings", None) or []
                for c in stc_list:
                    s_codings.append(
                        MeasureReportGroupStratifierCodeCoding(
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
                codes.append(
                    MeasureReportGroupStratifierCode(
                        code_text=sc.text,
                        coding=s_codings,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )

            strata = []
            for stratum in getattr(s, "stratum", None) or []:
                v_codings = []
                vtc_list = (
                    getattr(stratum, "value_coding", None)
                    or getattr(stratum, "value_codings", None)
                    or []
                )
                for c in vtc_list:
                    v_codings.append(
                        MeasureReportGroupStratifierStratumValueCoding(
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
                for comp in getattr(stratum, "component", None) or []:
                    c_code_codings = []
                    for c in (
                        getattr(comp, "code_coding", None)
                        or getattr(comp, "code_codings", None)
                        or []
                    ):
                        c_code_codings.append(
                            MeasureReportGroupStratifierStratumComponentCodeCoding(
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
                    c_val_codings = []
                    for c in (
                        getattr(comp, "value_coding", None)
                        or getattr(comp, "value_codings", None)
                        or []
                    ):
                        c_val_codings.append(
                            MeasureReportGroupStratifierStratumComponentValueCoding(
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
                        MeasureReportGroupStratifierStratumComponent(
                            code_text=comp.code_text,
                            code_coding=c_code_codings,
                            value_text=comp.value_text,
                            value_coding=c_val_codings,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                        )
                    )

                strat_pops = []
                for sp in getattr(stratum, "population", None) or []:
                    sp_codings = []
                    for c in (
                        getattr(sp, "code_coding", None)
                        or getattr(sp, "code_codings", None)
                        or []
                    ):
                        sp_codings.append(
                            MeasureReportGroupStratifierStratumPopulationCodeCoding(
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
                    sp_sr_kwargs = _single_reference_kwargs(
                        "subject_results", sp, MeasureReportSubjectResultsReferenceType
                    )
                    strat_pops.append(
                        MeasureReportGroupStratifierStratumPopulation(
                            code_text=sp.code_text,
                            code_coding=sp_codings,
                            count=sp.count,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                            **sp_sr_kwargs,
                        )
                    )

                strata.append(
                    MeasureReportGroupStratifierStratum(
                        value_text=stratum.value_text,
                        value_coding=v_codings,
                        components=comps,
                        populations=strat_pops,
                        measure_score_value=stratum.measure_score_value,
                        measure_score_comparator=_parse_comparator(
                            stratum.measure_score_comparator
                        ),
                        measure_score_unit=stratum.measure_score_unit,
                        measure_score_system=stratum.measure_score_system,
                        measure_score_code=stratum.measure_score_code,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )

            strats.append(
                MeasureReportGroupStratifier(
                    codes=codes,
                    strata=strata,
                    tenant_id=org_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        res.append(
            MeasureReportGroup(
                code_text=g.code_text,
                code_coding=g_codings,
                populations=pops,
                measure_score_value=g.measure_score_value,
                measure_score_comparator=_parse_comparator(g.measure_score_comparator),
                measure_score_unit=g.measure_score_unit,
                measure_score_system=g.measure_score_system,
                measure_score_code=g.measure_score_code,
                stratifiers=strats,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    return res


class _FullMixin:
    """Write (create/patch) operations for MeasureReport."""

    async def create(
        self,
        payload: MeasureReportCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> MeasureReportModel:
        async with self.session_factory() as session:
            subj_kwargs = _single_reference_kwargs(
                "subject", payload, MeasureReportSubjectReferenceType
            )
            await _validate_ref(
                session,
                subj_kwargs.get("subject_type"),
                subj_kwargs.get("subject_id"),
                org_id,
                "subject",
            )

            rep_kwargs = _single_reference_kwargs(
                "reporter", payload, MeasureReportReporterReferenceType
            )
            await _validate_ref(
                session,
                rep_kwargs.get("reporter_type"),
                rep_kwargs.get("reporter_id"),
                org_id,
                "reporter",
            )

            for ident in payload.identifier or []:
                if ident.assigner:
                    ass_kwargs = _single_reference_kwargs(
                        "assigner", ident.assigner, OrganizationReferenceType
                    )
                    await _validate_ref(
                        session,
                        ass_kwargs.get("assigner_type"),
                        ass_kwargs.get("assigner_id"),
                        org_id,
                        "identifier.assigner",
                    )

            for er in payload.evaluated_resource or []:
                er_kwargs = _single_reference_kwargs("evaluated_resource", er, None)
                await _validate_ref(
                    session,
                    er_kwargs.get("evaluated_resource_type"),
                    er_kwargs.get("evaluated_resource_id"),
                    org_id,
                    "evaluated_resource",
                )

            for g in payload.group or []:
                for p in g.population or []:
                    if p.subject_results:
                        sr_kwargs = _single_reference_kwargs(
                            "subject_results", p, MeasureReportSubjectResultsReferenceType
                        )
                        await _validate_ref(
                            session,
                            sr_kwargs.get("subject_results_type"),
                            sr_kwargs.get("subject_results_id"),
                            org_id,
                            "group.population.subject_results",
                        )

            status_val = (
                payload.status.value
                if hasattr(payload.status, "value")
                else str(payload.status)
            )
            type_val = (
                payload.type.value
                if hasattr(payload.type, "value")
                else str(payload.type)
            )

            model = MeasureReportModel(
                status=MeasureReportStatus(status_val),
                type=MeasureReportType(type_val),
                measure=payload.measure,
                date=payload.date,
                period_start=payload.period_start,
                period_end=payload.period_end,
                improvement_notation_text=payload.improvement_notation_text,
                extension=payload.extension or [],
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                **subj_kwargs,
                **rep_kwargs,
                identifiers=_build_identifiers(payload.identifier, org_id, actor_id),
                improvement_notation_coding=_build_improvement_notation_codings(
                    payload.improvement_notation_coding, org_id, actor_id
                ),
                evaluated_resources=_build_evaluated_resources(
                    payload.evaluated_resource, org_id, actor_id
                ),
                groups=_build_groups(payload.group, org_id, actor_id),
            )

            session.add(model)
            await session.commit()
            return await self.get_by_measure_report_id_in_org(
                model.measure_report_id, org_id
            )

    async def patch(
        self,
        measure_report_id: int,
        payload: MeasureReportPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> MeasureReportModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MeasureReportModel).where(
                    MeasureReportModel.measure_report_id == measure_report_id,
                    MeasureReportModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set and payload.status is not None:
                val = (
                    payload.status.value
                    if hasattr(payload.status, "value")
                    else str(payload.status)
                )
                model.status = MeasureReportStatus(val)

            if "type" in fields_set and payload.type is not None:
                val = (
                    payload.type.value
                    if hasattr(payload.type, "value")
                    else str(payload.type)
                )
                model.type = MeasureReportType(val)

            if "measure" in fields_set and payload.measure is not None:
                model.measure = payload.measure

            if "date" in fields_set:
                model.date = payload.date

            if "period_start" in fields_set:
                model.period_start = payload.period_start

            if "period_end" in fields_set:
                model.period_end = payload.period_end

            if "improvement_notation_text" in fields_set:
                model.improvement_notation_text = payload.improvement_notation_text

            if "extension" in fields_set:
                model.extension = payload.extension or []

            subject_fields = {
                "subject",
                "subject_display",
                "subject_identifier_use",
                "subject_identifier_type_system",
                "subject_identifier_type_version",
                "subject_identifier_type_code",
                "subject_identifier_type_display",
                "subject_identifier_type_user_selected",
                "subject_identifier_type_text",
                "subject_identifier_system",
                "subject_identifier_value",
                "subject_identifier_period_start",
                "subject_identifier_period_end",
            }
            if fields_set & subject_fields:
                subj_kwargs = _single_reference_kwargs(
                    "subject", payload, MeasureReportSubjectReferenceType
                )
                await _validate_ref(
                    session,
                    subj_kwargs.get("subject_type"),
                    subj_kwargs.get("subject_id"),
                    org_id,
                    "subject",
                )
                for k, v in subj_kwargs.items():
                    setattr(model, k, v)

            reporter_fields = {
                "reporter",
                "reporter_display",
                "reporter_identifier_use",
                "reporter_identifier_type_system",
                "reporter_identifier_type_version",
                "reporter_identifier_type_code",
                "reporter_identifier_type_display",
                "reporter_identifier_type_user_selected",
                "reporter_identifier_type_text",
                "reporter_identifier_system",
                "reporter_identifier_value",
                "reporter_identifier_period_start",
                "reporter_identifier_period_end",
            }
            if fields_set & reporter_fields:
                rep_kwargs = _single_reference_kwargs(
                    "reporter", payload, MeasureReportReporterReferenceType
                )
                await _validate_ref(
                    session,
                    rep_kwargs.get("reporter_type"),
                    rep_kwargs.get("reporter_id"),
                    org_id,
                    "reporter",
                )
                for k, v in rep_kwargs.items():
                    setattr(model, k, v)

            if "improvement_notation_coding" in fields_set:
                model.improvement_notation_coding.clear()
                for item in _build_improvement_notation_codings(
                    payload.improvement_notation_coding, org_id, actor_id
                ):
                    model.improvement_notation_coding.append(item)

            if "identifier" in fields_set:
                model.identifiers.clear()
                for item in _build_identifiers(payload.identifier, org_id, actor_id):
                    model.identifiers.append(item)

            if "evaluated_resource" in fields_set:
                model.evaluated_resources.clear()
                for item in _build_evaluated_resources(
                    payload.evaluated_resource, org_id, actor_id
                ):
                    model.evaluated_resources.append(item)

            if "group" in fields_set:
                model.groups.clear()
                for item in _build_groups(payload.group, org_id, actor_id):
                    model.groups.append(item)

            model.updated_by = actor_id
            await session.commit()
            return await self.get_by_measure_report_id_in_org(
                measure_report_id, org_id
            )

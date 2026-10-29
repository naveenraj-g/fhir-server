from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import EncounterReferenceType, ObservationReferenceType
from app.models.diagnostic_report import (
    DiagnosticReportActorReferenceType,
    DiagnosticReportBasedOn,
    DiagnosticReportBasedOnReferenceType,
    DiagnosticReportCategory,
    DiagnosticReportCategoryCoding,
    DiagnosticReportCodeCoding,
    DiagnosticReportConclusionCode,
    DiagnosticReportConclusionCodeCoding,
    DiagnosticReportIdentifier,
    DiagnosticReportIdentifierTypeCoding,
    DiagnosticReportImagingStudy,
    DiagnosticReportImagingStudyReferenceType,
    DiagnosticReportMedia,
    DiagnosticReportMediaLinkReferenceType,
    DiagnosticReportModel,
    DiagnosticReportPerformer,
    DiagnosticReportPresentedForm,
    DiagnosticReportResult,
    DiagnosticReportResultsInterpreter,
    DiagnosticReportSpecimen,
    DiagnosticReportSpecimenReferenceType,
    DiagnosticReportStatus as DiagnosticReportStatusModel,
    DiagnosticReportSubjectReferenceType,
)
from app.schemas.diagnostic_report import DiagnosticReportCreateSchema, DiagnosticReportPatchSchema

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _MODELED_ACTOR_TYPES,
    _MODELED_BASED_ON_TYPES,
    _MODELED_SUBJECT_TYPES,
    _org_ref_kwargs,
    _parse_org_ref,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)

_SUB = {
    "identifier", "based_on", "category", "performer", "results_interpreter",
    "specimen", "result", "imaging_study", "media", "conclusion_code", "presented_form",
}
_SINGLE_OBJECT_FIELDS = {"subject", "encounter"}
_EFFECTIVE_FIELDS = {"effective_date_time", "effective_period_start", "effective_period_end"}
_SPECIAL = {"status", "code"} | _SINGLE_OBJECT_FIELDS | _EFFECTIVE_FIELDS


def _model_status(v) -> DiagnosticReportStatusModel:
    return DiagnosticReportStatusModel[v.name]


def _coding_kwargs(coding, created_by: str | None) -> dict:
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _identifier_kwargs_for(i, prefix: str = "") -> dict:
    a_type, a_id = (_parse_org_ref(i.assigner) if i and i.assigner else (None, None))
    p = prefix
    return {
        f"{p}use": i.use if i else None,
        f"{p}type_text": i.type_text if i else None,
        f"{p}system": i.system if i else None,
        f"{p}value": i.value if i else None,
        f"{p}period_start": i.period_start if i else None,
        f"{p}period_end": i.period_end if i else None,
        f"{p}assigner_reference": i.assigner if i else None,
        f"{p}assigner_type": a_type,
        f"{p}assigner_id": a_id,
        f"{p}assigner_display": i.assigner_display if i else None,
        f"{p}assigner_identifier_use": i.assigner_identifier_use if i else None,
        f"{p}assigner_identifier_type_system": i.assigner_identifier_type_system if i else None,
        f"{p}assigner_identifier_type_version": i.assigner_identifier_type_version if i else None,
        f"{p}assigner_identifier_type_code": i.assigner_identifier_type_code if i else None,
        f"{p}assigner_identifier_type_display": i.assigner_identifier_type_display if i else None,
        f"{p}assigner_identifier_type_text": i.assigner_identifier_type_text if i else None,
        f"{p}assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected if i else None,
        f"{p}assigner_identifier_system": i.assigner_identifier_system if i else None,
        f"{p}assigner_identifier_value": i.assigner_identifier_value if i else None,
        f"{p}assigner_identifier_period_start": i.assigner_identifier_period_start if i else None,
        f"{p}assigner_identifier_period_end": i.assigner_identifier_period_end if i else None,
    }


def _list_reference_kwargs(obj, enum_cls) -> dict:
    kwargs = {
        "reference_reference": obj.reference,
        **_ref_kwargs("reference", obj.reference, obj.reference_display, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"reference_{suffix}"] = getattr(obj, f"reference_{suffix}")
    return kwargs


def _media_link_kwargs(m) -> dict:
    kwargs = {
        "link_reference": m.link_reference,
        **_ref_kwargs("link", m.link_reference, m.link_display, DiagnosticReportMediaLinkReferenceType),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"link_{suffix}"] = getattr(m, f"link_{suffix}")
    return kwargs


def _presented_form_kwargs(a) -> dict:
    return {
        "content_type": a.content_type,
        "language": a.language,
        "data": a.data,
        "url": a.url,
        "size": a.size,
        "hash": a.hash,
        "title": a.title,
        "creation": a.creation,
    }


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(self, payload: DiagnosticReportCreateSchema) -> DiagnosticReportModel:
        async with self.session_factory() as session:
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, DiagnosticReportSubjectReferenceType)
            encounter_kwargs = _single_reference_kwargs("encounter", payload.encounter, EncounterReferenceType)

            await _validate_ref(session, payload.tenant_id, "subject", subject_kwargs["subject_type"], subject_kwargs["subject_id"], _MODELED_SUBJECT_TYPES)
            await _validate_ref(session, payload.tenant_id, "encounter", encounter_kwargs["encounter_type"], encounter_kwargs["encounter_id"], None)

            dr = DiagnosticReportModel(
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                created_by=payload.created_by,
                extension=payload.extension or [],
                status=_model_status(payload.status),
                code_text=payload.code.text if payload.code else None,
                **subject_kwargs,
                **encounter_kwargs,
                effective_date_time=payload.effective_date_time,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                issued=payload.issued,
                conclusion=payload.conclusion,
            )
            session.add(dr)
            await session.flush()

            for coding in (payload.code.coding if payload.code else None) or []:
                session.add(DiagnosticReportCodeCoding(diagnostic_report_pk=dr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))

            await self._insert_sub_resources(session, dr.id, payload, payload.tenant_id, payload.created_by)

            try:
                await session.commit()
                await session.refresh(dr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_diagnostic_report_id(dr.diagnostic_report_id)

    async def _insert_sub_resources(self, session, dr_pk: int, payload, tenant_id: str, created_by: str | None) -> None:
        for i in payload.identifier or []:
            a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
            identifier = DiagnosticReportIdentifier(
                diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by,
                use=i.use, type_text=i.type_text, system=i.system, value=i.value,
                period_start=i.period_start, period_end=i.period_end,
                assigner_reference=i.assigner, assigner_type=a_type, assigner_id=a_id, assigner_display=i.assigner_display,
                **{f"assigner_{s}": getattr(i, f"assigner_{s}") for s in _IDENTIFIER_FALLBACK_SUFFIXES},
            )
            session.add(identifier)
            if i.type_coding:
                await session.flush()
                for coding in i.type_coding:
                    session.add(DiagnosticReportIdentifierTypeCoding(diagnostic_report_identifier_id=identifier.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for b in payload.based_on or []:
            kwargs = _list_reference_kwargs(b, DiagnosticReportBasedOnReferenceType)
            await _validate_ref(session, tenant_id, "basedOn", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_BASED_ON_TYPES)
            session.add(DiagnosticReportBasedOn(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for c in payload.category or []:
            category = DiagnosticReportCategory(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, text=c.text)
            session.add(category)
            if c.coding:
                await session.flush()
                for coding in c.coding:
                    session.add(DiagnosticReportCategoryCoding(diagnostic_report_category_id=category.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for p in payload.performer or []:
            kwargs = _list_reference_kwargs(p, DiagnosticReportActorReferenceType)
            await _validate_ref(session, tenant_id, "performer", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_ACTOR_TYPES)
            session.add(DiagnosticReportPerformer(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for r in payload.results_interpreter or []:
            kwargs = _list_reference_kwargs(r, DiagnosticReportActorReferenceType)
            await _validate_ref(session, tenant_id, "resultsInterpreter", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_ACTOR_TYPES)
            session.add(DiagnosticReportResultsInterpreter(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for s in payload.specimen or []:
            session.add(DiagnosticReportSpecimen(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(s, DiagnosticReportSpecimenReferenceType)))

        for r in payload.result or []:
            kwargs = _list_reference_kwargs(r, ObservationReferenceType)
            await _validate_ref(session, tenant_id, "result", kwargs.get("reference_type"), kwargs.get("reference_id"), None)
            session.add(DiagnosticReportResult(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for i in payload.imaging_study or []:
            session.add(DiagnosticReportImagingStudy(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(i, DiagnosticReportImagingStudyReferenceType)))

        for m in payload.media or []:
            session.add(DiagnosticReportMedia(
                diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by,
                comment=m.comment, **_media_link_kwargs(m),
            ))

        if payload.conclusion_code:
            for cc in payload.conclusion_code:
                conclusion_code = DiagnosticReportConclusionCode(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, text=cc.text)
                session.add(conclusion_code)
                if cc.coding:
                    await session.flush()
                    for coding in cc.coding:
                        session.add(DiagnosticReportConclusionCodeCoding(diagnostic_report_conclusion_code_id=conclusion_code.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for a in payload.presented_form or []:
            session.add(DiagnosticReportPresentedForm(diagnostic_report_pk=dr_pk, tenant_id=tenant_id, created_by=created_by, **_presented_form_kwargs(a)))

    async def patch_full(self, diagnostic_report_id: int, payload: DiagnosticReportPatchSchema) -> DiagnosticReportModel | None:
        async with self.session_factory() as session:
            stmt = select(DiagnosticReportModel).where(DiagnosticReportModel.diagnostic_report_id == diagnostic_report_id)
            dr = (await session.execute(stmt)).scalars().first()
            if not dr:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set
            sub_created_by = payload.updated_by if payload.updated_by is not None else dr.created_by

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(dr, field, value)
            if updated_by := payload.updated_by:
                dr.updated_by = updated_by

            if "status" in provided and payload.status is not None:
                dr.status = _model_status(payload.status)

            if "code" in provided and payload.code is not None:
                dr.code_text = payload.code.text
                await session.execute(delete(DiagnosticReportCodeCoding).where(DiagnosticReportCodeCoding.diagnostic_report_pk == dr.id))
                for coding in payload.code.coding or []:
                    session.add(DiagnosticReportCodeCoding(diagnostic_report_pk=dr.id, tenant_id=dr.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            if provided & _EFFECTIVE_FIELDS:
                for field in _EFFECTIVE_FIELDS:
                    if field in provided:
                        setattr(dr, field, getattr(payload, field))

            for prefix, enum_cls, modeled in (
                ("subject", DiagnosticReportSubjectReferenceType, _MODELED_SUBJECT_TYPES),
                ("encounter", EncounterReferenceType, None),
            ):
                if prefix in provided:
                    kwargs = _single_reference_kwargs(prefix, getattr(payload, prefix), enum_cls)
                    await _validate_ref(session, dr.tenant_id, prefix, kwargs[f"{prefix}_type"], kwargs[f"{prefix}_id"], modeled)
                    for col, value in kwargs.items():
                        setattr(dr, col, value)

            if payload.identifier is not None:
                await session.execute(delete(DiagnosticReportIdentifierTypeCoding).where(
                    DiagnosticReportIdentifierTypeCoding.diagnostic_report_identifier_id.in_(
                        select(DiagnosticReportIdentifier.id).where(DiagnosticReportIdentifier.diagnostic_report_pk == dr.id)
                    )
                ))
                await session.execute(delete(DiagnosticReportIdentifier).where(DiagnosticReportIdentifier.diagnostic_report_pk == dr.id))
            if payload.based_on is not None:
                await session.execute(delete(DiagnosticReportBasedOn).where(DiagnosticReportBasedOn.diagnostic_report_pk == dr.id))
            if payload.category is not None:
                await session.execute(delete(DiagnosticReportCategoryCoding).where(
                    DiagnosticReportCategoryCoding.diagnostic_report_category_id.in_(
                        select(DiagnosticReportCategory.id).where(DiagnosticReportCategory.diagnostic_report_pk == dr.id)
                    )
                ))
                await session.execute(delete(DiagnosticReportCategory).where(DiagnosticReportCategory.diagnostic_report_pk == dr.id))
            if payload.performer is not None:
                await session.execute(delete(DiagnosticReportPerformer).where(DiagnosticReportPerformer.diagnostic_report_pk == dr.id))
            if payload.results_interpreter is not None:
                await session.execute(delete(DiagnosticReportResultsInterpreter).where(DiagnosticReportResultsInterpreter.diagnostic_report_pk == dr.id))
            if payload.specimen is not None:
                await session.execute(delete(DiagnosticReportSpecimen).where(DiagnosticReportSpecimen.diagnostic_report_pk == dr.id))
            if payload.result is not None:
                await session.execute(delete(DiagnosticReportResult).where(DiagnosticReportResult.diagnostic_report_pk == dr.id))
            if payload.imaging_study is not None:
                await session.execute(delete(DiagnosticReportImagingStudy).where(DiagnosticReportImagingStudy.diagnostic_report_pk == dr.id))
            if payload.media is not None:
                await session.execute(delete(DiagnosticReportMedia).where(DiagnosticReportMedia.diagnostic_report_pk == dr.id))
            if payload.conclusion_code is not None:
                await session.execute(delete(DiagnosticReportConclusionCodeCoding).where(
                    DiagnosticReportConclusionCodeCoding.diagnostic_report_conclusion_code_id.in_(
                        select(DiagnosticReportConclusionCode.id).where(DiagnosticReportConclusionCode.diagnostic_report_pk == dr.id)
                    )
                ))
                await session.execute(delete(DiagnosticReportConclusionCode).where(DiagnosticReportConclusionCode.diagnostic_report_pk == dr.id))
            if payload.presented_form is not None:
                await session.execute(delete(DiagnosticReportPresentedForm).where(DiagnosticReportPresentedForm.diagnostic_report_pk == dr.id))

            await self._insert_sub_resources(session, dr.id, payload, dr.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted((_SUB | _SINGLE_OBJECT_FIELDS) & set(data.keys()))
            if replaced:
                logger.debug(
                    "DiagnosticReport sub-resource lists replaced",
                    extra={"event": "diagnostic_report.sublists_replaced", "diagnostic_report_id": diagnostic_report_id, "replaced": replaced},
                )

        return await self.get_by_diagnostic_report_id(diagnostic_report_id)

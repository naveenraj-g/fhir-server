from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.condition import (
    ConditionAsserterReferenceType,
    ConditionBodySite,
    ConditionBodySiteCoding,
    ConditionCategory,
    ConditionCategoryCoding,
    ConditionClinicalStatusCoding,
    ConditionCodeCoding,
    ConditionEvidence,
    ConditionEvidenceCode,
    ConditionEvidenceCodeCoding,
    ConditionEvidenceDetail,
    ConditionIdentifier,
    ConditionIdentifierTypeCoding,
    ConditionModel,
    ConditionNote,
    ConditionNoteAuthorReferenceType,
    ConditionQuantityComparator as ConditionQuantityComparatorModel,
    ConditionRecorderReferenceType,
    ConditionSeverityCoding,
    ConditionStage,
    ConditionStageAssessment,
    ConditionStageAssessmentReferenceType,
    ConditionStageSummaryCoding,
    ConditionStageTypeCoding,
    ConditionVerificationStatusCoding,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.schemas.condition import ConditionCreateSchema, ConditionPatchSchema

from ._shared import (
    _parse_asserter_ref,
    _parse_assessment_ref,
    _parse_encounter_ref,
    _parse_note_author_ref,
    _parse_org_ref,
    _parse_recorder_ref,
    _parse_subject_ref,
    _reference_kwargs,
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


async def _add_identifiers(session, condition_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
        await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = ConditionIdentifier(
            condition_pk=condition_pk,
            tenant_id=org_id,
            use=IdentifierUseModel[i.use.name] if i.use else None,
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=(
                IdentifierUseModel[i.assigner_identifier_use.name]
                if i.assigner_identifier_use
                else None
            ),
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            created_by=created_by,
        )
        session.add(ident)
        if i.type_coding:
            await session.flush()
            for c in i.type_coding:
                session.add(
                    ConditionIdentifierTypeCoding(
                        condition_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_clinical_status_codings(session, condition_pk: int, org_id: str, cc, created_by: str) -> None:
    if cc and cc.coding:
        for c in cc.coding:
            session.add(
                ConditionClinicalStatusCoding(
                    condition_pk=condition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_verification_status_codings(session, condition_pk: int, org_id: str, cc, created_by: str) -> None:
    if cc and cc.coding:
        for c in cc.coding:
            session.add(
                ConditionVerificationStatusCoding(
                    condition_pk=condition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_severity_codings(session, condition_pk: int, org_id: str, cc, created_by: str) -> None:
    if cc and cc.coding:
        for c in cc.coding:
            session.add(
                ConditionSeverityCoding(
                    condition_pk=condition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_code_codings(session, condition_pk: int, org_id: str, cc, created_by: str) -> None:
    if cc and cc.coding:
        for c in cc.coding:
            session.add(
                ConditionCodeCoding(
                    condition_pk=condition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_categories(session, condition_pk: int, org_id: str, categories, created_by: str) -> None:
    for cat in categories or []:
        cat_row = ConditionCategory(
            condition_pk=condition_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(cat_row)
        if cat.coding:
            await session.flush()
            for c in cat.coding:
                session.add(
                    ConditionCategoryCoding(
                        condition_category_id=cat_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_body_sites(session, condition_pk: int, org_id: str, body_sites, created_by: str) -> None:
    for b in body_sites or []:
        b_row = ConditionBodySite(
            condition_pk=condition_pk,
            tenant_id=org_id,
            text=b.text,
            created_by=created_by,
        )
        session.add(b_row)
        if b.coding:
            await session.flush()
            for c in b.coding:
                session.add(
                    ConditionBodySiteCoding(
                        condition_body_site_id=b_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_stages(session, condition_pk: int, org_id: str, stages, created_by: str) -> None:
    for s in stages or []:
        stage_row = ConditionStage(
            condition_pk=condition_pk,
            tenant_id=org_id,
            summary_text=s.summary.text if s.summary else None,
            type_text=s.type.text if s.type else None,
            created_by=created_by,
        )
        session.add(stage_row)
        await session.flush()

        if s.summary and s.summary.coding:
            for c in s.summary.coding:
                session.add(
                    ConditionStageSummaryCoding(
                        condition_stage_id=stage_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if s.type and s.type.coding:
            for c in s.type.coding:
                session.add(
                    ConditionStageTypeCoding(
                        condition_stage_id=stage_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if s.assessment:
            for a in s.assessment:
                ref_type, ref_id = (
                    _parse_assessment_ref(a.reference) if a.reference else (None, None)
                )
                await _validate_ref(session, org_id, ref_type, ref_id, "stage.assessment")
                session.add(
                    ConditionStageAssessment(
                        condition_stage_id=stage_row.id,
                        tenant_id=org_id,
                        reference_reference=a.reference,
                        reference_type=ref_type,
                        reference_id=ref_id,
                        reference_display=a.reference_display,
                        reference_identifier_use=(
                            IdentifierUseModel[a.reference_identifier_use.name]
                            if a.reference_identifier_use
                            else None
                        ),
                        reference_identifier_system=a.reference_identifier_system,
                        reference_identifier_value=a.reference_identifier_value,
                        reference_identifier_type_text=a.reference_identifier_type_text,
                        created_by=created_by,
                    )
                )


async def _add_evidence(session, condition_pk: int, org_id: str, evidence_list, created_by: str) -> None:
    for e in evidence_list or []:
        ev_row = ConditionEvidence(
            condition_pk=condition_pk,
            tenant_id=org_id,
            created_by=created_by,
        )
        session.add(ev_row)
        await session.flush()

        if e.code:
            for c in e.code:
                code_row = ConditionEvidenceCode(
                    condition_evidence_id=ev_row.id,
                    tenant_id=org_id,
                    text=c.text,
                    created_by=created_by,
                )
                session.add(code_row)
                if c.coding:
                    await session.flush()
                    for coding in c.coding:
                        session.add(
                            ConditionEvidenceCodeCoding(
                                condition_evidence_code_id=code_row.id,
                                **_coding_kwargs(coding, org_id, created_by),
                            )
                        )

        if e.detail:
            for d in e.detail:
                ref_type_str: str | None = None
                ref_id_int: int | None = None
                if d.reference and "/" in d.reference:
                    parts = d.reference.split("/", 1)
                    ref_type_str = parts[0]
                    if parts[1].isdigit():
                        ref_id_int = int(parts[1])
                await _validate_ref(session, org_id, ref_type_str, ref_id_int, "evidence.detail")
                session.add(
                    ConditionEvidenceDetail(
                        condition_evidence_id=ev_row.id,
                        tenant_id=org_id,
                        reference_reference=d.reference,
                        reference_type=ref_type_str,
                        reference_id=ref_id_int,
                        reference_display=d.reference_display,
                        reference_identifier_use=(
                            IdentifierUseModel[d.reference_identifier_use.name]
                            if d.reference_identifier_use
                            else None
                        ),
                        reference_identifier_system=d.reference_identifier_system,
                        reference_identifier_value=d.reference_identifier_value,
                        reference_identifier_type_text=d.reference_identifier_type_text,
                        created_by=created_by,
                    )
                )


async def _add_notes(session, condition_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        a_type, a_id = (
            _parse_note_author_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        await _validate_ref(session, org_id, a_type, a_id, "note.author")
        session.add(
            ConditionNote(
                condition_pk=condition_pk,
                tenant_id=org_id,
                author_string=n.author_string,
                author_reference=n.author_reference,
                author_type=a_type,
                author_id=a_id,
                author_display=n.author_reference_display,
                time=n.time,
                text=n.text,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Full-payload create and patch operations for Condition."""

    async def create_full(
        self,
        payload: ConditionCreateSchema,
        org_id: str,
        created_by: str,
    ) -> ConditionModel:
        async with self.session_factory() as session:
            # Validate subject reference (1..1)
            s_type, s_id = _parse_subject_ref(payload.subject.reference)
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            # Validate optional encounter reference
            e_type, e_id = (
                _parse_encounter_ref(payload.encounter.reference)
                if payload.encounter and payload.encounter.reference
                else (None, None)
            )
            await _validate_ref(session, org_id, e_type, e_id, "encounter")

            # Validate optional recorder reference
            r_type, r_id = (
                _parse_recorder_ref(payload.recorder.reference)
                if payload.recorder and payload.recorder.reference
                else (None, None)
            )
            await _validate_ref(session, org_id, r_type, r_id, "recorder")

            # Validate optional asserter reference
            as_type, as_id = (
                _parse_asserter_ref(payload.asserter.reference)
                if payload.asserter and payload.asserter.reference
                else (None, None)
            )
            await _validate_ref(session, org_id, as_type, as_id, "asserter")

            cond = ConditionModel(
                tenant_id=org_id,
                clinical_status_text=(
                    payload.clinical_status.text if payload.clinical_status else None
                ),
                verification_status_text=(
                    payload.verification_status.text if payload.verification_status else None
                ),
                severity_text=(
                    payload.severity.text if payload.severity else None
                ),
                code_text=(
                    payload.code.text if payload.code else None
                ),
                subject_reference=payload.subject.reference,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject.reference_display,
                **_reference_kwargs("subject", payload.subject),
                encounter_reference=(
                    payload.encounter.reference if payload.encounter else None
                ),
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=(
                    payload.encounter.reference_display if payload.encounter else None
                ),
                **_reference_kwargs("encounter", payload.encounter),
                onset_date_time=payload.onset_date_time,
                onset_age_value=payload.onset_age_value,
                onset_age_comparator=(
                    ConditionQuantityComparatorModel[payload.onset_age_comparator.name]
                    if payload.onset_age_comparator
                    else None
                ),
                onset_age_unit=payload.onset_age_unit,
                onset_age_system=payload.onset_age_system,
                onset_age_code=payload.onset_age_code,
                onset_period_start=payload.onset_period_start,
                onset_period_end=payload.onset_period_end,
                onset_range_low_value=payload.onset_range_low_value,
                onset_range_low_unit=payload.onset_range_low_unit,
                onset_range_low_system=payload.onset_range_low_system,
                onset_range_low_code=payload.onset_range_low_code,
                onset_range_high_value=payload.onset_range_high_value,
                onset_range_high_unit=payload.onset_range_high_unit,
                onset_range_high_system=payload.onset_range_high_system,
                onset_range_high_code=payload.onset_range_high_code,
                onset_string=payload.onset_string,
                abatement_date_time=payload.abatement_date_time,
                abatement_age_value=payload.abatement_age_value,
                abatement_age_comparator=(
                    ConditionQuantityComparatorModel[payload.abatement_age_comparator.name]
                    if payload.abatement_age_comparator
                    else None
                ),
                abatement_age_unit=payload.abatement_age_unit,
                abatement_age_system=payload.abatement_age_system,
                abatement_age_code=payload.abatement_age_code,
                abatement_period_start=payload.abatement_period_start,
                abatement_period_end=payload.abatement_period_end,
                abatement_range_low_value=payload.abatement_range_low_value,
                abatement_range_low_unit=payload.abatement_range_low_unit,
                abatement_range_low_system=payload.abatement_range_low_system,
                abatement_range_low_code=payload.abatement_range_low_code,
                abatement_range_high_value=payload.abatement_range_high_value,
                abatement_range_high_unit=payload.abatement_range_high_unit,
                abatement_range_high_system=payload.abatement_range_high_system,
                abatement_range_high_code=payload.abatement_range_high_code,
                abatement_string=payload.abatement_string,
                recorded_date=payload.recorded_date,
                recorder_reference=(
                    payload.recorder.reference if payload.recorder else None
                ),
                recorder_type=r_type,
                recorder_id=r_id,
                recorder_display=(
                    payload.recorder.reference_display if payload.recorder else None
                ),
                **_reference_kwargs("recorder", payload.recorder),
                asserter_reference=(
                    payload.asserter.reference if payload.asserter else None
                ),
                asserter_type=as_type,
                asserter_id=as_id,
                asserter_display=(
                    payload.asserter.reference_display if payload.asserter else None
                ),
                **_reference_kwargs("asserter", payload.asserter),
                extension=payload.extension if payload.extension is not None else [],
                created_by=created_by,
            )
            session.add(cond)
            await session.flush()

            # Add child rows
            await _add_identifiers(session, cond.id, org_id, payload.identifier, created_by)
            _add_clinical_status_codings(session, cond.id, org_id, payload.clinical_status, created_by)
            _add_verification_status_codings(session, cond.id, org_id, payload.verification_status, created_by)
            _add_severity_codings(session, cond.id, org_id, payload.severity, created_by)
            _add_code_codings(session, cond.id, org_id, payload.code, created_by)
            await _add_categories(session, cond.id, org_id, payload.category, created_by)
            await _add_body_sites(session, cond.id, org_id, payload.body_site, created_by)
            await _add_stages(session, cond.id, org_id, payload.stage, created_by)
            await _add_evidence(session, cond.id, org_id, payload.evidence, created_by)
            await _add_notes(session, cond.id, org_id, payload.note, created_by)

            await session.commit()

        return await self.get_by_condition_id(cond.condition_id)

    async def patch_full(
        self,
        condition_id: int,
        payload: ConditionPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> ConditionModel | None:
        async with self.session_factory() as session:
            stmt = select(ConditionModel).where(
                ConditionModel.condition_id == condition_id,
                ConditionModel.tenant_id == org_id,
            )
            cond = (await session.execute(stmt)).scalars().first()
            if not cond:
                return None

            provided = payload.model_dump(exclude_unset=True)

            if "extension" in provided:
                cond.extension = payload.extension if payload.extension is not None else []

            if "clinical_status" in provided:
                cond.clinical_status_text = (
                    payload.clinical_status.text if payload.clinical_status else None
                )
                await session.execute(
                    delete(ConditionClinicalStatusCoding).where(
                        ConditionClinicalStatusCoding.condition_pk == cond.id
                    )
                )
                _add_clinical_status_codings(session, cond.id, org_id, payload.clinical_status, updated_by)

            if "verification_status" in provided:
                cond.verification_status_text = (
                    payload.verification_status.text if payload.verification_status else None
                )
                await session.execute(
                    delete(ConditionVerificationStatusCoding).where(
                        ConditionVerificationStatusCoding.condition_pk == cond.id
                    )
                )
                _add_verification_status_codings(session, cond.id, org_id, payload.verification_status, updated_by)

            if "severity" in provided:
                cond.severity_text = (
                    payload.severity.text if payload.severity else None
                )
                await session.execute(
                    delete(ConditionSeverityCoding).where(
                        ConditionSeverityCoding.condition_pk == cond.id
                    )
                )
                _add_severity_codings(session, cond.id, org_id, payload.severity, updated_by)

            if "code" in provided:
                cond.code_text = (
                    payload.code.text if payload.code else None
                )
                await session.execute(
                    delete(ConditionCodeCoding).where(
                        ConditionCodeCoding.condition_pk == cond.id
                    )
                )
                _add_code_codings(session, cond.id, org_id, payload.code, updated_by)

            if "subject" in provided:
                if payload.subject and payload.subject.reference:
                    s_type, s_id = _parse_subject_ref(payload.subject.reference)
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                    cond.subject_reference = payload.subject.reference
                    cond.subject_type = s_type
                    cond.subject_id = s_id
                    cond.subject_display = payload.subject.reference_display
                    for k, v in _reference_kwargs("subject", payload.subject).items():
                        setattr(cond, k, v)
                elif payload.subject is None:
                    cond.subject_reference = None
                    cond.subject_type = None
                    cond.subject_id = None
                    cond.subject_display = None

            if "encounter" in provided:
                if payload.encounter and payload.encounter.reference:
                    e_type, e_id = _parse_encounter_ref(payload.encounter.reference)
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                    cond.encounter_reference = payload.encounter.reference
                    cond.encounter_type = e_type
                    cond.encounter_id = e_id
                    cond.encounter_display = payload.encounter.reference_display
                    for k, v in _reference_kwargs("encounter", payload.encounter).items():
                        setattr(cond, k, v)
                else:
                    cond.encounter_reference = None
                    cond.encounter_type = None
                    cond.encounter_id = None
                    cond.encounter_display = None

            # Onset fields
            for field in [
                "onset_date_time",
                "onset_age_value",
                "onset_age_unit",
                "onset_age_system",
                "onset_age_code",
                "onset_period_start",
                "onset_period_end",
                "onset_range_low_value",
                "onset_range_low_unit",
                "onset_range_low_system",
                "onset_range_low_code",
                "onset_range_high_value",
                "onset_range_high_unit",
                "onset_range_high_system",
                "onset_range_high_code",
                "onset_string",
            ]:
                if field in provided:
                    setattr(cond, field, getattr(payload, field))
            if "onset_age_comparator" in provided:
                cond.onset_age_comparator = (
                    ConditionQuantityComparatorModel[payload.onset_age_comparator.name]
                    if payload.onset_age_comparator
                    else None
                )

            # Abatement fields
            for field in [
                "abatement_date_time",
                "abatement_age_value",
                "abatement_age_unit",
                "abatement_age_system",
                "abatement_age_code",
                "abatement_period_start",
                "abatement_period_end",
                "abatement_range_low_value",
                "abatement_range_low_unit",
                "abatement_range_low_system",
                "abatement_range_low_code",
                "abatement_range_high_value",
                "abatement_range_high_unit",
                "abatement_range_high_system",
                "abatement_range_high_code",
                "abatement_string",
            ]:
                if field in provided:
                    setattr(cond, field, getattr(payload, field))
            if "abatement_age_comparator" in provided:
                cond.abatement_age_comparator = (
                    ConditionQuantityComparatorModel[payload.abatement_age_comparator.name]
                    if payload.abatement_age_comparator
                    else None
                )

            if "recorded_date" in provided:
                cond.recorded_date = payload.recorded_date

            if "recorder" in provided:
                if payload.recorder and payload.recorder.reference:
                    r_type, r_id = _parse_recorder_ref(payload.recorder.reference)
                    await _validate_ref(session, org_id, r_type, r_id, "recorder")
                    cond.recorder_reference = payload.recorder.reference
                    cond.recorder_type = r_type
                    cond.recorder_id = r_id
                    cond.recorder_display = payload.recorder.reference_display
                    for k, v in _reference_kwargs("recorder", payload.recorder).items():
                        setattr(cond, k, v)
                else:
                    cond.recorder_reference = None
                    cond.recorder_type = None
                    cond.recorder_id = None
                    cond.recorder_display = None

            if "asserter" in provided:
                if payload.asserter and payload.asserter.reference:
                    as_type, as_id = _parse_asserter_ref(payload.asserter.reference)
                    await _validate_ref(session, org_id, as_type, as_id, "asserter")
                    cond.asserter_reference = payload.asserter.reference
                    cond.asserter_type = as_type
                    cond.asserter_id = as_id
                    cond.asserter_display = payload.asserter.reference_display
                    for k, v in _reference_kwargs("asserter", payload.asserter).items():
                        setattr(cond, k, v)
                else:
                    cond.asserter_reference = None
                    cond.asserter_type = None
                    cond.asserter_id = None
                    cond.asserter_display = None

            # Sub-resources lists
            if "identifier" in provided:
                ident_sub = select(ConditionIdentifier.id).where(
                    ConditionIdentifier.condition_pk == cond.id
                )
                await session.execute(
                    delete(ConditionIdentifierTypeCoding).where(
                        ConditionIdentifierTypeCoding.condition_identifier_id.in_(ident_sub)
                    )
                )
                await session.execute(
                    delete(ConditionIdentifier).where(
                        ConditionIdentifier.condition_pk == cond.id
                    )
                )
                await _add_identifiers(session, cond.id, org_id, payload.identifier, updated_by)

            if "category" in provided:
                cat_sub = select(ConditionCategory.id).where(
                    ConditionCategory.condition_pk == cond.id
                )
                await session.execute(
                    delete(ConditionCategoryCoding).where(
                        ConditionCategoryCoding.condition_category_id.in_(cat_sub)
                    )
                )
                await session.execute(
                    delete(ConditionCategory).where(
                        ConditionCategory.condition_pk == cond.id
                    )
                )
                await _add_categories(session, cond.id, org_id, payload.category, updated_by)

            if "body_site" in provided:
                site_sub = select(ConditionBodySite.id).where(
                    ConditionBodySite.condition_pk == cond.id
                )
                await session.execute(
                    delete(ConditionBodySiteCoding).where(
                        ConditionBodySiteCoding.condition_body_site_id.in_(site_sub)
                    )
                )
                await session.execute(
                    delete(ConditionBodySite).where(
                        ConditionBodySite.condition_pk == cond.id
                    )
                )
                await _add_body_sites(session, cond.id, org_id, payload.body_site, updated_by)

            if "stage" in provided:
                stage_sub = select(ConditionStage.id).where(
                    ConditionStage.condition_pk == cond.id
                )
                await session.execute(
                    delete(ConditionStageSummaryCoding).where(
                        ConditionStageSummaryCoding.condition_stage_id.in_(stage_sub)
                    )
                )
                await session.execute(
                    delete(ConditionStageTypeCoding).where(
                        ConditionStageTypeCoding.condition_stage_id.in_(stage_sub)
                    )
                )
                await session.execute(
                    delete(ConditionStageAssessment).where(
                        ConditionStageAssessment.condition_stage_id.in_(stage_sub)
                    )
                )
                await session.execute(
                    delete(ConditionStage).where(
                        ConditionStage.condition_pk == cond.id
                    )
                )
                await _add_stages(session, cond.id, org_id, payload.stage, updated_by)

            if "evidence" in provided:
                ev_sub = select(ConditionEvidence.id).where(
                    ConditionEvidence.condition_pk == cond.id
                )
                code_sub = select(ConditionEvidenceCode.id).where(
                    ConditionEvidenceCode.condition_evidence_id.in_(ev_sub)
                )
                await session.execute(
                    delete(ConditionEvidenceCodeCoding).where(
                        ConditionEvidenceCodeCoding.condition_evidence_code_id.in_(code_sub)
                    )
                )
                await session.execute(
                    delete(ConditionEvidenceCode).where(
                        ConditionEvidenceCode.condition_evidence_id.in_(ev_sub)
                    )
                )
                await session.execute(
                    delete(ConditionEvidenceDetail).where(
                        ConditionEvidenceDetail.condition_evidence_id.in_(ev_sub)
                    )
                )
                await session.execute(
                    delete(ConditionEvidence).where(
                        ConditionEvidence.condition_pk == cond.id
                    )
                )
                await _add_evidence(session, cond.id, org_id, payload.evidence, updated_by)

            if "note" in provided:
                await session.execute(
                    delete(ConditionNote).where(
                        ConditionNote.condition_pk == cond.id
                    )
                )
                await _add_notes(session, cond.id, org_id, payload.note, updated_by)

            cond.updated_by = updated_by
            await session.commit()

        return await self.get_by_condition_id(condition_id)

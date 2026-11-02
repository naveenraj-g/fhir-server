from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.medication_statement import (
    MedicationStatementBasedOn,
    MedicationStatementBasedOnReferenceType,
    MedicationStatementCategoryCoding,
    MedicationStatementContextReferenceType,
    MedicationStatementDerivedFrom,
    MedicationStatementDosage,
    MedicationStatementDosageAdditionalInstruction,
    MedicationStatementDosageAdditionalInstructionCoding,
    MedicationStatementDosageAsNeededCoding,
    MedicationStatementDosageMethodCoding,
    MedicationStatementDosageRouteCoding,
    MedicationStatementDosageSiteCoding,
    MedicationStatementIdentifier,
    MedicationStatementIdentifierTypeCoding,
    MedicationStatementInformationSourceReferenceType,
    MedicationStatementMedicationCoding,
    MedicationStatementMedicationReferenceType,
    MedicationStatementModel,
    MedicationStatementNote,
    MedicationStatementNoteAuthorReferenceType,
    MedicationStatementPartOf,
    MedicationStatementPartOfReferenceType,
    MedicationStatementReasonCode,
    MedicationStatementReasonCodeCoding,
    MedicationStatementReasonReference,
    MedicationStatementReasonReferenceType,
    MedicationStatementStatus as MedicationStatementStatusModel,
    MedicationStatementStatusReason,
    MedicationStatementStatusReasonCoding,
    MedicationStatementSubjectReferenceType,
)
from app.schemas.medication_statement import (
    MedicationStatementCreateSchema,
    MedicationStatementPatchSchema,
)

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _list_reference_kwargs,
    _parse_org_ref,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)

_SUB = {
    "identifier",
    "based_on",
    "part_of",
    "status_reason",
    "category",
    "medication_codeable_concept",
    "derived_from",
    "reason_code",
    "reason_reference",
    "note",
    "dosage",
}

_SINGLE_OBJECT_FIELDS = {
    "subject",
    "context",
    "information_source",
    "medication_reference",
}


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


async def _add_identifiers(session, ms_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, "identifier.assigner", a_type, a_id)

        ident = MedicationStatementIdentifier(
            medication_statement_pk=ms_pk,
            tenant_id=org_id,
            use=IdentifierUseModel[i.use.name] if i.use else None,
            type_text=i.type.text if i.type else None,
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
                if getattr(i, "assigner_identifier_use", None)
                else None
            ),
            **{
                f"assigner_{s}": getattr(i, f"assigner_{s}", None)
                for s in _IDENTIFIER_FALLBACK_SUFFIXES
                if s != "identifier_use"
            },
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    MedicationStatementIdentifierTypeCoding(
                        medication_statement_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _insert_sub_resources(
    session, ms_pk: int, payload, org_id: str, created_by: str
) -> None:
    await _add_identifiers(session, ms_pk, org_id, payload.identifier, created_by)

    for b in payload.based_on or []:
        kwargs = _list_reference_kwargs(b, MedicationStatementBasedOnReferenceType)
        await _validate_ref(session, org_id, "basedOn", kwargs["reference_type"], kwargs["reference_id"])
        session.add(
            MedicationStatementBasedOn(
                medication_statement_pk=ms_pk,
                tenant_id=org_id,
                created_by=created_by,
                **kwargs,
            )
        )

    for p in payload.part_of or []:
        kwargs = _list_reference_kwargs(p, MedicationStatementPartOfReferenceType)
        await _validate_ref(session, org_id, "partOf", kwargs["reference_type"], kwargs["reference_id"])
        session.add(
            MedicationStatementPartOf(
                medication_statement_pk=ms_pk,
                tenant_id=org_id,
                created_by=created_by,
                **kwargs,
            )
        )

    for sr in payload.status_reason or []:
        sr_row = MedicationStatementStatusReason(
            medication_statement_pk=ms_pk,
            tenant_id=org_id,
            created_by=created_by,
            text=sr.text,
        )
        session.add(sr_row)
        if sr.coding:
            await session.flush()
            for coding in sr.coding:
                session.add(
                    MedicationStatementStatusReasonCoding(
                        medication_statement_status_reason_id=sr_row.id,
                        **_coding_kwargs(coding, org_id, created_by),
                    )
                )

    if payload.category and payload.category.coding:
        for coding in payload.category.coding:
            session.add(
                MedicationStatementCategoryCoding(
                    medication_statement_pk=ms_pk,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )

    if payload.medication_codeable_concept and payload.medication_codeable_concept.coding:
        for coding in payload.medication_codeable_concept.coding:
            session.add(
                MedicationStatementMedicationCoding(
                    medication_statement_pk=ms_pk,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )

    for df in payload.derived_from or []:
        kwargs = _list_reference_kwargs(df, None)
        session.add(
            MedicationStatementDerivedFrom(
                medication_statement_pk=ms_pk,
                tenant_id=org_id,
                created_by=created_by,
                **kwargs,
            )
        )

    for rc in payload.reason_code or []:
        rc_row = MedicationStatementReasonCode(
            medication_statement_pk=ms_pk,
            tenant_id=org_id,
            created_by=created_by,
            text=rc.text,
        )
        session.add(rc_row)
        if rc.coding:
            await session.flush()
            for coding in rc.coding:
                session.add(
                    MedicationStatementReasonCodeCoding(
                        medication_statement_reason_code_id=rc_row.id,
                        **_coding_kwargs(coding, org_id, created_by),
                    )
                )

    for rr in payload.reason_reference or []:
        kwargs = _list_reference_kwargs(rr, MedicationStatementReasonReferenceType)
        await _validate_ref(session, org_id, "reasonReference", kwargs["reference_type"], kwargs["reference_id"])
        session.add(
            MedicationStatementReasonReference(
                medication_statement_pk=ms_pk,
                tenant_id=org_id,
                created_by=created_by,
                **kwargs,
            )
        )

    for n in payload.note or []:
        author_kwargs = _ref_kwargs(
            "author", n.author_reference, n.author_display, MedicationStatementNoteAuthorReferenceType
        )
        if n.author_reference:
            await _validate_ref(session, org_id, "note.author", author_kwargs["author_type"], author_kwargs["author_id"])
        session.add(
            MedicationStatementNote(
                medication_statement_pk=ms_pk,
                tenant_id=org_id,
                created_by=created_by,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference=n.author_reference,
                **author_kwargs,
                author_identifier_use=(
                    IdentifierUseModel[n.author_identifier_use.name]
                    if getattr(n, "author_identifier_use", None)
                    else None
                ),
                **{
                    f"author_{s}": getattr(n, f"author_{s}", None)
                    for s in _IDENTIFIER_FALLBACK_SUFFIXES
                    if s != "identifier_use"
                },
            )
        )

    for d in payload.dosage or []:
        dosage = MedicationStatementDosage(
            medication_statement_pk=ms_pk,
            tenant_id=org_id,
            created_by=created_by,
            sequence=d.sequence,
            text=d.text,
            patient_instruction=d.patient_instruction,
            timing=d.timing,
            as_needed_boolean=d.as_needed_boolean,
            as_needed_codeable_concept_text=(
                d.as_needed_codeable_concept.text if d.as_needed_codeable_concept else None
            ),
            site_text=d.site.text if d.site else None,
            route_text=d.route.text if d.route else None,
            method_text=d.method.text if d.method else None,
            dose_and_rate=d.dose_and_rate,
            max_dose_per_period=d.max_dose_per_period,
            max_dose_per_administration_value=d.max_dose_per_administration_value,
            max_dose_per_administration_unit=d.max_dose_per_administration_unit,
            max_dose_per_administration_system=d.max_dose_per_administration_system,
            max_dose_per_administration_code=d.max_dose_per_administration_code,
            max_dose_per_lifetime_value=d.max_dose_per_lifetime_value,
            max_dose_per_lifetime_unit=d.max_dose_per_lifetime_unit,
            max_dose_per_lifetime_system=d.max_dose_per_lifetime_system,
            max_dose_per_lifetime_code=d.max_dose_per_lifetime_code,
        )
        session.add(dosage)
        await session.flush()

        for ai in d.additional_instruction or []:
            ai_row = MedicationStatementDosageAdditionalInstruction(
                medication_statement_dosage_id=dosage.id,
                tenant_id=org_id,
                created_by=created_by,
                text=ai.text,
            )
            session.add(ai_row)
            if ai.coding:
                await session.flush()
                for coding in ai.coding:
                    session.add(
                        MedicationStatementDosageAdditionalInstructionCoding(
                            medication_statement_dosage_additional_instruction_id=ai_row.id,
                            **_coding_kwargs(coding, org_id, created_by),
                        )
                    )

        for coding in (d.site.coding if d.site else None) or []:
            session.add(
                MedicationStatementDosageSiteCoding(
                    medication_statement_dosage_id=dosage.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )

        for coding in (d.route.coding if d.route else None) or []:
            session.add(
                MedicationStatementDosageRouteCoding(
                    medication_statement_dosage_id=dosage.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )

        for coding in (d.method.coding if d.method else None) or []:
            session.add(
                MedicationStatementDosageMethodCoding(
                    medication_statement_dosage_id=dosage.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )

        for coding in (d.as_needed_codeable_concept.coding if d.as_needed_codeable_concept else None) or []:
            session.add(
                MedicationStatementDosageAsNeededCoding(
                    medication_statement_dosage_id=dosage.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


class _FullMixin:
    """create_full/patch_full atomic nested-write orchestrators."""

    async def create_full(
        self,
        payload: MedicationStatementCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> MedicationStatementModel:
        actor_id = created_by or "system"
        async with self.session_factory() as session:
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, MedicationStatementSubjectReferenceType)
            medication_reference_kwargs = _single_reference_kwargs(
                "medication", payload.medication_reference, MedicationStatementMedicationReferenceType
            )
            context_kwargs = _single_reference_kwargs("context", payload.context, MedicationStatementContextReferenceType)
            info_source_kwargs = _single_reference_kwargs(
                "information_source", payload.information_source, MedicationStatementInformationSourceReferenceType
            )

            await _validate_ref(session, org_id, "subject", subject_kwargs["subject_type"], subject_kwargs["subject_id"])
            await _validate_ref(
                session, org_id, "medicationReference", medication_reference_kwargs["medication_type"], medication_reference_kwargs["medication_id"]
            )
            await _validate_ref(session, org_id, "context", context_kwargs["context_type"], context_kwargs["context_id"])
            await _validate_ref(
                session, org_id, "informationSource", info_source_kwargs["information_source_type"], info_source_kwargs["information_source_id"]
            )

            model = MedicationStatementModel(
                tenant_id=org_id,
                created_by=actor_id,
                status=(
                    MedicationStatementStatusModel[payload.status.name]
                    if hasattr(payload.status, "name")
                    else payload.status
                ),
                category_text=payload.category.text if payload.category else None,
                medication_codeable_concept_text=(
                    payload.medication_codeable_concept.text if payload.medication_codeable_concept else None
                ),
                **medication_reference_kwargs,
                **subject_kwargs,
                **context_kwargs,
                effective_date_time=payload.effective_date_time,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                date_asserted=payload.date_asserted,
                **info_source_kwargs,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            await _insert_sub_resources(session, model.id, payload, org_id, actor_id)

            await session.commit()
            return await self.get_by_medication_statement_id_in_org(model.medication_statement_id, org_id)

    async def patch_full(
        self,
        medication_statement_id: int,
        payload: MedicationStatementPatchSchema,
        org_id: str,
        updated_by: str | None = None,
    ) -> MedicationStatementModel | None:
        actor_id = updated_by or "system"
        async with self.session_factory() as session:
            stmt = select(MedicationStatementModel).where(
                MedicationStatementModel.medication_statement_id == medication_statement_id,
                MedicationStatementModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            data = payload.model_dump(exclude_unset=True)

            for field, value in data.items():
                if field in _SUB or field in _SINGLE_OBJECT_FIELDS:
                    continue
                if field == "status" and value is not None:
                    model.status = (
                        MedicationStatementStatusModel[payload.status.name]
                        if hasattr(payload.status, "name")
                        else payload.status
                    )
                else:
                    setattr(model, field, value)

            if "subject" in data:
                subj_kwargs = _single_reference_kwargs("subject", payload.subject, MedicationStatementSubjectReferenceType)
                if payload.subject:
                    await _validate_ref(session, org_id, "subject", subj_kwargs["subject_type"], subj_kwargs["subject_id"])
                for k, v in subj_kwargs.items():
                    setattr(model, k, v)

            if "medication_reference" in data:
                med_ref_kwargs = _single_reference_kwargs(
                    "medication", payload.medication_reference, MedicationStatementMedicationReferenceType
                )
                if payload.medication_reference:
                    await _validate_ref(
                        session, org_id, "medicationReference", med_ref_kwargs["medication_type"], med_ref_kwargs["medication_id"]
                    )
                for k, v in med_ref_kwargs.items():
                    setattr(model, k, v)

            if "context" in data:
                ctx_kwargs = _single_reference_kwargs("context", payload.context, MedicationStatementContextReferenceType)
                if payload.context:
                    await _validate_ref(session, org_id, "context", ctx_kwargs["context_type"], ctx_kwargs["context_id"])
                for k, v in ctx_kwargs.items():
                    setattr(model, k, v)

            if "information_source" in data:
                info_kwargs = _single_reference_kwargs(
                    "information_source", payload.information_source, MedicationStatementInformationSourceReferenceType
                )
                if payload.information_source:
                    await _validate_ref(
                        session, org_id, "informationSource", info_kwargs["information_source_type"], info_kwargs["information_source_id"]
                    )
                for k, v in info_kwargs.items():
                    setattr(model, k, v)

            if "category" in data:
                model.category_text = payload.category.text if payload.category else None
                await session.execute(
                    delete(MedicationStatementCategoryCoding).where(
                        MedicationStatementCategoryCoding.medication_statement_pk == model.id
                    )
                )
                if payload.category and payload.category.coding:
                    for c in payload.category.coding:
                        session.add(
                            MedicationStatementCategoryCoding(
                                medication_statement_pk=model.id,
                                **_coding_kwargs(c, org_id, actor_id),
                            )
                        )

            if "medication_codeable_concept" in data:
                model.medication_codeable_concept_text = (
                    payload.medication_codeable_concept.text if payload.medication_codeable_concept else None
                )
                await session.execute(
                    delete(MedicationStatementMedicationCoding).where(
                        MedicationStatementMedicationCoding.medication_statement_pk == model.id
                    )
                )
                if payload.medication_codeable_concept and payload.medication_codeable_concept.coding:
                    for c in payload.medication_codeable_concept.coding:
                        session.add(
                            MedicationStatementMedicationCoding(
                                medication_statement_pk=model.id,
                                **_coding_kwargs(c, org_id, actor_id),
                            )
                        )

            if "identifier" in data:
                ident_ids_subq = select(MedicationStatementIdentifier.id).where(
                    MedicationStatementIdentifier.medication_statement_pk == model.id
                )
                await session.execute(
                    delete(MedicationStatementIdentifierTypeCoding).where(
                        MedicationStatementIdentifierTypeCoding.medication_statement_identifier_id.in_(ident_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementIdentifier).where(
                        MedicationStatementIdentifier.medication_statement_pk == model.id
                    )
                )
                await _add_identifiers(session, model.id, org_id, payload.identifier, actor_id)

            if "based_on" in data:
                await session.execute(
                    delete(MedicationStatementBasedOn).where(
                        MedicationStatementBasedOn.medication_statement_pk == model.id
                    )
                )
                for b in payload.based_on or []:
                    kwargs = _list_reference_kwargs(b, MedicationStatementBasedOnReferenceType)
                    await _validate_ref(session, org_id, "basedOn", kwargs["reference_type"], kwargs["reference_id"])
                    session.add(
                        MedicationStatementBasedOn(
                            medication_statement_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **kwargs,
                        )
                    )

            if "part_of" in data:
                await session.execute(
                    delete(MedicationStatementPartOf).where(
                        MedicationStatementPartOf.medication_statement_pk == model.id
                    )
                )
                for p in payload.part_of or []:
                    kwargs = _list_reference_kwargs(p, MedicationStatementPartOfReferenceType)
                    await _validate_ref(session, org_id, "partOf", kwargs["reference_type"], kwargs["reference_id"])
                    session.add(
                        MedicationStatementPartOf(
                            medication_statement_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **kwargs,
                        )
                    )

            if "status_reason" in data:
                sr_ids_subq = select(MedicationStatementStatusReason.id).where(
                    MedicationStatementStatusReason.medication_statement_pk == model.id
                )
                await session.execute(
                    delete(MedicationStatementStatusReasonCoding).where(
                        MedicationStatementStatusReasonCoding.medication_statement_status_reason_id.in_(sr_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementStatusReason).where(
                        MedicationStatementStatusReason.medication_statement_pk == model.id
                    )
                )
                for sr in payload.status_reason or []:
                    sr_row = MedicationStatementStatusReason(
                        medication_statement_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        text=sr.text,
                    )
                    session.add(sr_row)
                    if sr.coding:
                        await session.flush()
                        for coding in sr.coding:
                            session.add(
                                MedicationStatementStatusReasonCoding(
                                    medication_statement_status_reason_id=sr_row.id,
                                    **_coding_kwargs(coding, org_id, actor_id),
                                )
                            )

            if "derived_from" in data:
                await session.execute(
                    delete(MedicationStatementDerivedFrom).where(
                        MedicationStatementDerivedFrom.medication_statement_pk == model.id
                    )
                )
                for df in payload.derived_from or []:
                    kwargs = _list_reference_kwargs(df, None)
                    session.add(
                        MedicationStatementDerivedFrom(
                            medication_statement_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **kwargs,
                        )
                    )

            if "reason_code" in data:
                rc_ids_subq = select(MedicationStatementReasonCode.id).where(
                    MedicationStatementReasonCode.medication_statement_pk == model.id
                )
                await session.execute(
                    delete(MedicationStatementReasonCodeCoding).where(
                        MedicationStatementReasonCodeCoding.medication_statement_reason_code_id.in_(rc_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementReasonCode).where(
                        MedicationStatementReasonCode.medication_statement_pk == model.id
                    )
                )
                for rc in payload.reason_code or []:
                    rc_row = MedicationStatementReasonCode(
                        medication_statement_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        text=rc.text,
                    )
                    session.add(rc_row)
                    if rc.coding:
                        await session.flush()
                        for coding in rc.coding:
                            session.add(
                                MedicationStatementReasonCodeCoding(
                                    medication_statement_reason_code_id=rc_row.id,
                                    **_coding_kwargs(coding, org_id, actor_id),
                                )
                            )

            if "reason_reference" in data:
                await session.execute(
                    delete(MedicationStatementReasonReference).where(
                        MedicationStatementReasonReference.medication_statement_pk == model.id
                    )
                )
                for rr in payload.reason_reference or []:
                    kwargs = _list_reference_kwargs(rr, MedicationStatementReasonReferenceType)
                    await _validate_ref(session, org_id, "reasonReference", kwargs["reference_type"], kwargs["reference_id"])
                    session.add(
                        MedicationStatementReasonReference(
                            medication_statement_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            **kwargs,
                        )
                    )

            if "note" in data:
                await session.execute(
                    delete(MedicationStatementNote).where(
                        MedicationStatementNote.medication_statement_pk == model.id
                    )
                )
                for n in payload.note or []:
                    author_kwargs = _ref_kwargs(
                        "author", n.author_reference, n.author_display, MedicationStatementNoteAuthorReferenceType
                    )
                    if n.author_reference:
                        await _validate_ref(session, org_id, "note.author", author_kwargs["author_type"], author_kwargs["author_id"])
                    session.add(
                        MedicationStatementNote(
                            medication_statement_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            text=n.text,
                            time=n.time,
                            author_string=n.author_string,
                            author_reference=n.author_reference,
                            **author_kwargs,
                            author_identifier_use=(
                                IdentifierUseModel[n.author_identifier_use.name]
                                if getattr(n, "author_identifier_use", None)
                                else None
                            ),
                            **{
                                f"author_{s}": getattr(n, f"author_{s}", None)
                                for s in _IDENTIFIER_FALLBACK_SUFFIXES
                                if s != "identifier_use"
                            },
                        )
                    )

            if "dosage" in data:
                dosage_ids_subq = select(MedicationStatementDosage.id).where(
                    MedicationStatementDosage.medication_statement_pk == model.id
                )
                ai_ids_subq = select(MedicationStatementDosageAdditionalInstruction.id).where(
                    MedicationStatementDosageAdditionalInstruction.medication_statement_dosage_id.in_(dosage_ids_subq)
                )
                await session.execute(
                    delete(MedicationStatementDosageAdditionalInstructionCoding).where(
                        MedicationStatementDosageAdditionalInstructionCoding.medication_statement_dosage_additional_instruction_id.in_(
                            ai_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosageAdditionalInstruction).where(
                        MedicationStatementDosageAdditionalInstruction.medication_statement_dosage_id.in_(dosage_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosageSiteCoding).where(
                        MedicationStatementDosageSiteCoding.medication_statement_dosage_id.in_(dosage_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosageRouteCoding).where(
                        MedicationStatementDosageRouteCoding.medication_statement_dosage_id.in_(dosage_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosageMethodCoding).where(
                        MedicationStatementDosageMethodCoding.medication_statement_dosage_id.in_(dosage_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosageAsNeededCoding).where(
                        MedicationStatementDosageAsNeededCoding.medication_statement_dosage_id.in_(dosage_ids_subq)
                    )
                )
                await session.execute(
                    delete(MedicationStatementDosage).where(
                        MedicationStatementDosage.medication_statement_pk == model.id
                    )
                )

                for d in payload.dosage or []:
                    dosage = MedicationStatementDosage(
                        medication_statement_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        sequence=d.sequence,
                        text=d.text,
                        patient_instruction=d.patient_instruction,
                        timing=d.timing,
                        as_needed_boolean=d.as_needed_boolean,
                        as_needed_codeable_concept_text=(
                            d.as_needed_codeable_concept.text if d.as_needed_codeable_concept else None
                        ),
                        site_text=d.site.text if d.site else None,
                        route_text=d.route.text if d.route else None,
                        method_text=d.method.text if d.method else None,
                        dose_and_rate=d.dose_and_rate,
                        max_dose_per_period=d.max_dose_per_period,
                        max_dose_per_administration_value=d.max_dose_per_administration_value,
                        max_dose_per_administration_unit=d.max_dose_per_administration_unit,
                        max_dose_per_administration_system=d.max_dose_per_administration_system,
                        max_dose_per_administration_code=d.max_dose_per_administration_code,
                        max_dose_per_lifetime_value=d.max_dose_per_lifetime_value,
                        max_dose_per_lifetime_unit=d.max_dose_per_lifetime_unit,
                        max_dose_per_lifetime_system=d.max_dose_per_lifetime_system,
                        max_dose_per_lifetime_code=d.max_dose_per_lifetime_code,
                    )
                    session.add(dosage)
                    await session.flush()

                    for ai in d.additional_instruction or []:
                        ai_row = MedicationStatementDosageAdditionalInstruction(
                            medication_statement_dosage_id=dosage.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            text=ai.text,
                        )
                        session.add(ai_row)
                        if ai.coding:
                            await session.flush()
                            for coding in ai.coding:
                                session.add(
                                    MedicationStatementDosageAdditionalInstructionCoding(
                                        medication_statement_dosage_additional_instruction_id=ai_row.id,
                                        **_coding_kwargs(coding, org_id, actor_id),
                                    )
                                )

                    for coding in (d.site.coding if d.site else None) or []:
                        session.add(
                            MedicationStatementDosageSiteCoding(
                                medication_statement_dosage_id=dosage.id,
                                **_coding_kwargs(coding, org_id, actor_id),
                            )
                        )

                    for coding in (d.route.coding if d.route else None) or []:
                        session.add(
                            MedicationStatementDosageRouteCoding(
                                medication_statement_dosage_id=dosage.id,
                                **_coding_kwargs(coding, org_id, actor_id),
                            )
                        )

                    for coding in (d.method.coding if d.method else None) or []:
                        session.add(
                            MedicationStatementDosageMethodCoding(
                                medication_statement_dosage_id=dosage.id,
                                **_coding_kwargs(coding, org_id, actor_id),
                            )
                        )

                    for coding in (d.as_needed_codeable_concept.coding if d.as_needed_codeable_concept else None) or []:
                        session.add(
                            MedicationStatementDosageAsNeededCoding(
                                medication_statement_dosage_id=dosage.id,
                                **_coding_kwargs(coding, org_id, actor_id),
                            )
                        )

            model.updated_by = actor_id
            await session.commit()
            return await self.get_by_medication_statement_id_in_org(medication_statement_id, org_id)

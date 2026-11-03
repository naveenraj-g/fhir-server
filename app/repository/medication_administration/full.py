from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.medication_administration import (
    MedicationAdministrationCategoryCoding,
    MedicationAdministrationContextReferenceType,
    MedicationAdministrationDevice,
    MedicationAdministrationDeviceReferenceType,
    MedicationAdministrationDosageMethodCoding,
    MedicationAdministrationDosageRouteCoding,
    MedicationAdministrationDosageSiteCoding,
    MedicationAdministrationEventHistory,
    MedicationAdministrationEventHistoryReferenceType,
    MedicationAdministrationIdentifier,
    MedicationAdministrationIdentifierTypeCoding,
    MedicationAdministrationMedicationCoding,
    MedicationAdministrationMedicationReferenceType,
    MedicationAdministrationModel,
    MedicationAdministrationNote,
    MedicationAdministrationNoteAuthorReferenceType,
    MedicationAdministrationPartOf,
    MedicationAdministrationPartOfReferenceType,
    MedicationAdministrationPerformer,
    MedicationAdministrationPerformerActorReferenceType,
    MedicationAdministrationPerformerFunctionCoding,
    MedicationAdministrationReasonCode,
    MedicationAdministrationReasonCodeCoding,
    MedicationAdministrationReasonReference,
    MedicationAdministrationReasonReferenceType,
    MedicationAdministrationRequestReferenceType,
    MedicationAdministrationStatus as MedicationAdministrationStatusModel,
    MedicationAdministrationStatusReason,
    MedicationAdministrationStatusReasonCoding,
    MedicationAdministrationSubjectReferenceType,
    MedicationAdministrationSupportingInformation,
)
from app.schemas.medication_administration import (
    MedicationAdministrationCreateSchema,
    MedicationAdministrationPatchSchema,
)

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _list_reference_kwargs,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)

_MEDICATION_FIELDS = {
    "medication_codeable_concept",
    "medication_reference",
    "medication_display",
    "medication_identifier_use",
    "medication_identifier_type_system",
    "medication_identifier_type_version",
    "medication_identifier_type_code",
    "medication_identifier_type_display",
    "medication_identifier_type_user_selected",
    "medication_identifier_type_text",
    "medication_identifier_system",
    "medication_identifier_value",
    "medication_identifier_period_start",
    "medication_identifier_period_end",
}

_EFFECTIVE_FIELDS = {"effective_date_time", "effective_period_start", "effective_period_end"}

_SUBJECT_FIELDS = {
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

_CONTEXT_FIELDS = {
    "context",
    "context_display",
    "context_identifier_use",
    "context_identifier_type_system",
    "context_identifier_type_version",
    "context_identifier_type_code",
    "context_identifier_type_display",
    "context_identifier_type_user_selected",
    "context_identifier_type_text",
    "context_identifier_system",
    "context_identifier_value",
    "context_identifier_period_start",
    "context_identifier_period_end",
}

_REQUEST_FIELDS = {
    "request",
    "request_display",
    "request_identifier_use",
    "request_identifier_type_system",
    "request_identifier_type_version",
    "request_identifier_type_code",
    "request_identifier_type_display",
    "request_identifier_type_user_selected",
    "request_identifier_type_text",
    "request_identifier_system",
    "request_identifier_value",
    "request_identifier_period_start",
    "request_identifier_period_end",
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


async def _add_identifiers(session, ma_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_ref = i.assigner
        a_type, a_id = None, None
        if a_ref:
            from app.models.enums import OrganizationReferenceType
            from app.core.filters import parse_reference
            a_type, a_id = parse_reference(a_ref, OrganizationReferenceType)
            if a_type and a_id:
                await _validate_ref(session, org_id, "identifier.assigner", a_type, a_id)

        ident = MedicationAdministrationIdentifier(
            medication_administration_pk=ma_pk,
            tenant_id=org_id,
            use=IdentifierUseModel[i.use.name] if i.use else None,
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            **_single_reference_kwargs("assigner", i, None),
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()
        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    MedicationAdministrationIdentifierTypeCoding(
                        medication_administration_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_category_codings(session, ma_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationAdministrationCategoryCoding(
                medication_administration_pk=ma_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_medication_codings(session, ma_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationAdministrationMedicationCoding(
                medication_administration_pk=ma_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_part_of(session, ma_pk: int, org_id: str, part_of, created_by: str) -> None:
    for p in part_of or []:
        kwargs = _list_reference_kwargs(p, MedicationAdministrationPartOfReferenceType)
        await _validate_ref(session, org_id, "partOf", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationAdministrationPartOf(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_status_reasons(session, ma_pk: int, org_id: str, status_reasons, created_by: str) -> None:
    for sr in status_reasons or []:
        sr_model = MedicationAdministrationStatusReason(
            medication_administration_pk=ma_pk,
            tenant_id=org_id,
            text=sr.text,
            created_by=created_by,
        )
        session.add(sr_model)
        await session.flush()
        for c in sr.coding or []:
            session.add(
                MedicationAdministrationStatusReasonCoding(
                    medication_administration_status_reason_id=sr_model.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_supporting_informations(session, ma_pk: int, org_id: str, supporting_info, created_by: str) -> None:
    for si in supporting_info or []:
        kwargs = _list_reference_kwargs(si, None)
        await _validate_ref(session, org_id, "supportingInformation", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationAdministrationSupportingInformation(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_performers(session, ma_pk: int, org_id: str, performers, created_by: str) -> None:
    for p in performers or []:
        actor_kwargs = _single_reference_kwargs("actor", p, MedicationAdministrationPerformerActorReferenceType)
        await _validate_ref(session, org_id, "performer.actor", actor_kwargs.get("actor_type"), actor_kwargs.get("actor_id"))
        perf = MedicationAdministrationPerformer(
            medication_administration_pk=ma_pk,
            tenant_id=org_id,
            function_text=p.function.text if p.function else None,
            **actor_kwargs,
            created_by=created_by,
        )
        session.add(perf)
        await session.flush()
        if p.function and p.function.coding:
            for c in p.function.coding:
                session.add(
                    MedicationAdministrationPerformerFunctionCoding(
                        medication_administration_performer_id=perf.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_reason_codes(session, ma_pk: int, org_id: str, reason_codes, created_by: str) -> None:
    for rc in reason_codes or []:
        rc_model = MedicationAdministrationReasonCode(
            medication_administration_pk=ma_pk,
            tenant_id=org_id,
            text=rc.text,
            created_by=created_by,
        )
        session.add(rc_model)
        await session.flush()
        for c in rc.coding or []:
            session.add(
                MedicationAdministrationReasonCodeCoding(
                    medication_administration_reason_code_id=rc_model.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_reason_references(session, ma_pk: int, org_id: str, reason_references, created_by: str) -> None:
    for rr in reason_references or []:
        kwargs = _list_reference_kwargs(rr, MedicationAdministrationReasonReferenceType)
        await _validate_ref(session, org_id, "reasonReference", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationAdministrationReasonReference(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_devices(session, ma_pk: int, org_id: str, devices, created_by: str) -> None:
    for d in devices or []:
        kwargs = _list_reference_kwargs(d, MedicationAdministrationDeviceReferenceType)
        await _validate_ref(session, org_id, "device", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationAdministrationDevice(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_notes(session, ma_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        author_kwargs = _single_reference_kwargs("author", n, MedicationAdministrationNoteAuthorReferenceType)
        await _validate_ref(session, org_id, "note.author", author_kwargs.get("author_type"), author_kwargs.get("author_id"))
        session.add(
            MedicationAdministrationNote(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                **author_kwargs,
                created_by=created_by,
            )
        )


async def _add_dosage_codings(session, ma_pk: int, org_id: str, dosage, created_by: str) -> None:
    if not dosage:
        return
    if dosage.site and dosage.site.coding:
        for c in dosage.site.coding:
            session.add(
                MedicationAdministrationDosageSiteCoding(
                    medication_administration_pk=ma_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
    if dosage.route and dosage.route.coding:
        for c in dosage.route.coding:
            session.add(
                MedicationAdministrationDosageRouteCoding(
                    medication_administration_pk=ma_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
    if dosage.method and dosage.method.coding:
        for c in dosage.method.coding:
            session.add(
                MedicationAdministrationDosageMethodCoding(
                    medication_administration_pk=ma_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_event_history(session, ma_pk: int, org_id: str, event_history, created_by: str) -> None:
    for eh in event_history or []:
        kwargs = _list_reference_kwargs(eh, MedicationAdministrationEventHistoryReferenceType)
        await _validate_ref(session, org_id, "eventHistory", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationAdministrationEventHistory(
                medication_administration_pk=ma_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Creation and full-update (patch) operations for MedicationAdministration."""

    async def create(
        self,
        payload: MedicationAdministrationCreateSchema,
        org_id: str,
        created_by: str,
    ) -> MedicationAdministrationModel:
        async with self.session_factory() as session:
            # Validate top-level references
            med_kwargs = _single_reference_kwargs("medication", payload, MedicationAdministrationMedicationReferenceType)
            await _validate_ref(session, org_id, "medication", med_kwargs.get("medication_type"), med_kwargs.get("medication_id"))

            subj_kwargs = _single_reference_kwargs("subject", payload, MedicationAdministrationSubjectReferenceType)
            await _validate_ref(session, org_id, "subject", subj_kwargs.get("subject_type"), subj_kwargs.get("subject_id"))

            ctx_kwargs = _single_reference_kwargs("context", payload, MedicationAdministrationContextReferenceType)
            await _validate_ref(session, org_id, "context", ctx_kwargs.get("context_type"), ctx_kwargs.get("context_id"))

            req_kwargs = _single_reference_kwargs("request", payload, MedicationAdministrationRequestReferenceType)
            await _validate_ref(session, org_id, "request", req_kwargs.get("request_type"), req_kwargs.get("request_id"))

            d = payload.dosage
            model = MedicationAdministrationModel(
                tenant_id=org_id,
                created_by=created_by,
                status=MedicationAdministrationStatusModel[payload.status.name],
                instantiates=payload.instantiates or None,
                category_text=payload.category.text if payload.category else None,
                medication_codeable_concept_text=payload.medication_codeable_concept.text if payload.medication_codeable_concept else None,
                **med_kwargs,
                **subj_kwargs,
                **ctx_kwargs,
                **req_kwargs,
                effective_date_time=payload.effective_date_time,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                dosage_text=d.text if d else None,
                dosage_site_text=d.site.text if (d and d.site) else None,
                dosage_route_text=d.route.text if (d and d.route) else None,
                dosage_method_text=d.method.text if (d and d.method) else None,
                dosage_dose_value=d.dose.value if (d and d.dose) else None,
                dosage_dose_unit=d.dose.unit if (d and d.dose) else None,
                dosage_dose_system=d.dose.system if (d and d.dose) else None,
                dosage_dose_code=d.dose.code if (d and d.dose) else None,
                dosage_rate_ratio_numerator_value=d.rate_ratio.numerator.value if (d and d.rate_ratio and d.rate_ratio.numerator) else None,
                dosage_rate_ratio_numerator_unit=d.rate_ratio.numerator.unit if (d and d.rate_ratio and d.rate_ratio.numerator) else None,
                dosage_rate_ratio_numerator_system=d.rate_ratio.numerator.system if (d and d.rate_ratio and d.rate_ratio.numerator) else None,
                dosage_rate_ratio_numerator_code=d.rate_ratio.numerator.code if (d and d.rate_ratio and d.rate_ratio.numerator) else None,
                dosage_rate_ratio_denominator_value=d.rate_ratio.denominator.value if (d and d.rate_ratio and d.rate_ratio.denominator) else None,
                dosage_rate_ratio_denominator_unit=d.rate_ratio.denominator.unit if (d and d.rate_ratio and d.rate_ratio.denominator) else None,
                dosage_rate_ratio_denominator_system=d.rate_ratio.denominator.system if (d and d.rate_ratio and d.rate_ratio.denominator) else None,
                dosage_rate_ratio_denominator_code=d.rate_ratio.denominator.code if (d and d.rate_ratio and d.rate_ratio.denominator) else None,
                dosage_rate_quantity_value=d.rate_quantity.value if (d and d.rate_quantity) else None,
                dosage_rate_quantity_unit=d.rate_quantity.unit if (d and d.rate_quantity) else None,
                dosage_rate_quantity_system=d.rate_quantity.system if (d and d.rate_quantity) else None,
                dosage_rate_quantity_code=d.rate_quantity.code if (d and d.rate_quantity) else None,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            ma_pk = model.id
            if payload.identifier:
                await _add_identifiers(session, ma_pk, org_id, payload.identifier, created_by)
            if payload.category and payload.category.coding:
                await _add_category_codings(session, ma_pk, org_id, payload.category.coding, created_by)
            if payload.medication_codeable_concept and payload.medication_codeable_concept.coding:
                await _add_medication_codings(session, ma_pk, org_id, payload.medication_codeable_concept.coding, created_by)
            if payload.part_of:
                await _add_part_of(session, ma_pk, org_id, payload.part_of, created_by)
            if payload.status_reason:
                await _add_status_reasons(session, ma_pk, org_id, payload.status_reason, created_by)
            if payload.supporting_information:
                await _add_supporting_informations(session, ma_pk, org_id, payload.supporting_information, created_by)
            if payload.performer:
                await _add_performers(session, ma_pk, org_id, payload.performer, created_by)
            if payload.reason_code:
                await _add_reason_codes(session, ma_pk, org_id, payload.reason_code, created_by)
            if payload.reason_reference:
                await _add_reason_references(session, ma_pk, org_id, payload.reason_reference, created_by)
            if payload.device:
                await _add_devices(session, ma_pk, org_id, payload.device, created_by)
            if payload.note:
                await _add_notes(session, ma_pk, org_id, payload.note, created_by)
            if payload.dosage:
                await _add_dosage_codings(session, ma_pk, org_id, payload.dosage, created_by)
            if payload.event_history:
                await _add_event_history(session, ma_pk, org_id, payload.event_history, created_by)

            await session.commit()
            return await self.get_by_medication_administration_id_in_org(
                model.medication_administration_id, org_id
            )

    async def patch(
        self,
        medication_administration_id: int,
        payload: MedicationAdministrationPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> MedicationAdministrationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationAdministrationModel).where(
                    MedicationAdministrationModel.medication_administration_id == medication_administration_id,
                    MedicationAdministrationModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            model.updated_by = updated_by
            provided = payload.model_fields_set
            ma_pk = model.id

            if "status" in provided and payload.status is not None:
                model.status = MedicationAdministrationStatusModel[payload.status.name]

            if "instantiates" in provided:
                model.instantiates = payload.instantiates

            if "extension" in provided:
                model.extension = payload.extension or []

            if provided & _EFFECTIVE_FIELDS:
                model.effective_date_time = payload.effective_date_time
                model.effective_period_start = payload.effective_period_start
                model.effective_period_end = payload.effective_period_end

            if provided & _SUBJECT_FIELDS:
                subj_kwargs = _single_reference_kwargs("subject", payload, MedicationAdministrationSubjectReferenceType)
                await _validate_ref(session, org_id, "subject", subj_kwargs.get("subject_type"), subj_kwargs.get("subject_id"))
                for k, v in subj_kwargs.items():
                    setattr(model, k, v)

            if provided & _CONTEXT_FIELDS:
                ctx_kwargs = _single_reference_kwargs("context", payload, MedicationAdministrationContextReferenceType)
                await _validate_ref(session, org_id, "context", ctx_kwargs.get("context_type"), ctx_kwargs.get("context_id"))
                for k, v in ctx_kwargs.items():
                    setattr(model, k, v)

            if provided & _REQUEST_FIELDS:
                req_kwargs = _single_reference_kwargs("request", payload, MedicationAdministrationRequestReferenceType)
                await _validate_ref(session, org_id, "request", req_kwargs.get("request_type"), req_kwargs.get("request_id"))
                for k, v in req_kwargs.items():
                    setattr(model, k, v)

            if provided & _MEDICATION_FIELDS:
                if payload.medication_codeable_concept is not None:
                    model.medication_codeable_concept_text = payload.medication_codeable_concept.text
                    med_kwargs = _single_reference_kwargs("medication", None, MedicationAdministrationMedicationReferenceType)
                    for k, v in med_kwargs.items():
                        setattr(model, k, v)
                    await session.execute(
                        delete(MedicationAdministrationMedicationCoding).where(
                            MedicationAdministrationMedicationCoding.medication_administration_pk == ma_pk
                        )
                    )
                    if payload.medication_codeable_concept.coding:
                        await _add_medication_codings(session, ma_pk, org_id, payload.medication_codeable_concept.coding, updated_by)
                elif payload.medication_reference is not None:
                    model.medication_codeable_concept_text = None
                    await session.execute(
                        delete(MedicationAdministrationMedicationCoding).where(
                            MedicationAdministrationMedicationCoding.medication_administration_pk == ma_pk
                        )
                    )
                    med_kwargs = _single_reference_kwargs("medication", payload, MedicationAdministrationMedicationReferenceType)
                    await _validate_ref(session, org_id, "medication", med_kwargs.get("medication_type"), med_kwargs.get("medication_id"))
                    for k, v in med_kwargs.items():
                        setattr(model, k, v)

            if "category" in provided:
                await session.execute(
                    delete(MedicationAdministrationCategoryCoding).where(
                        MedicationAdministrationCategoryCoding.medication_administration_pk == ma_pk
                    )
                )
                if payload.category:
                    model.category_text = payload.category.text
                    if payload.category.coding:
                        await _add_category_codings(session, ma_pk, org_id, payload.category.coding, updated_by)
                else:
                    model.category_text = None

            if "dosage" in provided:
                await session.execute(
                    delete(MedicationAdministrationDosageSiteCoding).where(
                        MedicationAdministrationDosageSiteCoding.medication_administration_pk == ma_pk
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationDosageRouteCoding).where(
                        MedicationAdministrationDosageRouteCoding.medication_administration_pk == ma_pk
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationDosageMethodCoding).where(
                        MedicationAdministrationDosageMethodCoding.medication_administration_pk == ma_pk
                    )
                )
                d = payload.dosage
                if d:
                    model.dosage_text = d.text
                    model.dosage_site_text = d.site.text if d.site else None
                    model.dosage_route_text = d.route.text if d.route else None
                    model.dosage_method_text = d.method.text if d.method else None
                    model.dosage_dose_value = d.dose.value if d.dose else None
                    model.dosage_dose_unit = d.dose.unit if d.dose else None
                    model.dosage_dose_system = d.dose.system if d.dose else None
                    model.dosage_dose_code = d.dose.code if d.dose else None
                    model.dosage_rate_ratio_numerator_value = d.rate_ratio.numerator.value if (d.rate_ratio and d.rate_ratio.numerator) else None
                    model.dosage_rate_ratio_numerator_unit = d.rate_ratio.numerator.unit if (d.rate_ratio and d.rate_ratio.numerator) else None
                    model.dosage_rate_ratio_numerator_system = d.rate_ratio.numerator.system if (d.rate_ratio and d.rate_ratio.numerator) else None
                    model.dosage_rate_ratio_numerator_code = d.rate_ratio.numerator.code if (d.rate_ratio and d.rate_ratio.numerator) else None
                    model.dosage_rate_ratio_denominator_value = d.rate_ratio.denominator.value if (d.rate_ratio and d.rate_ratio.denominator) else None
                    model.dosage_rate_ratio_denominator_unit = d.rate_ratio.denominator.unit if (d.rate_ratio and d.rate_ratio.denominator) else None
                    model.dosage_rate_ratio_denominator_system = d.rate_ratio.denominator.system if (d.rate_ratio and d.rate_ratio.denominator) else None
                    model.dosage_rate_ratio_denominator_code = d.rate_ratio.denominator.code if (d.rate_ratio and d.rate_ratio.denominator) else None
                    model.dosage_rate_quantity_value = d.rate_quantity.value if d.rate_quantity else None
                    model.dosage_rate_quantity_unit = d.rate_quantity.unit if d.rate_quantity else None
                    model.dosage_rate_quantity_system = d.rate_quantity.system if d.rate_quantity else None
                    model.dosage_rate_quantity_code = d.rate_quantity.code if d.rate_quantity else None
                    await _add_dosage_codings(session, ma_pk, org_id, d, updated_by)
                else:
                    model.dosage_text = None
                    model.dosage_site_text = None
                    model.dosage_route_text = None
                    model.dosage_method_text = None
                    model.dosage_dose_value = None
                    model.dosage_dose_unit = None
                    model.dosage_dose_system = None
                    model.dosage_dose_code = None
                    model.dosage_rate_ratio_numerator_value = None
                    model.dosage_rate_ratio_numerator_unit = None
                    model.dosage_rate_ratio_numerator_system = None
                    model.dosage_rate_ratio_numerator_code = None
                    model.dosage_rate_ratio_denominator_value = None
                    model.dosage_rate_ratio_denominator_unit = None
                    model.dosage_rate_ratio_denominator_system = None
                    model.dosage_rate_ratio_denominator_code = None
                    model.dosage_rate_quantity_value = None
                    model.dosage_rate_quantity_unit = None
                    model.dosage_rate_quantity_system = None
                    model.dosage_rate_quantity_code = None

            if "identifier" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(MedicationAdministrationIdentifierTypeCoding).where(
                        MedicationAdministrationIdentifierTypeCoding.medication_administration_identifier_id.in_(
                            select(MedicationAdministrationIdentifier.id).where(
                                MedicationAdministrationIdentifier.medication_administration_pk == ma_pk
                            )
                        )
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationIdentifier).where(
                        MedicationAdministrationIdentifier.medication_administration_pk == ma_pk
                    )
                )
                if payload.identifier:
                    await _add_identifiers(session, ma_pk, org_id, payload.identifier, updated_by)

            if "part_of" in provided:
                await session.execute(
                    delete(MedicationAdministrationPartOf).where(
                        MedicationAdministrationPartOf.medication_administration_pk == ma_pk
                    )
                )
                if payload.part_of:
                    await _add_part_of(session, ma_pk, org_id, payload.part_of, updated_by)

            if "status_reason" in provided:
                await session.execute(
                    delete(MedicationAdministrationStatusReasonCoding).where(
                        MedicationAdministrationStatusReasonCoding.medication_administration_status_reason_id.in_(
                            select(MedicationAdministrationStatusReason.id).where(
                                MedicationAdministrationStatusReason.medication_administration_pk == ma_pk
                            )
                        )
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationStatusReason).where(
                        MedicationAdministrationStatusReason.medication_administration_pk == ma_pk
                    )
                )
                if payload.status_reason:
                    await _add_status_reasons(session, ma_pk, org_id, payload.status_reason, updated_by)

            if "supporting_information" in provided:
                await session.execute(
                    delete(MedicationAdministrationSupportingInformation).where(
                        MedicationAdministrationSupportingInformation.medication_administration_pk == ma_pk
                    )
                )
                if payload.supporting_information:
                    await _add_supporting_informations(session, ma_pk, org_id, payload.supporting_information, updated_by)

            if "performer" in provided:
                await session.execute(
                    delete(MedicationAdministrationPerformerFunctionCoding).where(
                        MedicationAdministrationPerformerFunctionCoding.medication_administration_performer_id.in_(
                            select(MedicationAdministrationPerformer.id).where(
                                MedicationAdministrationPerformer.medication_administration_pk == ma_pk
                            )
                        )
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationPerformer).where(
                        MedicationAdministrationPerformer.medication_administration_pk == ma_pk
                    )
                )
                if payload.performer:
                    await _add_performers(session, ma_pk, org_id, payload.performer, updated_by)

            if "reason_code" in provided:
                await session.execute(
                    delete(MedicationAdministrationReasonCodeCoding).where(
                        MedicationAdministrationReasonCodeCoding.medication_administration_reason_code_id.in_(
                            select(MedicationAdministrationReasonCode.id).where(
                                MedicationAdministrationReasonCode.medication_administration_pk == ma_pk
                            )
                        )
                    )
                )
                await session.execute(
                    delete(MedicationAdministrationReasonCode).where(
                        MedicationAdministrationReasonCode.medication_administration_pk == ma_pk
                    )
                )
                if payload.reason_code:
                    await _add_reason_codes(session, ma_pk, org_id, payload.reason_code, updated_by)

            if "reason_reference" in provided:
                await session.execute(
                    delete(MedicationAdministrationReasonReference).where(
                        MedicationAdministrationReasonReference.medication_administration_pk == ma_pk
                    )
                )
                if payload.reason_reference:
                    await _add_reason_references(session, ma_pk, org_id, payload.reason_reference, updated_by)

            if "device" in provided:
                await session.execute(
                    delete(MedicationAdministrationDevice).where(
                        MedicationAdministrationDevice.medication_administration_pk == ma_pk
                    )
                )
                if payload.device:
                    await _add_devices(session, ma_pk, org_id, payload.device, updated_by)

            if "note" in provided:
                await session.execute(
                    delete(MedicationAdministrationNote).where(
                        MedicationAdministrationNote.medication_administration_pk == ma_pk
                    )
                )
                if payload.note:
                    await _add_notes(session, ma_pk, org_id, payload.note, updated_by)

            if "event_history" in provided:
                await session.execute(
                    delete(MedicationAdministrationEventHistory).where(
                        MedicationAdministrationEventHistory.medication_administration_pk == ma_pk
                    )
                )
                if payload.event_history:
                    await _add_event_history(session, ma_pk, org_id, payload.event_history, updated_by)

            await session.commit()
            return await self.get_by_medication_administration_id_in_org(
                model.medication_administration_id, org_id
            )

    create_full = create
    patch_full = patch


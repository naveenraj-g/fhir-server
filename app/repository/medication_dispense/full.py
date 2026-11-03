from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.medication_dispense import (
    MedicationDispenseAuthorizingPrescription,
    MedicationDispenseAuthorizingPrescriptionReferenceType,
    MedicationDispenseCategoryCoding,
    MedicationDispenseContextReferenceType,
    MedicationDispenseDestinationReferenceType,
    MedicationDispenseDetectedIssue,
    MedicationDispenseDetectedIssueReferenceType,
    MedicationDispenseDosageAdditionalInstruction,
    MedicationDispenseDosageAdditionalInstructionCoding,
    MedicationDispenseDosageAsNeededCoding,
    MedicationDispenseDosageInstruction,
    MedicationDispenseDosageMethodCoding,
    MedicationDispenseDosageRouteCoding,
    MedicationDispenseDosageSiteCoding,
    MedicationDispenseEventHistory,
    MedicationDispenseEventHistoryReferenceType,
    MedicationDispenseIdentifier,
    MedicationDispenseIdentifierTypeCoding,
    MedicationDispenseLocationReferenceType,
    MedicationDispenseMedicationCoding,
    MedicationDispenseMedicationReferenceType,
    MedicationDispenseModel,
    MedicationDispenseNote,
    MedicationDispenseNoteAuthorReferenceType,
    MedicationDispensePartOf,
    MedicationDispensePartOfReferenceType,
    MedicationDispensePerformer,
    MedicationDispensePerformerActorReferenceType,
    MedicationDispensePerformerFunctionCoding,
    MedicationDispenseReceiver,
    MedicationDispenseReceiverReferenceType,
    MedicationDispenseStatus as MedicationDispenseStatusModel,
    MedicationDispenseStatusReasonCoding,
    MedicationDispenseStatusReasonReferenceType,
    MedicationDispenseSubjectReferenceType,
    MedicationDispenseSubstitutionReason,
    MedicationDispenseSubstitutionReasonCoding,
    MedicationDispenseSubstitutionResponsibleParty,
    MedicationDispenseSubstitutionResponsiblePartyReferenceType,
    MedicationDispenseSubstitutionTypeCoding,
    MedicationDispenseSupportingInfo,
    MedicationDispenseTypeCoding,
)
from app.schemas.medication_dispense import (
    MedicationDispenseCreateSchema,
    MedicationDispensePatchSchema,
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

_STATUS_REASON_FIELDS = {
    "status_reason_codeable_concept",
    "status_reason_reference",
    "status_reason_reference_display",
    "status_reason_reference_identifier_use",
    "status_reason_reference_identifier_type_system",
    "status_reason_reference_identifier_type_version",
    "status_reason_reference_identifier_type_code",
    "status_reason_reference_identifier_type_display",
    "status_reason_reference_identifier_type_user_selected",
    "status_reason_reference_identifier_type_text",
    "status_reason_reference_identifier_system",
    "status_reason_reference_identifier_value",
    "status_reason_reference_identifier_period_start",
    "status_reason_reference_identifier_period_end",
}

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

_LOCATION_FIELDS = {
    "location",
    "location_display",
    "location_identifier_use",
    "location_identifier_type_system",
    "location_identifier_type_version",
    "location_identifier_type_code",
    "location_identifier_type_display",
    "location_identifier_type_user_selected",
    "location_identifier_type_text",
    "location_identifier_system",
    "location_identifier_value",
    "location_identifier_period_start",
    "location_identifier_period_end",
}

_DESTINATION_FIELDS = {
    "destination",
    "destination_display",
    "destination_identifier_use",
    "destination_identifier_type_system",
    "destination_identifier_type_version",
    "destination_identifier_type_code",
    "destination_identifier_type_display",
    "destination_identifier_type_user_selected",
    "destination_identifier_type_text",
    "destination_identifier_system",
    "destination_identifier_value",
    "destination_identifier_period_start",
    "destination_identifier_period_end",
}

_QUANTITY_FIELDS = {"quantity_value", "quantity_unit", "quantity_system", "quantity_code"}
_DAYS_SUPPLY_FIELDS = {"days_supply_value", "days_supply_unit", "days_supply_system", "days_supply_code"}


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


async def _add_identifiers(session, md_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_ref = i.assigner
        a_type, a_id = None, None
        if a_ref:
            from app.core.filters import parse_reference
            from app.models.enums import OrganizationReferenceType

            a_type, a_id = parse_reference(a_ref, OrganizationReferenceType)
            if a_type and a_id:
                await _validate_ref(session, org_id, "identifier.assigner", a_type, a_id)

        ident = MedicationDispenseIdentifier(
            medication_dispense_pk=md_pk,
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
                    MedicationDispenseIdentifierTypeCoding(
                        medication_dispense_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_category_codings(session, md_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationDispenseCategoryCoding(
                medication_dispense_pk=md_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_medication_codings(session, md_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationDispenseMedicationCoding(
                medication_dispense_pk=md_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_status_reason_codings(session, md_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationDispenseStatusReasonCoding(
                medication_dispense_pk=md_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_type_codings(session, md_pk: int, org_id: str, codings, created_by: str) -> None:
    for c in codings or []:
        session.add(
            MedicationDispenseTypeCoding(
                medication_dispense_pk=md_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_part_of(session, md_pk: int, org_id: str, part_of, created_by: str) -> None:
    for p in part_of or []:
        kwargs = _list_reference_kwargs(p, MedicationDispensePartOfReferenceType)
        await _validate_ref(session, org_id, "partOf", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispensePartOf(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_supporting_informations(session, md_pk: int, org_id: str, supporting_info, created_by: str) -> None:
    for si in supporting_info or []:
        kwargs = _list_reference_kwargs(si, None)
        await _validate_ref(session, org_id, "supportingInformation", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseSupportingInfo(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_performers(session, md_pk: int, org_id: str, performers, created_by: str) -> None:
    for p in performers or []:
        actor_kwargs = _single_reference_kwargs("actor", p, MedicationDispensePerformerActorReferenceType)
        await _validate_ref(session, org_id, "performer.actor", actor_kwargs.get("actor_type"), actor_kwargs.get("actor_id"))
        perf = MedicationDispensePerformer(
            medication_dispense_pk=md_pk,
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
                    MedicationDispensePerformerFunctionCoding(
                        medication_dispense_performer_id=perf.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_authorizing_prescriptions(session, md_pk: int, org_id: str, authorizing_prescriptions, created_by: str) -> None:
    for a in authorizing_prescriptions or []:
        kwargs = _list_reference_kwargs(a, MedicationDispenseAuthorizingPrescriptionReferenceType)
        await _validate_ref(session, org_id, "authorizingPrescription", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseAuthorizingPrescription(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_receivers(session, md_pk: int, org_id: str, receivers, created_by: str) -> None:
    for r in receivers or []:
        kwargs = _list_reference_kwargs(r, MedicationDispenseReceiverReferenceType)
        await _validate_ref(session, org_id, "receiver", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseReceiver(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_notes(session, md_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        author_kwargs = _single_reference_kwargs("author", n, MedicationDispenseNoteAuthorReferenceType)
        await _validate_ref(session, org_id, "note.author", author_kwargs.get("author_type"), author_kwargs.get("author_id"))
        session.add(
            MedicationDispenseNote(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                **author_kwargs,
                created_by=created_by,
            )
        )


async def _add_dosage_instructions(session, md_pk: int, org_id: str, dosage_instructions, created_by: str) -> None:
    for d in dosage_instructions or []:
        dosage = MedicationDispenseDosageInstruction(
            medication_dispense_pk=md_pk,
            tenant_id=org_id,
            created_by=created_by,
            sequence=d.sequence,
            text=d.text,
            patient_instruction=d.patient_instruction,
            timing=d.timing,
            as_needed_boolean=d.as_needed_boolean,
            as_needed_codeable_concept_text=d.as_needed_codeable_concept.text if d.as_needed_codeable_concept else None,
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
            ai_row = MedicationDispenseDosageAdditionalInstruction(
                medication_dispense_dosage_instruction_id=dosage.id,
                tenant_id=org_id,
                created_by=created_by,
                text=ai.text,
            )
            session.add(ai_row)
            if ai.coding:
                await session.flush()
                for c in ai.coding:
                    session.add(
                        MedicationDispenseDosageAdditionalInstructionCoding(
                            medication_dispense_dosage_additional_instruction_id=ai_row.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

        for c in (d.site.coding if d.site else None) or []:
            session.add(
                MedicationDispenseDosageSiteCoding(
                    medication_dispense_dosage_instruction_id=dosage.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
        for c in (d.route.coding if d.route else None) or []:
            session.add(
                MedicationDispenseDosageRouteCoding(
                    medication_dispense_dosage_instruction_id=dosage.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
        for c in (d.method.coding if d.method else None) or []:
            session.add(
                MedicationDispenseDosageMethodCoding(
                    medication_dispense_dosage_instruction_id=dosage.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
        for c in (d.as_needed_codeable_concept.coding if d.as_needed_codeable_concept else None) or []:
            session.add(
                MedicationDispenseDosageAsNeededCoding(
                    medication_dispense_dosage_instruction_id=dosage.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_substitution_elements(
    session, md_pk: int, org_id: str, sub: MedicationDispenseSubstitutionInput | None, created_by: str
) -> None:
    if not sub:
        return

    if sub.type and sub.type.coding:
        for c in sub.type.coding:
            session.add(
                MedicationDispenseSubstitutionTypeCoding(
                    medication_dispense_pk=md_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )

    for r in sub.reason or []:
        reason_row = MedicationDispenseSubstitutionReason(
            medication_dispense_pk=md_pk,
            tenant_id=org_id,
            text=r.text,
            created_by=created_by,
        )
        session.add(reason_row)
        await session.flush()
        for c in r.coding or []:
            session.add(
                MedicationDispenseSubstitutionReasonCoding(
                    medication_dispense_substitution_reason_id=reason_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )

    for rp in sub.responsible_party or []:
        kwargs = _list_reference_kwargs(rp, MedicationDispenseSubstitutionResponsiblePartyReferenceType)
        await _validate_ref(session, org_id, "substitution.responsibleParty", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseSubstitutionResponsibleParty(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_detected_issues(session, md_pk: int, org_id: str, detected_issues, created_by: str) -> None:
    for di in detected_issues or []:
        kwargs = _list_reference_kwargs(di, MedicationDispenseDetectedIssueReferenceType)
        await _validate_ref(session, org_id, "detectedIssue", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseDetectedIssue(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


async def _add_event_history(session, md_pk: int, org_id: str, event_history, created_by: str) -> None:
    for eh in event_history or []:
        kwargs = _list_reference_kwargs(eh, MedicationDispenseEventHistoryReferenceType)
        await _validate_ref(session, org_id, "eventHistory", kwargs.get("reference_type"), kwargs.get("reference_id"))
        session.add(
            MedicationDispenseEventHistory(
                medication_dispense_pk=md_pk,
                tenant_id=org_id,
                **kwargs,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Atomic write operations (create_full / patch_full) for MedicationDispense."""

    async def create_full(
        self,
        payload: MedicationDispenseCreateSchema,
        org_id: str,
        created_by: str,
    ) -> MedicationDispenseModel:
        async with self.session_factory() as session:
            # 1. Resolve & validate single references
            status_reason_ref_kwargs = _single_reference_kwargs(
                "status_reason_reference", payload, MedicationDispenseStatusReasonReferenceType
            )
            await _validate_ref(
                session, org_id, "statusReasonReference",
                status_reason_ref_kwargs.get("status_reason_reference_type"),
                status_reason_ref_kwargs.get("status_reason_reference_id"),
            )

            medication_kwargs = _single_reference_kwargs(
                "medication", payload, MedicationDispenseMedicationReferenceType
            )
            await _validate_ref(
                session, org_id, "medicationReference",
                medication_kwargs.get("medication_type"),
                medication_kwargs.get("medication_id"),
            )

            subject_kwargs = _single_reference_kwargs(
                "subject", payload, MedicationDispenseSubjectReferenceType
            )
            await _validate_ref(
                session, org_id, "subject",
                subject_kwargs.get("subject_type"),
                subject_kwargs.get("subject_id"),
            )

            context_kwargs = _single_reference_kwargs(
                "context", payload, MedicationDispenseContextReferenceType
            )
            await _validate_ref(
                session, org_id, "context",
                context_kwargs.get("context_type"),
                context_kwargs.get("context_id"),
            )

            location_kwargs = _single_reference_kwargs(
                "location", payload, MedicationDispenseLocationReferenceType
            )
            await _validate_ref(
                session, org_id, "location",
                location_kwargs.get("location_type"),
                location_kwargs.get("location_id"),
            )

            destination_kwargs = _single_reference_kwargs(
                "destination", payload, MedicationDispenseDestinationReferenceType
            )
            await _validate_ref(
                session, org_id, "destination",
                destination_kwargs.get("destination_type"),
                destination_kwargs.get("destination_id"),
            )

            # 2. Instantiate main row
            md = MedicationDispenseModel(
                tenant_id=org_id,
                created_by=created_by,
                status=MedicationDispenseStatusModel[payload.status.name],
                status_reason_codeable_concept_text=(
                    payload.status_reason_codeable_concept.text
                    if payload.status_reason_codeable_concept
                    else None
                ),
                **status_reason_ref_kwargs,
                category_text=payload.category.text if payload.category else None,
                medication_codeable_concept_text=(
                    payload.medication_codeable_concept.text
                    if payload.medication_codeable_concept
                    else None
                ),
                **medication_kwargs,
                **subject_kwargs,
                **context_kwargs,
                **location_kwargs,
                type_text=payload.type.text if payload.type else None,
                quantity_value=payload.quantity_value,
                quantity_unit=payload.quantity_unit,
                quantity_system=payload.quantity_system,
                quantity_code=payload.quantity_code,
                days_supply_value=payload.days_supply_value,
                days_supply_unit=payload.days_supply_unit,
                days_supply_system=payload.days_supply_system,
                days_supply_code=payload.days_supply_code,
                when_prepared=payload.when_prepared,
                when_handed_over=payload.when_handed_over,
                **destination_kwargs,
                substitution_was_substituted=(
                    payload.substitution.was_substituted if payload.substitution else None
                ),
                substitution_type_text=(
                    payload.substitution.type.text
                    if payload.substitution and payload.substitution.type
                    else None
                ),
                extension=payload.extension if payload.extension is not None else [],
            )
            session.add(md)
            await session.flush()

            # 3. Add sub-resources
            await _add_identifiers(session, md.id, org_id, payload.identifier, created_by)
            await _add_part_of(session, md.id, org_id, payload.part_of, created_by)
            if payload.status_reason_codeable_concept and payload.status_reason_codeable_concept.coding:
                await _add_status_reason_codings(
                    session, md.id, org_id, payload.status_reason_codeable_concept.coding, created_by
                )
            if payload.category and payload.category.coding:
                await _add_category_codings(session, md.id, org_id, payload.category.coding, created_by)
            if payload.medication_codeable_concept and payload.medication_codeable_concept.coding:
                await _add_medication_codings(
                    session, md.id, org_id, payload.medication_codeable_concept.coding, created_by
                )
            await _add_supporting_informations(session, md.id, org_id, payload.supporting_information, created_by)
            await _add_performers(session, md.id, org_id, payload.performer, created_by)
            await _add_authorizing_prescriptions(session, md.id, org_id, payload.authorizing_prescription, created_by)
            if payload.type and payload.type.coding:
                await _add_type_codings(session, md.id, org_id, payload.type.coding, created_by)
            await _add_receivers(session, md.id, org_id, payload.receiver, created_by)
            await _add_notes(session, md.id, org_id, payload.note, created_by)
            await _add_dosage_instructions(session, md.id, org_id, payload.dosage_instruction, created_by)
            if payload.substitution:
                await _add_substitution_elements(session, md.id, org_id, payload.substitution, created_by)
            await _add_detected_issues(session, md.id, org_id, payload.detected_issue, created_by)
            await _add_event_history(session, md.id, org_id, payload.event_history, created_by)

            await session.commit()
            pub_id = md.medication_dispense_id

        # Reload with relationships in a fresh session
        return await self.get_by_medication_dispense_id_in_org(pub_id, org_id)

    async def patch_full(
        self,
        medication_dispense_id: int,
        payload: MedicationDispensePatchSchema,
        org_id: str,
        updated_by: str,
    ) -> MedicationDispenseModel | None:
        async with self.session_factory() as session:
            stmt = select(MedicationDispenseModel).where(
                MedicationDispenseModel.medication_dispense_id == medication_dispense_id,
                MedicationDispenseModel.tenant_id == org_id,
            )
            md = (await session.execute(stmt)).scalar_one_or_none()
            if not md:
                return None

            provided = payload.model_fields_set
            md.updated_by = updated_by

            if "status" in provided and payload.status is not None:
                md.status = MedicationDispenseStatusModel[payload.status.name]

            if provided & _STATUS_REASON_FIELDS:
                if "status_reason_codeable_concept" in provided:
                    md.status_reason_codeable_concept_text = (
                        payload.status_reason_codeable_concept.text
                        if payload.status_reason_codeable_concept
                        else None
                    )
                    await session.execute(
                        delete(MedicationDispenseStatusReasonCoding).where(
                            MedicationDispenseStatusReasonCoding.medication_dispense_pk == md.id
                        )
                    )
                    if (
                        payload.status_reason_codeable_concept
                        and payload.status_reason_codeable_concept.coding
                    ):
                        await _add_status_reason_codings(
                            session, md.id, org_id, payload.status_reason_codeable_concept.coding, updated_by
                        )
                status_reason_ref_kwargs = _single_reference_kwargs(
                    "status_reason_reference", payload, MedicationDispenseStatusReasonReferenceType
                )
                await _validate_ref(
                    session, org_id, "statusReasonReference",
                    status_reason_ref_kwargs.get("status_reason_reference_type"),
                    status_reason_ref_kwargs.get("status_reason_reference_id"),
                )
                for k, v in status_reason_ref_kwargs.items():
                    setattr(md, k, v)

            if "category" in provided:
                md.category_text = payload.category.text if payload.category else None
                await session.execute(
                    delete(MedicationDispenseCategoryCoding).where(
                        MedicationDispenseCategoryCoding.medication_dispense_pk == md.id
                    )
                )
                if payload.category and payload.category.coding:
                    await _add_category_codings(session, md.id, org_id, payload.category.coding, updated_by)

            if provided & _MEDICATION_FIELDS:
                if "medication_codeable_concept" in provided:
                    md.medication_codeable_concept_text = (
                        payload.medication_codeable_concept.text
                        if payload.medication_codeable_concept
                        else None
                    )
                    await session.execute(
                        delete(MedicationDispenseMedicationCoding).where(
                            MedicationDispenseMedicationCoding.medication_dispense_pk == md.id
                        )
                    )
                    if (
                        payload.medication_codeable_concept
                        and payload.medication_codeable_concept.coding
                    ):
                        await _add_medication_codings(
                            session, md.id, org_id, payload.medication_codeable_concept.coding, updated_by
                        )
                med_kwargs = _single_reference_kwargs(
                    "medication", payload, MedicationDispenseMedicationReferenceType
                )
                await _validate_ref(
                    session, org_id, "medicationReference",
                    med_kwargs.get("medication_type"),
                    med_kwargs.get("medication_id"),
                )
                for k, v in med_kwargs.items():
                    setattr(md, k, v)

            if provided & _SUBJECT_FIELDS:
                subject_kwargs = _single_reference_kwargs(
                    "subject", payload, MedicationDispenseSubjectReferenceType
                )
                await _validate_ref(
                    session, org_id, "subject",
                    subject_kwargs.get("subject_type"),
                    subject_kwargs.get("subject_id"),
                )
                for k, v in subject_kwargs.items():
                    setattr(md, k, v)

            if provided & _CONTEXT_FIELDS:
                context_kwargs = _single_reference_kwargs(
                    "context", payload, MedicationDispenseContextReferenceType
                )
                await _validate_ref(
                    session, org_id, "context",
                    context_kwargs.get("context_type"),
                    context_kwargs.get("context_id"),
                )
                for k, v in context_kwargs.items():
                    setattr(md, k, v)

            if provided & _LOCATION_FIELDS:
                location_kwargs = _single_reference_kwargs(
                    "location", payload, MedicationDispenseLocationReferenceType
                )
                await _validate_ref(
                    session, org_id, "location",
                    location_kwargs.get("location_type"),
                    location_kwargs.get("location_id"),
                )
                for k, v in location_kwargs.items():
                    setattr(md, k, v)

            if "type" in provided:
                md.type_text = payload.type.text if payload.type else None
                await session.execute(
                    delete(MedicationDispenseTypeCoding).where(
                        MedicationDispenseTypeCoding.medication_dispense_pk == md.id
                    )
                )
                if payload.type and payload.type.coding:
                    await _add_type_codings(session, md.id, org_id, payload.type.coding, updated_by)

            if provided & _QUANTITY_FIELDS:
                md.quantity_value = payload.quantity_value
                md.quantity_unit = payload.quantity_unit
                md.quantity_system = payload.quantity_system
                md.quantity_code = payload.quantity_code

            if provided & _DAYS_SUPPLY_FIELDS:
                md.days_supply_value = payload.days_supply_value
                md.days_supply_unit = payload.days_supply_unit
                md.days_supply_system = payload.days_supply_system
                md.days_supply_code = payload.days_supply_code

            if "when_prepared" in provided:
                md.when_prepared = payload.when_prepared

            if "when_handed_over" in provided:
                md.when_handed_over = payload.when_handed_over

            if provided & _DESTINATION_FIELDS:
                destination_kwargs = _single_reference_kwargs(
                    "destination", payload, MedicationDispenseDestinationReferenceType
                )
                await _validate_ref(
                    session, org_id, "destination",
                    destination_kwargs.get("destination_type"),
                    destination_kwargs.get("destination_id"),
                )
                for k, v in destination_kwargs.items():
                    setattr(md, k, v)

            if "substitution" in provided:
                md.substitution_was_substituted = (
                    payload.substitution.was_substituted if payload.substitution else None
                )
                md.substitution_type_text = (
                    payload.substitution.type.text
                    if payload.substitution and payload.substitution.type
                    else None
                )
                await session.execute(
                    delete(MedicationDispenseSubstitutionTypeCoding).where(
                        MedicationDispenseSubstitutionTypeCoding.medication_dispense_pk == md.id
                    )
                )
                # Delete grandchild reasons first
                sub_reason_ids_subq = select(MedicationDispenseSubstitutionReason.id).where(
                    MedicationDispenseSubstitutionReason.medication_dispense_pk == md.id
                )
                await session.execute(
                    delete(MedicationDispenseSubstitutionReasonCoding).where(
                        MedicationDispenseSubstitutionReasonCoding.medication_dispense_substitution_reason_id.in_(
                            sub_reason_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseSubstitutionReason).where(
                        MedicationDispenseSubstitutionReason.medication_dispense_pk == md.id
                    )
                )
                await session.execute(
                    delete(MedicationDispenseSubstitutionResponsibleParty).where(
                        MedicationDispenseSubstitutionResponsibleParty.medication_dispense_pk == md.id
                    )
                )
                if payload.substitution:
                    await _add_substitution_elements(session, md.id, org_id, payload.substitution, updated_by)

            if "extension" in provided:
                md.extension = list(payload.extension) if payload.extension is not None else []

            # 0..* collections
            if "identifier" in provided:
                ident_ids_subq = select(MedicationDispenseIdentifier.id).where(
                    MedicationDispenseIdentifier.medication_dispense_pk == md.id
                )
                await session.execute(
                    delete(MedicationDispenseIdentifierTypeCoding).where(
                        MedicationDispenseIdentifierTypeCoding.medication_dispense_identifier_id.in_(
                            ident_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseIdentifier).where(
                        MedicationDispenseIdentifier.medication_dispense_pk == md.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(session, md.id, org_id, payload.identifier, updated_by)

            if "part_of" in provided:
                await session.execute(
                    delete(MedicationDispensePartOf).where(
                        MedicationDispensePartOf.medication_dispense_pk == md.id
                    )
                )
                if payload.part_of:
                    await _add_part_of(session, md.id, org_id, payload.part_of, updated_by)

            if "supporting_information" in provided:
                await session.execute(
                    delete(MedicationDispenseSupportingInfo).where(
                        MedicationDispenseSupportingInfo.medication_dispense_pk == md.id
                    )
                )
                if payload.supporting_information:
                    await _add_supporting_informations(
                        session, md.id, org_id, payload.supporting_information, updated_by
                    )

            if "performer" in provided:
                perf_ids_subq = select(MedicationDispensePerformer.id).where(
                    MedicationDispensePerformer.medication_dispense_pk == md.id
                )
                await session.execute(
                    delete(MedicationDispensePerformerFunctionCoding).where(
                        MedicationDispensePerformerFunctionCoding.medication_dispense_performer_id.in_(
                            perf_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispensePerformer).where(
                        MedicationDispensePerformer.medication_dispense_pk == md.id
                    )
                )
                if payload.performer:
                    await _add_performers(session, md.id, org_id, payload.performer, updated_by)

            if "authorizing_prescription" in provided:
                await session.execute(
                    delete(MedicationDispenseAuthorizingPrescription).where(
                        MedicationDispenseAuthorizingPrescription.medication_dispense_pk == md.id
                    )
                )
                if payload.authorizing_prescription:
                    await _add_authorizing_prescriptions(
                        session, md.id, org_id, payload.authorizing_prescription, updated_by
                    )

            if "receiver" in provided:
                await session.execute(
                    delete(MedicationDispenseReceiver).where(
                        MedicationDispenseReceiver.medication_dispense_pk == md.id
                    )
                )
                if payload.receiver:
                    await _add_receivers(session, md.id, org_id, payload.receiver, updated_by)

            if "note" in provided:
                await session.execute(
                    delete(MedicationDispenseNote).where(
                        MedicationDispenseNote.medication_dispense_pk == md.id
                    )
                )
                if payload.note:
                    await _add_notes(session, md.id, org_id, payload.note, updated_by)

            if "dosage_instruction" in provided:
                dosage_ids_subq = select(MedicationDispenseDosageInstruction.id).where(
                    MedicationDispenseDosageInstruction.medication_dispense_pk == md.id
                )
                ai_ids_subq = select(MedicationDispenseDosageAdditionalInstruction.id).where(
                    MedicationDispenseDosageAdditionalInstruction.medication_dispense_dosage_instruction_id.in_(
                        dosage_ids_subq
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageAdditionalInstructionCoding).where(
                        MedicationDispenseDosageAdditionalInstructionCoding.medication_dispense_dosage_additional_instruction_id.in_(
                            ai_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageAdditionalInstruction).where(
                        MedicationDispenseDosageAdditionalInstruction.medication_dispense_dosage_instruction_id.in_(
                            dosage_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageSiteCoding).where(
                        MedicationDispenseDosageSiteCoding.medication_dispense_dosage_instruction_id.in_(
                            dosage_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageRouteCoding).where(
                        MedicationDispenseDosageRouteCoding.medication_dispense_dosage_instruction_id.in_(
                            dosage_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageMethodCoding).where(
                        MedicationDispenseDosageMethodCoding.medication_dispense_dosage_instruction_id.in_(
                            dosage_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageAsNeededCoding).where(
                        MedicationDispenseDosageAsNeededCoding.medication_dispense_dosage_instruction_id.in_(
                            dosage_ids_subq
                        )
                    )
                )
                await session.execute(
                    delete(MedicationDispenseDosageInstruction).where(
                        MedicationDispenseDosageInstruction.medication_dispense_pk == md.id
                    )
                )
                if payload.dosage_instruction:
                    await _add_dosage_instructions(
                        session, md.id, org_id, payload.dosage_instruction, updated_by
                    )

            if "detected_issue" in provided:
                await session.execute(
                    delete(MedicationDispenseDetectedIssue).where(
                        MedicationDispenseDetectedIssue.medication_dispense_pk == md.id
                    )
                )
                if payload.detected_issue:
                    await _add_detected_issues(session, md.id, org_id, payload.detected_issue, updated_by)

            if "event_history" in provided:
                await session.execute(
                    delete(MedicationDispenseEventHistory).where(
                        MedicationDispenseEventHistory.medication_dispense_pk == md.id
                    )
                )
                if payload.event_history:
                    await _add_event_history(session, md.id, org_id, payload.event_history, updated_by)

            await session.commit()

        return await self.get_by_medication_dispense_id_in_org(medication_dispense_id, org_id)

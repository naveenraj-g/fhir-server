from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import EncounterReferenceType, MedicationRequestReferenceType, OrganizationReferenceType, SubjectReferenceType
from app.models.medication_request import (
    MedicationRequestBasedOn,
    MedicationRequestBasedOnReferenceType,
    MedicationRequestCategory,
    MedicationRequestCategoryCoding,
    MedicationRequestCourseOfTherapyTypeCoding,
    MedicationRequestDetectedIssue,
    MedicationRequestDetectedIssueReferenceType,
    MedicationRequestDosageAdditionalInstruction,
    MedicationRequestDosageAdditionalInstructionCoding,
    MedicationRequestDosageAsNeededCoding,
    MedicationRequestDosageInstruction,
    MedicationRequestDosageMethodCoding,
    MedicationRequestDosageRouteCoding,
    MedicationRequestDosageSiteCoding,
    MedicationRequestEventHistory,
    MedicationRequestEventHistoryReferenceType,
    MedicationRequestGroupIdentifierTypeCoding,
    MedicationRequestIdentifier,
    MedicationRequestIdentifierTypeCoding,
    MedicationRequestInsurance,
    MedicationRequestInsuranceReferenceType,
    MedicationRequestIntent as MedicationRequestIntentModel,
    MedicationRequestMedicationCoding,
    MedicationRequestMedicationReferenceType,
    MedicationRequestModel,
    MedicationRequestNote,
    MedicationRequestNoteAuthorReferenceType,
    MedicationRequestPerformerReferenceType,
    MedicationRequestPerformerTypeCoding,
    MedicationRequestPriority as MedicationRequestPriorityModel,
    MedicationRequestQuantityComparator as MedicationRequestQuantityComparatorModel,
    MedicationRequestReasonCode,
    MedicationRequestReasonCodeCoding,
    MedicationRequestReasonReference,
    MedicationRequestReasonReferenceType,
    MedicationRequestRecorderReferenceType,
    MedicationRequestReportedReferenceType,
    MedicationRequestRequesterReferenceType,
    MedicationRequestStatus as MedicationRequestStatusModel,
    MedicationRequestStatusReasonCoding,
    MedicationRequestSubstitutionAllowedCoding,
    MedicationRequestSubstitutionReasonCoding,
    MedicationRequestSupportingInformation,
)
from app.schemas.medication_request import MedicationRequestCreateSchema, MedicationRequestPatchSchema

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _MODELED_BASED_ON_TYPES,
    _MODELED_NOTE_AUTHOR_TYPES,
    _MODELED_PERFORMER_TYPES,
    _MODELED_REPORTED_REFERENCE_TYPES,
    _MODELED_REQUESTER_TYPES,
    _org_ref_kwargs,
    _parse_org_ref,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)

_SUB = {
    "identifier", "category", "reason_code", "reason_reference", "based_on", "insurance",
    "supporting_information", "note", "dosage_instruction", "detected_issue", "event_history",
}
_SINGLE_OBJECT_FIELDS = {
    "status_reason", "reported_reference", "medication_codeable_concept", "medication_reference",
    "subject", "encounter", "requester", "performer", "performer_type", "recorder",
    "group_identifier", "course_of_therapy_type", "substitution_allowed_codeable_concept",
    "substitution_reason", "prior_prescription", "dispense_request_performer",
}
_DISPENSE_REQUEST_FIELDS = {
    "dispense_request_initial_fill_quantity_value", "dispense_request_initial_fill_quantity_comparator",
    "dispense_request_initial_fill_quantity_unit", "dispense_request_initial_fill_quantity_system",
    "dispense_request_initial_fill_quantity_code", "dispense_request_initial_fill_duration_value",
    "dispense_request_initial_fill_duration_unit", "dispense_request_initial_fill_duration_system",
    "dispense_request_initial_fill_duration_code", "dispense_request_dispense_interval_value",
    "dispense_request_dispense_interval_unit", "dispense_request_dispense_interval_system",
    "dispense_request_dispense_interval_code", "dispense_request_validity_period_start",
    "dispense_request_validity_period_end", "dispense_request_number_of_repeats_allowed",
    "dispense_request_quantity_value", "dispense_request_quantity_unit", "dispense_request_quantity_system",
    "dispense_request_quantity_code", "dispense_request_expected_supply_duration_value",
    "dispense_request_expected_supply_duration_unit", "dispense_request_expected_supply_duration_system",
    "dispense_request_expected_supply_duration_code",
}
_SPECIAL = (
    {"status", "intent", "priority", "reported_boolean", "substitution_allowed_boolean"}
    | _SINGLE_OBJECT_FIELDS
    | _DISPENSE_REQUEST_FIELDS
)


def _model_status(v) -> MedicationRequestStatusModel:
    return MedicationRequestStatusModel[v.name]


def _model_intent(v) -> MedicationRequestIntentModel:
    return MedicationRequestIntentModel[v.name]


def _model_priority(v) -> MedicationRequestPriorityModel:
    return MedicationRequestPriorityModel[v.name]


def _model_comparator(v) -> MedicationRequestQuantityComparatorModel:
    return MedicationRequestQuantityComparatorModel[v.name]


def _identifier_kwargs_for(i, prefix: str = "") -> dict:
    """Full column set for one Identifier value — used for both
    MedicationRequest.identifier (prefix="", own child table) and
    MedicationRequest.groupIdentifier (prefix="group_identifier_",
    flattened onto the main row). `i` may be `None`."""
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


def _cc_text_kwargs(cc, prefix: str) -> dict:
    """Full `{prefix}text` column set for one plain 0..1 CodeableConcept
    field — `coding[]` is handled separately via its own direct-child
    table replace."""
    return {f"{prefix}text": cc.text if cc else None}


def _list_reference_kwargs(obj, enum_cls) -> dict:
    """Full column set for one row of a bare 0..* Reference list table —
    all share the bare `reference_*` column prefix."""
    kwargs = {
        "reference_reference": obj.reference,
        **_ref_kwargs("reference", obj.reference, obj.reference_display, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"reference_{suffix}"] = getattr(obj, f"reference_{suffix}")
    return kwargs


def _coding_kwargs(coding, created_by: str | None) -> dict:
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(self, payload: MedicationRequestCreateSchema) -> MedicationRequestModel:
        async with self.session_factory() as session:
            reported_reference_kwargs = _single_reference_kwargs(
                "reported_reference", payload.reported_reference, MedicationRequestReportedReferenceType
            )
            medication_reference_kwargs = _single_reference_kwargs(
                "medication_reference", payload.medication_reference, MedicationRequestMedicationReferenceType
            )
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, SubjectReferenceType)
            encounter_kwargs = _single_reference_kwargs("encounter", payload.encounter, EncounterReferenceType)
            requester_kwargs = _single_reference_kwargs("requester", payload.requester, MedicationRequestRequesterReferenceType)
            performer_kwargs = _single_reference_kwargs("performer", payload.performer, MedicationRequestPerformerReferenceType)
            recorder_kwargs = _single_reference_kwargs("recorder", payload.recorder, MedicationRequestRecorderReferenceType)
            dispense_request_performer_kwargs = _single_reference_kwargs(
                "dispense_request_performer", payload.dispense_request_performer, OrganizationReferenceType
            )
            prior_prescription_kwargs = _single_reference_kwargs(
                "prior_prescription", payload.prior_prescription, MedicationRequestReferenceType
            )

            await _validate_ref(session, payload.tenant_id, "reportedReference", reported_reference_kwargs["reported_reference_type"], reported_reference_kwargs["reported_reference_id"], _MODELED_REPORTED_REFERENCE_TYPES)
            await _validate_ref(session, payload.tenant_id, "medicationReference", medication_reference_kwargs["medication_reference_type"], medication_reference_kwargs["medication_reference_id"], set())
            await _validate_ref(session, payload.tenant_id, "subject", subject_kwargs["subject_type"], subject_kwargs["subject_id"], set())
            await _validate_ref(session, payload.tenant_id, "encounter", encounter_kwargs["encounter_type"], encounter_kwargs["encounter_id"], None)
            await _validate_ref(session, payload.tenant_id, "requester", requester_kwargs["requester_type"], requester_kwargs["requester_id"], _MODELED_REQUESTER_TYPES)
            await _validate_ref(session, payload.tenant_id, "performer", performer_kwargs["performer_type"], performer_kwargs["performer_id"], _MODELED_PERFORMER_TYPES)
            await _validate_ref(session, payload.tenant_id, "recorder", recorder_kwargs["recorder_type"], recorder_kwargs["recorder_id"], None)
            await _validate_ref(session, payload.tenant_id, "dispenseRequest.performer", dispense_request_performer_kwargs["dispense_request_performer_type"], dispense_request_performer_kwargs["dispense_request_performer_id"], None)
            await _validate_ref(session, payload.tenant_id, "priorPrescription", prior_prescription_kwargs["prior_prescription_type"], prior_prescription_kwargs["prior_prescription_id"], None)

            mr = MedicationRequestModel(
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                created_by=payload.created_by,
                extension=payload.extension or [],
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                status=_model_status(payload.status),
                **_cc_text_kwargs(payload.status_reason, "status_reason_"),
                intent=_model_intent(payload.intent),
                priority=_model_priority(payload.priority) if payload.priority else None,
                do_not_perform=payload.do_not_perform,
                reported_boolean=payload.reported_boolean,
                **reported_reference_kwargs,
                **_cc_text_kwargs(payload.medication_codeable_concept, "medication_codeable_concept_"),
                **medication_reference_kwargs,
                **subject_kwargs,
                **encounter_kwargs,
                authored_on=payload.authored_on,
                **requester_kwargs,
                **performer_kwargs,
                **_cc_text_kwargs(payload.performer_type, "performer_type_"),
                **recorder_kwargs,
                **_identifier_kwargs_for(payload.group_identifier, "group_identifier_"),
                **_cc_text_kwargs(payload.course_of_therapy_type, "course_of_therapy_type_"),
                dispense_request_initial_fill_quantity_value=payload.dispense_request_initial_fill_quantity_value,
                dispense_request_initial_fill_quantity_comparator=_model_comparator(payload.dispense_request_initial_fill_quantity_comparator) if payload.dispense_request_initial_fill_quantity_comparator else None,
                dispense_request_initial_fill_quantity_unit=payload.dispense_request_initial_fill_quantity_unit,
                dispense_request_initial_fill_quantity_system=payload.dispense_request_initial_fill_quantity_system,
                dispense_request_initial_fill_quantity_code=payload.dispense_request_initial_fill_quantity_code,
                dispense_request_initial_fill_duration_value=payload.dispense_request_initial_fill_duration_value,
                dispense_request_initial_fill_duration_unit=payload.dispense_request_initial_fill_duration_unit,
                dispense_request_initial_fill_duration_system=payload.dispense_request_initial_fill_duration_system,
                dispense_request_initial_fill_duration_code=payload.dispense_request_initial_fill_duration_code,
                dispense_request_dispense_interval_value=payload.dispense_request_dispense_interval_value,
                dispense_request_dispense_interval_unit=payload.dispense_request_dispense_interval_unit,
                dispense_request_dispense_interval_system=payload.dispense_request_dispense_interval_system,
                dispense_request_dispense_interval_code=payload.dispense_request_dispense_interval_code,
                dispense_request_validity_period_start=payload.dispense_request_validity_period_start,
                dispense_request_validity_period_end=payload.dispense_request_validity_period_end,
                dispense_request_number_of_repeats_allowed=payload.dispense_request_number_of_repeats_allowed,
                dispense_request_quantity_value=payload.dispense_request_quantity_value,
                dispense_request_quantity_unit=payload.dispense_request_quantity_unit,
                dispense_request_quantity_system=payload.dispense_request_quantity_system,
                dispense_request_quantity_code=payload.dispense_request_quantity_code,
                dispense_request_expected_supply_duration_value=payload.dispense_request_expected_supply_duration_value,
                dispense_request_expected_supply_duration_unit=payload.dispense_request_expected_supply_duration_unit,
                dispense_request_expected_supply_duration_system=payload.dispense_request_expected_supply_duration_system,
                dispense_request_expected_supply_duration_code=payload.dispense_request_expected_supply_duration_code,
                **dispense_request_performer_kwargs,
                substitution_allowed_boolean=payload.substitution_allowed_boolean,
                **_cc_text_kwargs(payload.substitution_allowed_codeable_concept, "substitution_allowed_codeable_concept_"),
                **_cc_text_kwargs(payload.substitution_reason, "substitution_reason_"),
                **prior_prescription_kwargs,
            )
            session.add(mr)
            await session.flush()

            for coding in (payload.status_reason.coding if payload.status_reason else None) or []:
                session.add(MedicationRequestStatusReasonCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.medication_codeable_concept.coding if payload.medication_codeable_concept else None) or []:
                session.add(MedicationRequestMedicationCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.performer_type.coding if payload.performer_type else None) or []:
                session.add(MedicationRequestPerformerTypeCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.group_identifier.type_coding if payload.group_identifier else None) or []:
                session.add(MedicationRequestGroupIdentifierTypeCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.course_of_therapy_type.coding if payload.course_of_therapy_type else None) or []:
                session.add(MedicationRequestCourseOfTherapyTypeCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.substitution_allowed_codeable_concept.coding if payload.substitution_allowed_codeable_concept else None) or []:
                session.add(MedicationRequestSubstitutionAllowedCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))
            for coding in (payload.substitution_reason.coding if payload.substitution_reason else None) or []:
                session.add(MedicationRequestSubstitutionReasonCoding(medication_request_pk=mr.id, tenant_id=payload.tenant_id, **_coding_kwargs(coding, payload.created_by)))

            await self._insert_sub_resources(session, mr.id, payload, payload.tenant_id, payload.created_by)

            try:
                await session.commit()
                await session.refresh(mr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_medication_request_id(mr.medication_request_id)

    async def _insert_sub_resources(self, session, mr_pk: int, payload, tenant_id: str, created_by: str | None) -> None:
        for i in payload.identifier or []:
            a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
            identifier = MedicationRequestIdentifier(
                medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by,
                use=i.use, type_text=i.type_text, system=i.system, value=i.value,
                period_start=i.period_start, period_end=i.period_end,
                assigner_reference=i.assigner, assigner_type=a_type, assigner_id=a_id, assigner_display=i.assigner_display,
                **{f"assigner_{s}": getattr(i, f"assigner_{s}") for s in _IDENTIFIER_FALLBACK_SUFFIXES},
            )
            session.add(identifier)
            if i.type_coding:
                await session.flush()
                for coding in i.type_coding:
                    session.add(MedicationRequestIdentifierTypeCoding(medication_request_identifier_id=identifier.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for c in payload.category or []:
            category = MedicationRequestCategory(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, text=c.text)
            session.add(category)
            if c.coding:
                await session.flush()
                for coding in c.coding:
                    session.add(MedicationRequestCategoryCoding(medication_request_category_id=category.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for rc in payload.reason_code or []:
            rcrow = MedicationRequestReasonCode(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, text=rc.text)
            session.add(rcrow)
            if rc.coding:
                await session.flush()
                for coding in rc.coding:
                    session.add(MedicationRequestReasonCodeCoding(medication_request_reason_code_id=rcrow.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for rr in payload.reason_reference or []:
            session.add(MedicationRequestReasonReference(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(rr, MedicationRequestReasonReferenceType)))

        for b in payload.based_on or []:
            kwargs = _list_reference_kwargs(b, MedicationRequestBasedOnReferenceType)
            await _validate_ref(session, tenant_id, "basedOn", kwargs["reference_type"], kwargs["reference_id"], _MODELED_BASED_ON_TYPES)
            session.add(MedicationRequestBasedOn(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for ins in payload.insurance or []:
            session.add(MedicationRequestInsurance(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(ins, MedicationRequestInsuranceReferenceType)))

        for si in payload.supporting_information or []:
            session.add(MedicationRequestSupportingInformation(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(si, None)))

        for n in payload.note or []:
            author_kwargs = _ref_kwargs("author", n.author_reference, n.author_reference_display, MedicationRequestNoteAuthorReferenceType)
            if n.author_reference:
                await _validate_ref(session, tenant_id, "note.author", author_kwargs["author_type"], author_kwargs["author_id"], _MODELED_NOTE_AUTHOR_TYPES)
            session.add(MedicationRequestNote(
                medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by,
                author_string=n.author_string, author_reference=n.author_reference, **author_kwargs,
                time=n.time, text=n.text,
            ))

        for d in payload.dosage_instruction or []:
            dosage = MedicationRequestDosageInstruction(
                medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by,
                sequence=d.sequence, text=d.text, patient_instruction=d.patient_instruction, timing=d.timing,
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
                ai_row = MedicationRequestDosageAdditionalInstruction(
                    medication_request_dosage_instruction_id=dosage.id, tenant_id=tenant_id, created_by=created_by, text=ai.text
                )
                session.add(ai_row)
                if ai.coding:
                    await session.flush()
                    for coding in ai.coding:
                        session.add(MedicationRequestDosageAdditionalInstructionCoding(
                            medication_request_dosage_additional_instruction_id=ai_row.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)
                        ))

            for coding in (d.site.coding if d.site else None) or []:
                session.add(MedicationRequestDosageSiteCoding(medication_request_dosage_instruction_id=dosage.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
            for coding in (d.route.coding if d.route else None) or []:
                session.add(MedicationRequestDosageRouteCoding(medication_request_dosage_instruction_id=dosage.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
            for coding in (d.method.coding if d.method else None) or []:
                session.add(MedicationRequestDosageMethodCoding(medication_request_dosage_instruction_id=dosage.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
            for coding in (d.as_needed_codeable_concept.coding if d.as_needed_codeable_concept else None) or []:
                session.add(MedicationRequestDosageAsNeededCoding(medication_request_dosage_instruction_id=dosage.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for di in payload.detected_issue or []:
            session.add(MedicationRequestDetectedIssue(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(di, MedicationRequestDetectedIssueReferenceType)))

        for eh in payload.event_history or []:
            session.add(MedicationRequestEventHistory(medication_request_pk=mr_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(eh, MedicationRequestEventHistoryReferenceType)))

    async def patch_full(self, medication_request_id: int, payload: MedicationRequestPatchSchema) -> MedicationRequestModel | None:
        async with self.session_factory() as session:
            stmt = select(MedicationRequestModel).where(MedicationRequestModel.medication_request_id == medication_request_id)
            mr = (await session.execute(stmt)).scalars().first()
            if not mr:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set
            sub_created_by = payload.updated_by if payload.updated_by is not None else mr.created_by

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(mr, field, value)

            if "status" in provided and payload.status is not None:
                mr.status = _model_status(payload.status)
            if "intent" in provided and payload.intent is not None:
                mr.intent = _model_intent(payload.intent)
            if "priority" in provided:
                mr.priority = _model_priority(payload.priority) if payload.priority else None
            if "reported_boolean" in provided:
                mr.reported_boolean = payload.reported_boolean
            if "substitution_allowed_boolean" in provided:
                mr.substitution_allowed_boolean = payload.substitution_allowed_boolean

            if provided & _DISPENSE_REQUEST_FIELDS:
                for field in _DISPENSE_REQUEST_FIELDS:
                    if field in provided:
                        value = getattr(payload, field)
                        if field.endswith("_comparator") and value is not None:
                            value = _model_comparator(value)
                        setattr(mr, field, value)

            # 0..1 CodeableConcept fields (text + direct-child coding replace)
            for field, text_prefix, coding_model, coding_fk in (
                ("status_reason", "status_reason_", MedicationRequestStatusReasonCoding, MedicationRequestStatusReasonCoding.medication_request_pk),
                ("medication_codeable_concept", "medication_codeable_concept_", MedicationRequestMedicationCoding, MedicationRequestMedicationCoding.medication_request_pk),
                ("performer_type", "performer_type_", MedicationRequestPerformerTypeCoding, MedicationRequestPerformerTypeCoding.medication_request_pk),
                ("course_of_therapy_type", "course_of_therapy_type_", MedicationRequestCourseOfTherapyTypeCoding, MedicationRequestCourseOfTherapyTypeCoding.medication_request_pk),
                ("substitution_allowed_codeable_concept", "substitution_allowed_codeable_concept_", MedicationRequestSubstitutionAllowedCoding, MedicationRequestSubstitutionAllowedCoding.medication_request_pk),
                ("substitution_reason", "substitution_reason_", MedicationRequestSubstitutionReasonCoding, MedicationRequestSubstitutionReasonCoding.medication_request_pk),
            ):
                if field in provided:
                    cc = getattr(payload, field)
                    for col, value in _cc_text_kwargs(cc, text_prefix).items():
                        setattr(mr, col, value)
                    await session.execute(delete(coding_model).where(coding_fk == mr.id))
                    for coding in (cc.coding if cc else None) or []:
                        session.add(coding_model(medication_request_pk=mr.id, tenant_id=mr.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            if "group_identifier" in provided:
                for col, value in _identifier_kwargs_for(payload.group_identifier, "group_identifier_").items():
                    setattr(mr, col, value)
                await session.execute(delete(MedicationRequestGroupIdentifierTypeCoding).where(MedicationRequestGroupIdentifierTypeCoding.medication_request_pk == mr.id))
                for coding in (payload.group_identifier.type_coding if payload.group_identifier else None) or []:
                    session.add(MedicationRequestGroupIdentifierTypeCoding(medication_request_pk=mr.id, tenant_id=mr.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            for prefix, enum_cls, modeled in (
                ("reported_reference", MedicationRequestReportedReferenceType, _MODELED_REPORTED_REFERENCE_TYPES),
                ("medication_reference", MedicationRequestMedicationReferenceType, set()),
                ("subject", SubjectReferenceType, set()),
                ("encounter", EncounterReferenceType, None),
                ("requester", MedicationRequestRequesterReferenceType, _MODELED_REQUESTER_TYPES),
                ("performer", MedicationRequestPerformerReferenceType, _MODELED_PERFORMER_TYPES),
                ("recorder", MedicationRequestRecorderReferenceType, None),
                ("dispense_request_performer", OrganizationReferenceType, None),
                ("prior_prescription", MedicationRequestReferenceType, None),
            ):
                if prefix in provided:
                    kwargs = _single_reference_kwargs(prefix, getattr(payload, prefix), enum_cls)
                    await _validate_ref(session, mr.tenant_id, prefix, kwargs[f"{prefix}_type"], kwargs[f"{prefix}_id"], modeled)
                    for col, value in kwargs.items():
                        setattr(mr, col, value)

            # Sub-resource list replace — delete grandchildren before parents.
            if payload.identifier is not None:
                await session.execute(delete(MedicationRequestIdentifierTypeCoding).where(
                    MedicationRequestIdentifierTypeCoding.medication_request_identifier_id.in_(
                        select(MedicationRequestIdentifier.id).where(MedicationRequestIdentifier.medication_request_pk == mr.id)
                    )
                ))
                await session.execute(delete(MedicationRequestIdentifier).where(MedicationRequestIdentifier.medication_request_pk == mr.id))
            if payload.category is not None:
                await session.execute(delete(MedicationRequestCategoryCoding).where(
                    MedicationRequestCategoryCoding.medication_request_category_id.in_(
                        select(MedicationRequestCategory.id).where(MedicationRequestCategory.medication_request_pk == mr.id)
                    )
                ))
                await session.execute(delete(MedicationRequestCategory).where(MedicationRequestCategory.medication_request_pk == mr.id))
            if payload.reason_code is not None:
                await session.execute(delete(MedicationRequestReasonCodeCoding).where(
                    MedicationRequestReasonCodeCoding.medication_request_reason_code_id.in_(
                        select(MedicationRequestReasonCode.id).where(MedicationRequestReasonCode.medication_request_pk == mr.id)
                    )
                ))
                await session.execute(delete(MedicationRequestReasonCode).where(MedicationRequestReasonCode.medication_request_pk == mr.id))
            if payload.reason_reference is not None:
                await session.execute(delete(MedicationRequestReasonReference).where(MedicationRequestReasonReference.medication_request_pk == mr.id))
            if payload.based_on is not None:
                await session.execute(delete(MedicationRequestBasedOn).where(MedicationRequestBasedOn.medication_request_pk == mr.id))
            if payload.insurance is not None:
                await session.execute(delete(MedicationRequestInsurance).where(MedicationRequestInsurance.medication_request_pk == mr.id))
            if payload.supporting_information is not None:
                await session.execute(delete(MedicationRequestSupportingInformation).where(MedicationRequestSupportingInformation.medication_request_pk == mr.id))
            if payload.note is not None:
                await session.execute(delete(MedicationRequestNote).where(MedicationRequestNote.medication_request_pk == mr.id))
            if payload.dosage_instruction is not None:
                dosage_ids_subq = select(MedicationRequestDosageInstruction.id).where(MedicationRequestDosageInstruction.medication_request_pk == mr.id)
                ai_ids_subq = select(MedicationRequestDosageAdditionalInstruction.id).where(MedicationRequestDosageAdditionalInstruction.medication_request_dosage_instruction_id.in_(dosage_ids_subq))
                await session.execute(delete(MedicationRequestDosageAdditionalInstructionCoding).where(MedicationRequestDosageAdditionalInstructionCoding.medication_request_dosage_additional_instruction_id.in_(ai_ids_subq)))
                await session.execute(delete(MedicationRequestDosageAdditionalInstruction).where(MedicationRequestDosageAdditionalInstruction.medication_request_dosage_instruction_id.in_(dosage_ids_subq)))
                await session.execute(delete(MedicationRequestDosageSiteCoding).where(MedicationRequestDosageSiteCoding.medication_request_dosage_instruction_id.in_(dosage_ids_subq)))
                await session.execute(delete(MedicationRequestDosageRouteCoding).where(MedicationRequestDosageRouteCoding.medication_request_dosage_instruction_id.in_(dosage_ids_subq)))
                await session.execute(delete(MedicationRequestDosageMethodCoding).where(MedicationRequestDosageMethodCoding.medication_request_dosage_instruction_id.in_(dosage_ids_subq)))
                await session.execute(delete(MedicationRequestDosageAsNeededCoding).where(MedicationRequestDosageAsNeededCoding.medication_request_dosage_instruction_id.in_(dosage_ids_subq)))
                await session.execute(delete(MedicationRequestDosageInstruction).where(MedicationRequestDosageInstruction.medication_request_pk == mr.id))
            if payload.detected_issue is not None:
                await session.execute(delete(MedicationRequestDetectedIssue).where(MedicationRequestDetectedIssue.medication_request_pk == mr.id))
            if payload.event_history is not None:
                await session.execute(delete(MedicationRequestEventHistory).where(MedicationRequestEventHistory.medication_request_pk == mr.id))

            await self._insert_sub_resources(session, mr.id, payload, mr.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted((_SUB | _SINGLE_OBJECT_FIELDS) & set(data.keys()))
            if replaced:
                logger.debug(
                    "MedicationRequest sub-resource lists replaced",
                    extra={"event": "medication_request.sublists_replaced", "medication_request_id": medication_request_id, "replaced": replaced},
                )

        return await self.get_by_medication_request_id(medication_request_id)

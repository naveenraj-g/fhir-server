from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import EncounterReferenceType, LocationReferenceType, ServiceRequestReferenceType
from app.models.service_request import (
    ServiceRequestAsNeededCoding,
    ServiceRequestBasedOn,
    ServiceRequestBasedOnReferenceType,
    ServiceRequestBodySite,
    ServiceRequestBodySiteCoding,
    ServiceRequestCategory,
    ServiceRequestCategoryCoding,
    ServiceRequestCodeCoding,
    ServiceRequestIdentifier,
    ServiceRequestIdentifierTypeCoding,
    ServiceRequestInsurance,
    ServiceRequestInsuranceReferenceType,
    ServiceRequestIntent as ServiceRequestIntentModel,
    ServiceRequestLocationCode,
    ServiceRequestLocationCodeCoding,
    ServiceRequestLocationReference,
    ServiceRequestModel,
    ServiceRequestNote,
    ServiceRequestNoteAuthorReferenceType,
    ServiceRequestOrderDetail,
    ServiceRequestOrderDetailCoding,
    ServiceRequestPerformer,
    ServiceRequestPerformerReferenceType,
    ServiceRequestPerformerTypeCoding,
    ServiceRequestPriority as ServiceRequestPriorityModel,
    ServiceRequestQuantityComparator as ServiceRequestQuantityComparatorModel,
    ServiceRequestReasonCode,
    ServiceRequestReasonCodeCoding,
    ServiceRequestReasonReference,
    ServiceRequestReasonReferenceType,
    ServiceRequestRelevantHistory,
    ServiceRequestRelevantHistoryReferenceType,
    ServiceRequestReplaces,
    ServiceRequestRequesterReferenceType,
    ServiceRequestRequisitionTypeCoding,
    ServiceRequestSpecimen,
    ServiceRequestSpecimenReferenceType,
    ServiceRequestStatus as ServiceRequestStatusModel,
    ServiceRequestSubjectReferenceType,
    ServiceRequestSupportingInfo,
)
from app.schemas.service_request import ServiceRequestCreateSchema, ServiceRequestPatchSchema

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _MODELED_BASED_ON_TYPES,
    _MODELED_NOTE_AUTHOR_TYPES,
    _MODELED_PERFORMER_TYPES,
    _MODELED_REQUESTER_TYPES,
    _MODELED_SUBJECT_TYPES,
    _org_ref_kwargs,
    _parse_org_ref,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)

_SUB = {
    "identifier", "based_on", "replaces", "category", "order_detail", "performer",
    "location_code", "location_reference", "reason_code", "reason_reference",
    "insurance", "supporting_info", "specimen", "body_site", "note", "relevant_history",
}
_SINGLE_OBJECT_FIELDS = {"requisition", "code", "as_needed_codeable_concept", "subject", "encounter", "requester", "performer_type"}
_QUANTITY_FIELDS = {
    "quantity_quantity_value", "quantity_quantity_comparator", "quantity_quantity_unit",
    "quantity_quantity_system", "quantity_quantity_code",
    "quantity_ratio_numerator_value", "quantity_ratio_numerator_comparator", "quantity_ratio_numerator_unit",
    "quantity_ratio_numerator_system", "quantity_ratio_numerator_code",
    "quantity_ratio_denominator_value", "quantity_ratio_denominator_comparator", "quantity_ratio_denominator_unit",
    "quantity_ratio_denominator_system", "quantity_ratio_denominator_code",
    "quantity_range_low_value", "quantity_range_low_unit", "quantity_range_low_system", "quantity_range_low_code",
    "quantity_range_high_value", "quantity_range_high_unit", "quantity_range_high_system", "quantity_range_high_code",
}
_OCCURRENCE_FIELDS = {"occurrence_date_time", "occurrence_period_start", "occurrence_period_end", "occurrence_timing"}
_AS_NEEDED_FIELDS = {"as_needed_boolean", "as_needed_codeable_concept"}
_SPECIAL = {"status", "intent", "priority"} | _SINGLE_OBJECT_FIELDS | _QUANTITY_FIELDS | _OCCURRENCE_FIELDS | _AS_NEEDED_FIELDS


def _model_status(v) -> ServiceRequestStatusModel:
    return ServiceRequestStatusModel[v.name]


def _model_intent(v) -> ServiceRequestIntentModel:
    return ServiceRequestIntentModel[v.name]


def _model_priority(v) -> ServiceRequestPriorityModel:
    return ServiceRequestPriorityModel[v.name]


def _model_comparator(v) -> ServiceRequestQuantityComparatorModel:
    return ServiceRequestQuantityComparatorModel[v.name]


def _identifier_kwargs_for(i, prefix: str = "") -> dict:
    """Full column set for one Identifier value — used for both
    ServiceRequest.identifier (prefix="", own child table) and
    ServiceRequest.requisition (prefix="requisition_", flattened onto the
    main row). `i` may be `None` (requisition absent/cleared)."""
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


def _codeable_concept_kwargs(cc, prefix: str) -> dict:
    """Full `{prefix}text` column set for one plain 0..1 CodeableConcept
    field (code/performerType/asNeededCodeableConcept) — coding[] is
    handled separately via its own child-table replace."""
    return {f"{prefix}text": cc.text if cc else None}


def _list_reference_kwargs(obj, enum_cls) -> dict:
    """Full column set for one row of a bare 0..* Reference list table
    (basedOn/replaces/locationReference/reasonReference/insurance/
    supportingInfo/specimen/relevantHistory/performer) — all share the
    bare `reference_*` column prefix."""
    kwargs = {
        "reference_reference": obj.reference,
        **_ref_kwargs("reference", obj.reference, obj.reference_display, enum_cls),
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        kwargs[f"reference_{suffix}"] = getattr(obj, f"reference_{suffix}")
    return kwargs


async def _replace_identifier_type_coding(session, sr_pk, identifier_row_id, coding_list, tenant_id, created_by):
    for coding in coding_list or []:
        session.add(
            ServiceRequestIdentifierTypeCoding(
                service_request_identifier_id=identifier_row_id,
                tenant_id=tenant_id,
                created_by=created_by,
                system=coding.system,
                version=coding.version,
                code=coding.code,
                display=coding.display,
                user_selected=coding.user_selected,
            )
        )


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(
        self,
        payload: ServiceRequestCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> ServiceRequestModel:
        async with self.session_factory() as session:
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, ServiceRequestSubjectReferenceType)
            encounter_kwargs = _single_reference_kwargs("encounter", payload.encounter, EncounterReferenceType)
            requester_kwargs = _single_reference_kwargs("requester", payload.requester, ServiceRequestRequesterReferenceType)

            await _validate_ref(session, org_id, "subject", subject_kwargs["subject_type"], subject_kwargs["subject_id"], _MODELED_SUBJECT_TYPES)
            await _validate_ref(session, org_id, "encounter", encounter_kwargs["encounter_type"], encounter_kwargs["encounter_id"], None)
            await _validate_ref(session, org_id, "requester", requester_kwargs["requester_type"], requester_kwargs["requester_id"], _MODELED_REQUESTER_TYPES)

            sr = ServiceRequestModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                **_identifier_kwargs_for(payload.requisition, "requisition_"),
                status=_model_status(payload.status),
                intent=_model_intent(payload.intent),
                priority=_model_priority(payload.priority) if payload.priority else None,
                do_not_perform=payload.do_not_perform,
                **_codeable_concept_kwargs(payload.code, "code_"),
                quantity_quantity_value=payload.quantity_quantity_value,
                quantity_quantity_comparator=_model_comparator(payload.quantity_quantity_comparator) if payload.quantity_quantity_comparator else None,
                quantity_quantity_unit=payload.quantity_quantity_unit,
                quantity_quantity_system=payload.quantity_quantity_system,
                quantity_quantity_code=payload.quantity_quantity_code,
                quantity_ratio_numerator_value=payload.quantity_ratio_numerator_value,
                quantity_ratio_numerator_comparator=_model_comparator(payload.quantity_ratio_numerator_comparator) if payload.quantity_ratio_numerator_comparator else None,
                quantity_ratio_numerator_unit=payload.quantity_ratio_numerator_unit,
                quantity_ratio_numerator_system=payload.quantity_ratio_numerator_system,
                quantity_ratio_numerator_code=payload.quantity_ratio_numerator_code,
                quantity_ratio_denominator_value=payload.quantity_ratio_denominator_value,
                quantity_ratio_denominator_comparator=_model_comparator(payload.quantity_ratio_denominator_comparator) if payload.quantity_ratio_denominator_comparator else None,
                quantity_ratio_denominator_unit=payload.quantity_ratio_denominator_unit,
                quantity_ratio_denominator_system=payload.quantity_ratio_denominator_system,
                quantity_ratio_denominator_code=payload.quantity_ratio_denominator_code,
                quantity_range_low_value=payload.quantity_range_low_value,
                quantity_range_low_unit=payload.quantity_range_low_unit,
                quantity_range_low_system=payload.quantity_range_low_system,
                quantity_range_low_code=payload.quantity_range_low_code,
                quantity_range_high_value=payload.quantity_range_high_value,
                quantity_range_high_unit=payload.quantity_range_high_unit,
                quantity_range_high_system=payload.quantity_range_high_system,
                quantity_range_high_code=payload.quantity_range_high_code,
                **subject_kwargs,
                **encounter_kwargs,
                occurrence_date_time=payload.occurrence_date_time,
                occurrence_period_start=payload.occurrence_period_start,
                occurrence_period_end=payload.occurrence_period_end,
                occurrence_timing=payload.occurrence_timing,
                as_needed_boolean=payload.as_needed_boolean,
                as_needed_codeable_concept_text=payload.as_needed_codeable_concept.text if payload.as_needed_codeable_concept else None,
                authored_on=payload.authored_on,
                **requester_kwargs,
                performer_type_text=payload.performer_type.text if payload.performer_type else None,
                patient_instruction=payload.patient_instruction,
            )
            session.add(sr)
            await session.flush()

            # Direct-child coding tables for the main row's own 0..1 CCs.
            for coding in (payload.requisition.type_coding if payload.requisition else None) or []:
                session.add(ServiceRequestRequisitionTypeCoding(
                    service_request_pk=sr.id, tenant_id=org_id, created_by=created_by,
                    system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                ))
            for coding in (payload.code.coding if payload.code else None) or []:
                session.add(ServiceRequestCodeCoding(
                    service_request_pk=sr.id, tenant_id=org_id, created_by=created_by,
                    system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                ))
            for coding in (payload.as_needed_codeable_concept.coding if payload.as_needed_codeable_concept else None) or []:
                session.add(ServiceRequestAsNeededCoding(
                    service_request_pk=sr.id, tenant_id=org_id, created_by=created_by,
                    system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                ))
            for coding in (payload.performer_type.coding if payload.performer_type else None) or []:
                session.add(ServiceRequestPerformerTypeCoding(
                    service_request_pk=sr.id, tenant_id=org_id, created_by=created_by,
                    system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                ))

            await self._insert_sub_resources(session, sr.id, payload, org_id, created_by)

            try:
                await session.commit()
                await session.refresh(sr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_service_request_id(sr.service_request_id)

    async def _insert_sub_resources(self, session, sr_pk: int, payload, tenant_id: str, created_by: str | None) -> None:
        """Shared by create_full (full payload) and patch_full (each list
        called only when supplied) — inserts every 0..* sub-resource list
        for a payload object exposing the same field names as
        ServiceRequestCreateSchema/PatchSchema."""
        for i in payload.identifier or []:
            a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
            identifier = ServiceRequestIdentifier(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                use=i.use, type_text=i.type_text, system=i.system, value=i.value,
                period_start=i.period_start, period_end=i.period_end,
                assigner_reference=i.assigner, assigner_type=a_type, assigner_id=a_id, assigner_display=i.assigner_display,
                **{f"assigner_{s}": getattr(i, f"assigner_{s}") for s in _IDENTIFIER_FALLBACK_SUFFIXES},
            )
            session.add(identifier)
            if i.type_coding:
                await session.flush()
                await _replace_identifier_type_coding(session, sr_pk, identifier.id, i.type_coding, tenant_id, created_by)

        for b in payload.based_on or []:
            session.add(ServiceRequestBasedOn(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(b, ServiceRequestBasedOnReferenceType),
            ))

        for r in payload.replaces or []:
            session.add(ServiceRequestReplaces(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(r, ServiceRequestReferenceType),
            ))

        for c in payload.category or []:
            category = ServiceRequestCategory(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, text=c.text)
            session.add(category)
            if c.coding:
                await session.flush()
                for coding in c.coding:
                    session.add(ServiceRequestCategoryCoding(
                        service_request_category_id=category.id, tenant_id=tenant_id, created_by=created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

        for o in payload.order_detail or []:
            od = ServiceRequestOrderDetail(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, text=o.text)
            session.add(od)
            if o.coding:
                await session.flush()
                for coding in o.coding:
                    session.add(ServiceRequestOrderDetailCoding(
                        service_request_order_detail_id=od.id, tenant_id=tenant_id, created_by=created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

        for p in payload.performer or []:
            kwargs = _list_reference_kwargs(p, ServiceRequestPerformerReferenceType)
            await _validate_ref(session, tenant_id, "performer", kwargs["reference_type"], kwargs["reference_id"], _MODELED_PERFORMER_TYPES)
            session.add(ServiceRequestPerformer(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for lc in payload.location_code or []:
            loc = ServiceRequestLocationCode(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, text=lc.text)
            session.add(loc)
            if lc.coding:
                await session.flush()
                for coding in lc.coding:
                    session.add(ServiceRequestLocationCodeCoding(
                        service_request_location_code_id=loc.id, tenant_id=tenant_id, created_by=created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

        for lr in payload.location_reference or []:
            kwargs = _list_reference_kwargs(lr, LocationReferenceType)
            await _validate_ref(session, tenant_id, "locationReference", kwargs["reference_type"], kwargs["reference_id"], None)
            session.add(ServiceRequestLocationReference(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for rc in payload.reason_code or []:
            rcrow = ServiceRequestReasonCode(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, text=rc.text)
            session.add(rcrow)
            if rc.coding:
                await session.flush()
                for coding in rc.coding:
                    session.add(ServiceRequestReasonCodeCoding(
                        service_request_reason_code_id=rcrow.id, tenant_id=tenant_id, created_by=created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

        for rr in payload.reason_reference or []:
            session.add(ServiceRequestReasonReference(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(rr, ServiceRequestReasonReferenceType),
            ))

        for ins in payload.insurance or []:
            session.add(ServiceRequestInsurance(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(ins, ServiceRequestInsuranceReferenceType),
            ))

        for si in payload.supporting_info or []:
            session.add(ServiceRequestSupportingInfo(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(si, None),
            ))

        for sp in payload.specimen or []:
            session.add(ServiceRequestSpecimen(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(sp, ServiceRequestSpecimenReferenceType),
            ))

        for bs in payload.body_site or []:
            bsrow = ServiceRequestBodySite(service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by, text=bs.text)
            session.add(bsrow)
            if bs.coding:
                await session.flush()
                for coding in bs.coding:
                    session.add(ServiceRequestBodySiteCoding(
                        service_request_body_site_id=bsrow.id, tenant_id=tenant_id, created_by=created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

        for n in payload.note or []:
            author_kwargs = _ref_kwargs("author", n.author_reference, n.author_reference_display, ServiceRequestNoteAuthorReferenceType) if n.author_reference else {"author_type": None, "author_id": None, "author_display": n.author_reference_display}
            if n.author_reference:
                await _validate_ref(session, tenant_id, "note.author", author_kwargs["author_type"], author_kwargs["author_id"], _MODELED_NOTE_AUTHOR_TYPES)
            session.add(ServiceRequestNote(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                author_string=n.author_string, author_reference=n.author_reference, **author_kwargs,
                time=n.time, text=n.text,
            ))

        for rh in payload.relevant_history or []:
            session.add(ServiceRequestRelevantHistory(
                service_request_pk=sr_pk, tenant_id=tenant_id, created_by=created_by,
                **_list_reference_kwargs(rh, ServiceRequestRelevantHistoryReferenceType),
            ))

    async def patch_full(
        self,
        service_request_id: int,
        payload: ServiceRequestPatchSchema,
        updated_by: str | None = None,
    ) -> ServiceRequestModel | None:
        async with self.session_factory() as session:
            stmt = select(ServiceRequestModel).where(ServiceRequestModel.service_request_id == service_request_id)
            sr = (await session.execute(stmt)).scalars().first()
            if not sr:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(sr, field, value)

            if updated_by is not None:
                sr.updated_by = updated_by
            sub_created_by = updated_by if updated_by is not None else sr.created_by

            if "status" in provided and payload.status is not None:
                sr.status = _model_status(payload.status)
            if "intent" in provided and payload.intent is not None:
                sr.intent = _model_intent(payload.intent)
            if "priority" in provided:
                sr.priority = _model_priority(payload.priority) if payload.priority else None

            if "requisition" in provided:
                for col, value in _identifier_kwargs_for(payload.requisition, "requisition_").items():
                    setattr(sr, col, value)
                await session.execute(delete(ServiceRequestRequisitionTypeCoding).where(ServiceRequestRequisitionTypeCoding.service_request_pk == sr.id))
                for coding in (payload.requisition.type_coding if payload.requisition else None) or []:
                    session.add(ServiceRequestRequisitionTypeCoding(
                        service_request_pk=sr.id, tenant_id=sr.tenant_id, created_by=sub_created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

            if "code" in provided:
                for col, value in _codeable_concept_kwargs(payload.code, "code_").items():
                    setattr(sr, col, value)
                await session.execute(delete(ServiceRequestCodeCoding).where(ServiceRequestCodeCoding.service_request_pk == sr.id))
                for coding in (payload.code.coding if payload.code else None) or []:
                    session.add(ServiceRequestCodeCoding(
                        service_request_pk=sr.id, tenant_id=sr.tenant_id, created_by=sub_created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

            if provided & _QUANTITY_FIELDS:
                for field in _QUANTITY_FIELDS:
                    if field in provided:
                        value = getattr(payload, field)
                        if field.endswith("_comparator") and value is not None:
                            value = _model_comparator(value)
                        setattr(sr, field, value)

            for prefix, enum_cls, modeled in (
                ("subject", ServiceRequestSubjectReferenceType, _MODELED_SUBJECT_TYPES),
                ("encounter", EncounterReferenceType, None),
                ("requester", ServiceRequestRequesterReferenceType, _MODELED_REQUESTER_TYPES),
            ):
                if prefix in provided:
                    kwargs = _single_reference_kwargs(prefix, getattr(payload, prefix), enum_cls)
                    await _validate_ref(session, sr.tenant_id, prefix, kwargs[f"{prefix}_type"], kwargs[f"{prefix}_id"], modeled)
                    for col, value in kwargs.items():
                        setattr(sr, col, value)

            if provided & _OCCURRENCE_FIELDS:
                for field in _OCCURRENCE_FIELDS:
                    if field in provided:
                        setattr(sr, field, getattr(payload, field))

            if provided & _AS_NEEDED_FIELDS:
                if "as_needed_boolean" in provided:
                    sr.as_needed_boolean = payload.as_needed_boolean
                if "as_needed_codeable_concept" in provided:
                    sr.as_needed_codeable_concept_text = payload.as_needed_codeable_concept.text if payload.as_needed_codeable_concept else None
                    await session.execute(delete(ServiceRequestAsNeededCoding).where(ServiceRequestAsNeededCoding.service_request_pk == sr.id))
                    for coding in (payload.as_needed_codeable_concept.coding if payload.as_needed_codeable_concept else None) or []:
                        session.add(ServiceRequestAsNeededCoding(
                            service_request_pk=sr.id, tenant_id=sr.tenant_id, created_by=sub_created_by,
                            system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                        ))

            if "performer_type" in provided:
                sr.performer_type_text = payload.performer_type.text if payload.performer_type else None
                await session.execute(delete(ServiceRequestPerformerTypeCoding).where(ServiceRequestPerformerTypeCoding.service_request_pk == sr.id))
                for coding in (payload.performer_type.coding if payload.performer_type else None) or []:
                    session.add(ServiceRequestPerformerTypeCoding(
                        service_request_pk=sr.id, tenant_id=sr.tenant_id, created_by=sub_created_by,
                        system=coding.system, version=coding.version, code=coding.code, display=coding.display, user_selected=coding.user_selected,
                    ))

            # Sub-resource list replace — delete grandchildren before parents.
            if payload.identifier is not None:
                await session.execute(delete(ServiceRequestIdentifierTypeCoding).where(
                    ServiceRequestIdentifierTypeCoding.service_request_identifier_id.in_(
                        select(ServiceRequestIdentifier.id).where(ServiceRequestIdentifier.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestIdentifier).where(ServiceRequestIdentifier.service_request_pk == sr.id))
            if payload.category is not None:
                await session.execute(delete(ServiceRequestCategoryCoding).where(
                    ServiceRequestCategoryCoding.service_request_category_id.in_(
                        select(ServiceRequestCategory.id).where(ServiceRequestCategory.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestCategory).where(ServiceRequestCategory.service_request_pk == sr.id))
            if payload.order_detail is not None:
                await session.execute(delete(ServiceRequestOrderDetailCoding).where(
                    ServiceRequestOrderDetailCoding.service_request_order_detail_id.in_(
                        select(ServiceRequestOrderDetail.id).where(ServiceRequestOrderDetail.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestOrderDetail).where(ServiceRequestOrderDetail.service_request_pk == sr.id))
            if payload.location_code is not None:
                await session.execute(delete(ServiceRequestLocationCodeCoding).where(
                    ServiceRequestLocationCodeCoding.service_request_location_code_id.in_(
                        select(ServiceRequestLocationCode.id).where(ServiceRequestLocationCode.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestLocationCode).where(ServiceRequestLocationCode.service_request_pk == sr.id))
            if payload.reason_code is not None:
                await session.execute(delete(ServiceRequestReasonCodeCoding).where(
                    ServiceRequestReasonCodeCoding.service_request_reason_code_id.in_(
                        select(ServiceRequestReasonCode.id).where(ServiceRequestReasonCode.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestReasonCode).where(ServiceRequestReasonCode.service_request_pk == sr.id))
            if payload.body_site is not None:
                await session.execute(delete(ServiceRequestBodySiteCoding).where(
                    ServiceRequestBodySiteCoding.service_request_body_site_id.in_(
                        select(ServiceRequestBodySite.id).where(ServiceRequestBodySite.service_request_pk == sr.id)
                    )
                ))
                await session.execute(delete(ServiceRequestBodySite).where(ServiceRequestBodySite.service_request_pk == sr.id))
            if payload.based_on is not None:
                await session.execute(delete(ServiceRequestBasedOn).where(ServiceRequestBasedOn.service_request_pk == sr.id))
            if payload.replaces is not None:
                await session.execute(delete(ServiceRequestReplaces).where(ServiceRequestReplaces.service_request_pk == sr.id))
            if payload.performer is not None:
                await session.execute(delete(ServiceRequestPerformer).where(ServiceRequestPerformer.service_request_pk == sr.id))
            if payload.location_reference is not None:
                await session.execute(delete(ServiceRequestLocationReference).where(ServiceRequestLocationReference.service_request_pk == sr.id))
            if payload.reason_reference is not None:
                await session.execute(delete(ServiceRequestReasonReference).where(ServiceRequestReasonReference.service_request_pk == sr.id))
            if payload.insurance is not None:
                await session.execute(delete(ServiceRequestInsurance).where(ServiceRequestInsurance.service_request_pk == sr.id))
            if payload.supporting_info is not None:
                await session.execute(delete(ServiceRequestSupportingInfo).where(ServiceRequestSupportingInfo.service_request_pk == sr.id))
            if payload.specimen is not None:
                await session.execute(delete(ServiceRequestSpecimen).where(ServiceRequestSpecimen.service_request_pk == sr.id))
            if payload.note is not None:
                await session.execute(delete(ServiceRequestNote).where(ServiceRequestNote.service_request_pk == sr.id))
            if payload.relevant_history is not None:
                await session.execute(delete(ServiceRequestRelevantHistory).where(ServiceRequestRelevantHistory.service_request_pk == sr.id))

            await self._insert_sub_resources(session, sr.id, payload, sr.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted((_SUB | _SINGLE_OBJECT_FIELDS) & set(data.keys()))
            if replaced:
                logger.debug(
                    "ServiceRequest sub-resource lists replaced",
                    extra={"event": "service_request.sublists_replaced", "service_request_id": service_request_id, "replaced": replaced},
                )

        return await self.get_by_service_request_id(service_request_id)

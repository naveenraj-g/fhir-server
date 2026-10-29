from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import EncounterReferenceType
from app.models.observation import (
    ObservationBasedOn,
    ObservationBasedOnReferenceType,
    ObservationBodySiteCoding,
    ObservationCategory,
    ObservationCategoryCoding,
    ObservationComponent,
    ObservationComponentCodeCoding,
    ObservationComponentDataAbsentReasonCoding,
    ObservationComponentInterpretation,
    ObservationComponentInterpretationCoding,
    ObservationComponentReferenceRange,
    ObservationComponentReferenceRangeAppliesTo,
    ObservationComponentReferenceRangeAppliesToCoding,
    ObservationComponentReferenceRangeTypeCoding,
    ObservationComponentValueCodeableConceptCoding,
    ObservationDataAbsentReasonCoding,
    ObservationDerivedFrom,
    ObservationDerivedFromReferenceType,
    ObservationDeviceReferenceType,
    ObservationFocus,
    ObservationHasMember,
    ObservationHasMemberReferenceType,
    ObservationIdentifier,
    ObservationIdentifierTypeCoding,
    ObservationInterpretation,
    ObservationInterpretationCoding,
    ObservationMethodCoding,
    ObservationModel,
    ObservationNote,
    ObservationNoteAuthorReferenceType,
    ObservationPartOf,
    ObservationPartOfReferenceType,
    ObservationPerformer,
    ObservationPerformerReferenceType,
    ObservationQuantityComparator as ObservationQuantityComparatorModel,
    ObservationReferenceRange,
    ObservationReferenceRangeAppliesTo,
    ObservationReferenceRangeAppliesToCoding,
    ObservationReferenceRangeTypeCoding,
    ObservationSpecimenReferenceType,
    ObservationStatus as ObservationStatusModel,
    ObservationSubjectReferenceType,
    ObservationValueCodeableConceptCoding,
)
from app.schemas.observation import ObservationCreateSchema, ObservationPatchSchema

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _MODELED_BASED_ON_TYPES,
    _MODELED_DERIVED_FROM_TYPES,
    _MODELED_HAS_MEMBER_TYPES,
    _MODELED_NOTE_AUTHOR_TYPES,
    _MODELED_PERFORMER_TYPES,
    _MODELED_SUBJECT_TYPES,
    _org_ref_kwargs,
    _parse_org_ref,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)

_SUB = {
    "identifier", "based_on", "part_of", "category", "focus", "performer",
    "interpretation", "note", "reference_range", "has_member", "derived_from", "component",
}
_SINGLE_OBJECT_FIELDS = {
    "subject", "encounter", "value_codeable_concept", "data_absent_reason",
    "body_site", "method", "specimen", "device",
}
_EFFECTIVE_FIELDS = {
    "effective_date_time", "effective_period_start", "effective_period_end",
    "effective_timing", "effective_instant",
}
_VALUE_X_FIELDS = {
    "value_quantity_value", "value_quantity_comparator", "value_quantity_unit", "value_quantity_system",
    "value_quantity_code", "value_codeable_concept", "value_string", "value_boolean", "value_integer",
    "value_range_low_value", "value_range_low_unit", "value_range_low_system", "value_range_low_code",
    "value_range_high_value", "value_range_high_unit", "value_range_high_system", "value_range_high_code",
    "value_ratio_numerator_value", "value_ratio_numerator_comparator", "value_ratio_numerator_unit",
    "value_ratio_numerator_system", "value_ratio_numerator_code", "value_ratio_denominator_value",
    "value_ratio_denominator_comparator", "value_ratio_denominator_unit", "value_ratio_denominator_system",
    "value_ratio_denominator_code", "value_sampled_data_origin_value", "value_sampled_data_origin_unit",
    "value_sampled_data_origin_system", "value_sampled_data_origin_code", "value_sampled_data_period",
    "value_sampled_data_factor", "value_sampled_data_lower_limit", "value_sampled_data_upper_limit",
    "value_sampled_data_dimensions", "value_sampled_data_data", "value_time", "value_date_time",
    "value_period_start", "value_period_end",
}
_SPECIAL = {"status", "code"} | _SINGLE_OBJECT_FIELDS | _EFFECTIVE_FIELDS | _VALUE_X_FIELDS


def _model_status(v) -> ObservationStatusModel:
    return ObservationStatusModel[v.name]


def _model_comparator(v) -> ObservationQuantityComparatorModel:
    return ObservationQuantityComparatorModel[v.name]


def _coding_kwargs(coding, created_by: str | None) -> dict:
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _cc_text_kwargs(cc, prefix: str) -> dict:
    return {f"{prefix}text": cc.text if cc else None}


def _value_x_kwargs(obj) -> dict:
    """Full `value_*` column set for the 11-variant value[x] choice —
    shared shape between the root resource and its own component. Every
    column is always returned (possibly None); the comparator enums are
    converted schema-member -> model-member by NAME."""
    return {
        "value_quantity_value": obj.value_quantity_value,
        "value_quantity_comparator": _model_comparator(obj.value_quantity_comparator) if obj.value_quantity_comparator else None,
        "value_quantity_unit": obj.value_quantity_unit,
        "value_quantity_system": obj.value_quantity_system,
        "value_quantity_code": obj.value_quantity_code,
        "value_string": obj.value_string,
        "value_boolean": obj.value_boolean,
        "value_integer": obj.value_integer,
        "value_range_low_value": obj.value_range_low_value,
        "value_range_low_unit": obj.value_range_low_unit,
        "value_range_low_system": obj.value_range_low_system,
        "value_range_low_code": obj.value_range_low_code,
        "value_range_high_value": obj.value_range_high_value,
        "value_range_high_unit": obj.value_range_high_unit,
        "value_range_high_system": obj.value_range_high_system,
        "value_range_high_code": obj.value_range_high_code,
        "value_ratio_numerator_value": obj.value_ratio_numerator_value,
        "value_ratio_numerator_comparator": _model_comparator(obj.value_ratio_numerator_comparator) if obj.value_ratio_numerator_comparator else None,
        "value_ratio_numerator_unit": obj.value_ratio_numerator_unit,
        "value_ratio_numerator_system": obj.value_ratio_numerator_system,
        "value_ratio_numerator_code": obj.value_ratio_numerator_code,
        "value_ratio_denominator_value": obj.value_ratio_denominator_value,
        "value_ratio_denominator_comparator": _model_comparator(obj.value_ratio_denominator_comparator) if obj.value_ratio_denominator_comparator else None,
        "value_ratio_denominator_unit": obj.value_ratio_denominator_unit,
        "value_ratio_denominator_system": obj.value_ratio_denominator_system,
        "value_ratio_denominator_code": obj.value_ratio_denominator_code,
        "value_sampled_data_origin_value": obj.value_sampled_data_origin_value,
        "value_sampled_data_origin_unit": obj.value_sampled_data_origin_unit,
        "value_sampled_data_origin_system": obj.value_sampled_data_origin_system,
        "value_sampled_data_origin_code": obj.value_sampled_data_origin_code,
        "value_sampled_data_period": obj.value_sampled_data_period,
        "value_sampled_data_factor": obj.value_sampled_data_factor,
        "value_sampled_data_lower_limit": obj.value_sampled_data_lower_limit,
        "value_sampled_data_upper_limit": obj.value_sampled_data_upper_limit,
        "value_sampled_data_dimensions": obj.value_sampled_data_dimensions,
        "value_sampled_data_data": obj.value_sampled_data_data,
        "value_time": obj.value_time,
        "value_date_time": obj.value_date_time,
        "value_period_start": obj.value_period_start,
        "value_period_end": obj.value_period_end,
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


def _reference_range_kwargs(rr) -> dict:
    return {
        "low_value": rr.low_value, "low_unit": rr.low_unit, "low_system": rr.low_system, "low_code": rr.low_code,
        "high_value": rr.high_value, "high_unit": rr.high_unit, "high_system": rr.high_system, "high_code": rr.high_code,
        "type_text": rr.type.text if rr.type else None,
        "age_low_value": rr.age_low_value, "age_low_unit": rr.age_low_unit,
        "age_low_system": rr.age_low_system, "age_low_code": rr.age_low_code,
        "age_high_value": rr.age_high_value, "age_high_unit": rr.age_high_unit,
        "age_high_system": rr.age_high_system, "age_high_code": rr.age_high_code,
        "text": rr.text,
    }


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators."""

    async def create_full(
        self,
        payload: ObservationCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> ObservationModel:
        async with self.session_factory() as session:
            subject_kwargs = _single_reference_kwargs("subject", payload.subject, ObservationSubjectReferenceType)
            encounter_kwargs = _single_reference_kwargs("encounter", payload.encounter, EncounterReferenceType)
            specimen_kwargs = _single_reference_kwargs("specimen", payload.specimen, ObservationSpecimenReferenceType)
            device_kwargs = _single_reference_kwargs("device", payload.device, ObservationDeviceReferenceType)

            await _validate_ref(session, org_id, "subject", subject_kwargs["subject_type"], subject_kwargs["subject_id"], _MODELED_SUBJECT_TYPES)
            await _validate_ref(session, org_id, "encounter", encounter_kwargs["encounter_type"], encounter_kwargs["encounter_id"], None)
            await _validate_ref(session, org_id, "specimen", specimen_kwargs["specimen_type"], specimen_kwargs["specimen_id"], set())
            await _validate_ref(session, org_id, "device", device_kwargs["device_type"], device_kwargs["device_id"], set())

            obs = ObservationModel(
                tenant_id=org_id,
                user_id=payload.user_id,
                created_by=created_by,
                extension=payload.extension or [],
                status=_model_status(payload.status),
                code_text=payload.code.text if payload.code else None,
                **subject_kwargs,
                **encounter_kwargs,
                effective_date_time=payload.effective_date_time,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                effective_timing=payload.effective_timing,
                effective_instant=payload.effective_instant,
                issued=payload.issued,
                **_value_x_kwargs(payload),
                **_cc_text_kwargs(payload.value_codeable_concept, "value_codeable_concept_"),
                **_cc_text_kwargs(payload.data_absent_reason, "data_absent_reason_"),
                **_cc_text_kwargs(payload.body_site, "body_site_"),
                **_cc_text_kwargs(payload.method, "method_"),
                **specimen_kwargs,
                **device_kwargs,
            )
            session.add(obs)
            await session.flush()

            for coding in (payload.code.coding if payload.code else None) or []:
                session.add(ObservationCodeCoding(observation_pk=obs.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))
            for coding in (payload.value_codeable_concept.coding if payload.value_codeable_concept else None) or []:
                session.add(ObservationValueCodeableConceptCoding(observation_pk=obs.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            await self._insert_sub_resources(session, obs.id, payload, org_id, created_by)

            try:
                await session.commit()
                await session.refresh(obs)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_observation_id(obs.observation_id)

    async def _insert_sub_resources(self, session, obs_pk: int, payload, tenant_id: str, created_by: str | None) -> None:
        for i in payload.identifier or []:
            a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
            identifier = ObservationIdentifier(
                observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by,
                use=i.use, type_text=i.type_text, system=i.system, value=i.value,
                period_start=i.period_start, period_end=i.period_end,
                assigner_reference=i.assigner, assigner_type=a_type, assigner_id=a_id, assigner_display=i.assigner_display,
                **{f"assigner_{s}": getattr(i, f"assigner_{s}") for s in _IDENTIFIER_FALLBACK_SUFFIXES},
            )
            session.add(identifier)
            if i.type_coding:
                await session.flush()
                for coding in i.type_coding:
                    session.add(ObservationIdentifierTypeCoding(observation_identifier_id=identifier.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for b in payload.based_on or []:
            kwargs = _list_reference_kwargs(b, ObservationBasedOnReferenceType)
            await _validate_ref(session, tenant_id, "basedOn", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_BASED_ON_TYPES)
            session.add(ObservationBasedOn(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for p in payload.part_of or []:
            session.add(ObservationPartOf(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(p, ObservationPartOfReferenceType)))

        for c in payload.category or []:
            category = ObservationCategory(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, text=c.text)
            session.add(category)
            if c.coding:
                await session.flush()
                for coding in c.coding:
                    session.add(ObservationCategoryCoding(observation_category_id=category.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for f in payload.focus or []:
            session.add(ObservationFocus(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **_list_reference_kwargs(f, None)))

        for p in payload.performer or []:
            kwargs = _list_reference_kwargs(p, ObservationPerformerReferenceType)
            await _validate_ref(session, tenant_id, "performer", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_PERFORMER_TYPES)
            session.add(ObservationPerformer(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for i in payload.interpretation or []:
            interp = ObservationInterpretation(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, text=i.text)
            session.add(interp)
            if i.coding:
                await session.flush()
                for coding in i.coding:
                    session.add(ObservationInterpretationCoding(observation_interpretation_id=interp.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for n in payload.note or []:
            author_kwargs = _ref_kwargs("author", n.author_reference, n.author_reference_display, ObservationNoteAuthorReferenceType)
            if n.author_reference:
                await _validate_ref(session, tenant_id, "note.author", author_kwargs["author_type"], author_kwargs["author_id"], _MODELED_NOTE_AUTHOR_TYPES)
            session.add(ObservationNote(
                observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by,
                author_string=n.author_string, author_reference=n.author_reference, **author_kwargs,
                time=n.time, text=n.text,
            ))

        for rr in payload.reference_range or []:
            await self._insert_reference_range(session, obs_pk, rr, tenant_id, created_by)

        for h in payload.has_member or []:
            kwargs = _list_reference_kwargs(h, ObservationHasMemberReferenceType)
            await _validate_ref(session, tenant_id, "hasMember", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_HAS_MEMBER_TYPES)
            session.add(ObservationHasMember(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for d in payload.derived_from or []:
            kwargs = _list_reference_kwargs(d, ObservationDerivedFromReferenceType)
            await _validate_ref(session, tenant_id, "derivedFrom", kwargs.get("reference_type"), kwargs.get("reference_id"), _MODELED_DERIVED_FROM_TYPES)
            session.add(ObservationDerivedFrom(observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **kwargs))

        for c in payload.component or []:
            await self._insert_component(session, obs_pk, c, tenant_id, created_by)

    async def _insert_reference_range(self, session, obs_pk: int, rr, tenant_id: str, created_by: str | None) -> None:
        row = ObservationReferenceRange(
            observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by, **_reference_range_kwargs(rr)
        )
        session.add(row)
        await session.flush()
        for coding in (rr.type.coding if rr.type else None) or []:
            session.add(ObservationReferenceRangeTypeCoding(observation_reference_range_id=row.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
        for a in rr.applies_to or []:
            applies_to = ObservationReferenceRangeAppliesTo(
                observation_reference_range_id=row.id, tenant_id=tenant_id, created_by=created_by, text=a.text
            )
            session.add(applies_to)
            if a.coding:
                await session.flush()
                for coding in a.coding:
                    session.add(ObservationReferenceRangeAppliesToCoding(observation_reference_range_applies_to_id=applies_to.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

    async def _insert_component(self, session, obs_pk: int, c, tenant_id: str, created_by: str | None) -> None:
        component = ObservationComponent(
            observation_pk=obs_pk, tenant_id=tenant_id, created_by=created_by,
            code_text=c.code.text if c.code else None,
            **_value_x_kwargs(c),
            **_cc_text_kwargs(c.value_codeable_concept, "value_codeable_concept_"),
            **_cc_text_kwargs(c.data_absent_reason, "data_absent_reason_"),
        )
        session.add(component)
        await session.flush()

        for coding in (c.code.coding if c.code else None) or []:
            session.add(ObservationComponentCodeCoding(observation_component_id=component.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
        for coding in (c.value_codeable_concept.coding if c.value_codeable_concept else None) or []:
            session.add(ObservationComponentValueCodeableConceptCoding(observation_component_id=component.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
        for coding in (c.data_absent_reason.coding if c.data_absent_reason else None) or []:
            session.add(ObservationComponentDataAbsentReasonCoding(observation_component_id=component.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for i in c.interpretation or []:
            interp = ObservationComponentInterpretation(observation_component_id=component.id, tenant_id=tenant_id, created_by=created_by, text=i.text)
            session.add(interp)
            if i.coding:
                await session.flush()
                for coding in i.coding:
                    session.add(ObservationComponentInterpretationCoding(observation_component_interpretation_id=interp.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

        for rr in c.reference_range or []:
            rr_row = ObservationComponentReferenceRange(
                observation_component_id=component.id, tenant_id=tenant_id, created_by=created_by, **_reference_range_kwargs(rr)
            )
            session.add(rr_row)
            await session.flush()
            for coding in (rr.type.coding if rr.type else None) or []:
                session.add(ObservationComponentReferenceRangeTypeCoding(observation_component_reference_range_id=rr_row.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))
            for a in rr.applies_to or []:
                applies_to = ObservationComponentReferenceRangeAppliesTo(
                    observation_component_reference_range_id=rr_row.id, tenant_id=tenant_id, created_by=created_by, text=a.text
                )
                session.add(applies_to)
                if a.coding:
                    await session.flush()
                    for coding in a.coding:
                        session.add(ObservationComponentReferenceRangeAppliesToCoding(observation_component_reference_range_applies_to_id=applies_to.id, tenant_id=tenant_id, **_coding_kwargs(coding, created_by)))

    async def patch_full(
        self,
        observation_id: int,
        payload: ObservationPatchSchema,
        updated_by: str | None = None,
    ) -> ObservationModel | None:
        async with self.session_factory() as session:
            stmt = select(ObservationModel).where(ObservationModel.observation_id == observation_id)
            obs = (await session.execute(stmt)).scalars().first()
            if not obs:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set
            sub_created_by = updated_by if updated_by is not None else obs.created_by

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(obs, field, value)
            if updated_by is not None:
                obs.updated_by = updated_by

            if "status" in provided and payload.status is not None:
                obs.status = _model_status(payload.status)

            if "code" in provided and payload.code is not None:
                obs.code_text = payload.code.text
                await session.execute(delete(ObservationCodeCoding).where(ObservationCodeCoding.observation_pk == obs.id))
                for coding in payload.code.coding or []:
                    session.add(ObservationCodeCoding(observation_pk=obs.id, tenant_id=obs.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            if provided & _EFFECTIVE_FIELDS:
                for field in _EFFECTIVE_FIELDS:
                    if field in provided:
                        setattr(obs, field, getattr(payload, field))

            if provided & _VALUE_X_FIELDS:
                for col, value in _value_x_kwargs(payload).items():
                    if col in provided:
                        setattr(obs, col, value)
                if "value_codeable_concept" in provided:
                    cc = payload.value_codeable_concept
                    obs.value_codeable_concept_text = cc.text if cc else None
                    await session.execute(delete(ObservationValueCodeableConceptCoding).where(ObservationValueCodeableConceptCoding.observation_pk == obs.id))
                    for coding in (cc.coding if cc else None) or []:
                        session.add(ObservationValueCodeableConceptCoding(observation_pk=obs.id, tenant_id=obs.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            for field, text_prefix, coding_model, coding_fk in (
                ("data_absent_reason", "data_absent_reason_", ObservationDataAbsentReasonCoding, "observation_pk"),
                ("body_site", "body_site_", ObservationBodySiteCoding, "observation_pk"),
                ("method", "method_", ObservationMethodCoding, "observation_pk"),
            ):
                if field in provided:
                    cc = getattr(payload, field)
                    for col, value in _cc_text_kwargs(cc, text_prefix).items():
                        setattr(obs, col, value)
                    await session.execute(delete(coding_model).where(getattr(coding_model, coding_fk) == obs.id))
                    for coding in (cc.coding if cc else None) or []:
                        session.add(coding_model(observation_pk=obs.id, tenant_id=obs.tenant_id, **_coding_kwargs(coding, sub_created_by)))

            for prefix, enum_cls, modeled in (
                ("subject", ObservationSubjectReferenceType, _MODELED_SUBJECT_TYPES),
                ("encounter", EncounterReferenceType, None),
                ("specimen", ObservationSpecimenReferenceType, set()),
                ("device", ObservationDeviceReferenceType, set()),
            ):
                if prefix in provided:
                    kwargs = _single_reference_kwargs(prefix, getattr(payload, prefix), enum_cls)
                    await _validate_ref(session, obs.tenant_id, prefix, kwargs[f"{prefix}_type"], kwargs[f"{prefix}_id"], modeled)
                    for col, value in kwargs.items():
                        setattr(obs, col, value)

            if payload.identifier is not None:
                await session.execute(delete(ObservationIdentifierTypeCoding).where(
                    ObservationIdentifierTypeCoding.observation_identifier_id.in_(
                        select(ObservationIdentifier.id).where(ObservationIdentifier.observation_pk == obs.id)
                    )
                ))
                await session.execute(delete(ObservationIdentifier).where(ObservationIdentifier.observation_pk == obs.id))
            if payload.based_on is not None:
                await session.execute(delete(ObservationBasedOn).where(ObservationBasedOn.observation_pk == obs.id))
            if payload.part_of is not None:
                await session.execute(delete(ObservationPartOf).where(ObservationPartOf.observation_pk == obs.id))
            if payload.category is not None:
                await session.execute(delete(ObservationCategoryCoding).where(
                    ObservationCategoryCoding.observation_category_id.in_(
                        select(ObservationCategory.id).where(ObservationCategory.observation_pk == obs.id)
                    )
                ))
                await session.execute(delete(ObservationCategory).where(ObservationCategory.observation_pk == obs.id))
            if payload.focus is not None:
                await session.execute(delete(ObservationFocus).where(ObservationFocus.observation_pk == obs.id))
            if payload.performer is not None:
                await session.execute(delete(ObservationPerformer).where(ObservationPerformer.observation_pk == obs.id))
            if payload.interpretation is not None:
                await session.execute(delete(ObservationInterpretationCoding).where(
                    ObservationInterpretationCoding.observation_interpretation_id.in_(
                        select(ObservationInterpretation.id).where(ObservationInterpretation.observation_pk == obs.id)
                    )
                ))
                await session.execute(delete(ObservationInterpretation).where(ObservationInterpretation.observation_pk == obs.id))
            if payload.note is not None:
                await session.execute(delete(ObservationNote).where(ObservationNote.observation_pk == obs.id))
            if payload.reference_range is not None:
                rr_ids_subq = select(ObservationReferenceRange.id).where(ObservationReferenceRange.observation_pk == obs.id)
                applies_to_ids_subq = select(ObservationReferenceRangeAppliesTo.id).where(ObservationReferenceRangeAppliesTo.observation_reference_range_id.in_(rr_ids_subq))
                await session.execute(delete(ObservationReferenceRangeAppliesToCoding).where(ObservationReferenceRangeAppliesToCoding.observation_reference_range_applies_to_id.in_(applies_to_ids_subq)))
                await session.execute(delete(ObservationReferenceRangeAppliesTo).where(ObservationReferenceRangeAppliesTo.observation_reference_range_id.in_(rr_ids_subq)))
                await session.execute(delete(ObservationReferenceRangeTypeCoding).where(ObservationReferenceRangeTypeCoding.observation_reference_range_id.in_(rr_ids_subq)))
                await session.execute(delete(ObservationReferenceRange).where(ObservationReferenceRange.observation_pk == obs.id))
            if payload.has_member is not None:
                await session.execute(delete(ObservationHasMember).where(ObservationHasMember.observation_pk == obs.id))
            if payload.derived_from is not None:
                await session.execute(delete(ObservationDerivedFrom).where(ObservationDerivedFrom.observation_pk == obs.id))
            if payload.component is not None:
                comp_ids_subq = select(ObservationComponent.id).where(ObservationComponent.observation_pk == obs.id)
                comp_rr_ids_subq = select(ObservationComponentReferenceRange.id).where(ObservationComponentReferenceRange.observation_component_id.in_(comp_ids_subq))
                comp_applies_to_ids_subq = select(ObservationComponentReferenceRangeAppliesTo.id).where(ObservationComponentReferenceRangeAppliesTo.observation_component_reference_range_id.in_(comp_rr_ids_subq))
                await session.execute(delete(ObservationComponentReferenceRangeAppliesToCoding).where(ObservationComponentReferenceRangeAppliesToCoding.observation_component_reference_range_applies_to_id.in_(comp_applies_to_ids_subq)))
                await session.execute(delete(ObservationComponentReferenceRangeAppliesTo).where(ObservationComponentReferenceRangeAppliesTo.observation_component_reference_range_id.in_(comp_rr_ids_subq)))
                await session.execute(delete(ObservationComponentReferenceRangeTypeCoding).where(ObservationComponentReferenceRangeTypeCoding.observation_component_reference_range_id.in_(comp_rr_ids_subq)))
                await session.execute(delete(ObservationComponentReferenceRange).where(ObservationComponentReferenceRange.observation_component_id.in_(comp_ids_subq)))
                comp_interp_ids_subq = select(ObservationComponentInterpretation.id).where(ObservationComponentInterpretation.observation_component_id.in_(comp_ids_subq))
                await session.execute(delete(ObservationComponentInterpretationCoding).where(ObservationComponentInterpretationCoding.observation_component_interpretation_id.in_(comp_interp_ids_subq)))
                await session.execute(delete(ObservationComponentInterpretation).where(ObservationComponentInterpretation.observation_component_id.in_(comp_ids_subq)))
                await session.execute(delete(ObservationComponentCodeCoding).where(ObservationComponentCodeCoding.observation_component_id.in_(comp_ids_subq)))
                await session.execute(delete(ObservationComponentValueCodeableConceptCoding).where(ObservationComponentValueCodeableConceptCoding.observation_component_id.in_(comp_ids_subq)))
                await session.execute(delete(ObservationComponentDataAbsentReasonCoding).where(ObservationComponentDataAbsentReasonCoding.observation_component_id.in_(comp_ids_subq)))
                await session.execute(delete(ObservationComponent).where(ObservationComponent.observation_pk == obs.id))

            await self._insert_sub_resources(session, obs.id, payload, obs.tenant_id, sub_created_by)

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted((_SUB | _SINGLE_OBJECT_FIELDS) & set(data.keys()))
            if replaced:
                logger.debug(
                    "Observation sub-resource lists replaced",
                    extra={"event": "observation.sublists_replaced", "observation_id": observation_id, "replaced": replaced},
                )

        return await self.get_by_observation_id(observation_id)

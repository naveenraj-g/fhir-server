from sqlalchemy import select

from app.core.logging import get_logger
from app.models.enums import (
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
)
from app.models.specimen_definition import (
    SpecimenDefinitionAdditiveReferenceType,
    SpecimenDefinitionCollection,
    SpecimenDefinitionCollectionCoding,
    SpecimenDefinitionContainerAdditive,
    SpecimenDefinitionContainerAdditiveCoding,
    SpecimenDefinitionContainerCapCoding,
    SpecimenDefinitionContainerMaterialCoding,
    SpecimenDefinitionContainerTypeCoding,
    SpecimenDefinitionHandlingTempQualCoding,
    SpecimenDefinitionIdentifierTypeCoding,
    SpecimenDefinitionModel,
    SpecimenDefinitionPatientPreparation,
    SpecimenDefinitionPatientPreparationCoding,
    SpecimenDefinitionPreference,
    SpecimenDefinitionQuantityComparator,
    SpecimenDefinitionTypeCollectedCoding,
    SpecimenDefinitionTypeTested,
    SpecimenDefinitionTypeTestedHandling,
    SpecimenDefinitionTypeTestedRejectionCriterion,
    SpecimenDefinitionTypeTestedRejectionCriterionCoding,
    SpecimenDefinitionTypeTestedTypeCoding,
)
from app.schemas.specimen_definition import (
    SpecimenDefinitionCreateSchema,
    SpecimenDefinitionPatchSchema,
)

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)

_INPUT_COMPARATOR_MAP = {
    "<": SpecimenDefinitionQuantityComparator.lt,
    "<=": SpecimenDefinitionQuantityComparator.le,
    ">=": SpecimenDefinitionQuantityComparator.ge,
    ">": SpecimenDefinitionQuantityComparator.gt,
    "lt": SpecimenDefinitionQuantityComparator.lt,
    "le": SpecimenDefinitionQuantityComparator.le,
    "ge": SpecimenDefinitionQuantityComparator.ge,
    "gt": SpecimenDefinitionQuantityComparator.gt,
}


def _to_db_comparator(val) -> SpecimenDefinitionQuantityComparator | None:
    if not val:
        return None
    comp_str = val.value if hasattr(val, "value") else str(val)
    return _INPUT_COMPARATOR_MAP.get(comp_str)


def _to_db_preference(val) -> SpecimenDefinitionPreference:
    if not val:
        return SpecimenDefinitionPreference.preferred
    val_str = val.value if hasattr(val, "value") else str(val)
    return SpecimenDefinitionPreference(val_str)


def _to_db_identifier_use(val) -> IdentifierUseModel | None:
    if not val:
        return None
    val_str = val.name if hasattr(val, "name") else (val.value if hasattr(val, "value") else str(val))
    return IdentifierUseModel[val_str] if val_str in IdentifierUseModel.__members__ else None


def _build_identifier_fields(ident, org_id: str, actor_id: str):
    if not ident:
        cols = {
            "identifier_use": None,
            "identifier_type_text": None,
            "identifier_system": None,
            "identifier_value": None,
            "identifier_period_start": None,
            "identifier_period_end": None,
            "identifier_assigner_reference": None,
            "identifier_assigner_type": None,
            "identifier_assigner_id": None,
            "identifier_assigner_display": None,
        }
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
            cols[f"identifier_assigner_{suffix}"] = None
        return cols, []

    use = _to_db_identifier_use(getattr(ident, "use", None))
    assigner_str = getattr(ident, "assigner", None)
    assigner_display = getattr(ident, "assigner_display", None)
    ass_kw = _ref_kwargs("identifier_assigner", assigner_str, assigner_display, OrganizationReferenceType)

    cols = {
        "identifier_use": use,
        "identifier_type_text": getattr(ident, "type_text", None),
        "identifier_system": getattr(ident, "system", None),
        "identifier_value": getattr(ident, "value", None),
        "identifier_period_start": getattr(ident, "period_start", None),
        "identifier_period_end": getattr(ident, "period_end", None),
        "identifier_assigner_reference": assigner_str,
        "identifier_assigner_type": ass_kw["identifier_assigner_type"],
        "identifier_assigner_id": ass_kw["identifier_assigner_id"],
        "identifier_assigner_display": assigner_display,
    }
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(ident, f"assigner_{suffix}", None)
        if suffix == "identifier_use" and val is not None:
            cols[f"identifier_assigner_{suffix}"] = _to_db_identifier_use(val)
        else:
            cols[f"identifier_assigner_{suffix}"] = val

    type_codings = []
    for c in getattr(ident, "type_coding", None) or []:
        type_codings.append(
            SpecimenDefinitionIdentifierTypeCoding(
                system=getattr(c, "system", None),
                version=getattr(c, "version", None),
                code=getattr(c, "code", None),
                display=getattr(c, "display", None),
                user_selected=getattr(c, "user_selected", None),
                tenant_id=org_id,
                created_by=actor_id,
            )
        )
    return cols, type_codings


def _build_type_collected_codings(type_collected, org_id: str, actor_id: str):
    if not type_collected:
        return []
    codings = []
    for c in getattr(type_collected, "coding", None) or []:
        codings.append(
            SpecimenDefinitionTypeCollectedCoding(
                system=getattr(c, "system", None),
                version=getattr(c, "version", None),
                code=getattr(c, "code", None),
                display=getattr(c, "display", None),
                user_selected=getattr(c, "user_selected", None),
                tenant_id=org_id,
                created_by=actor_id,
            )
        )
    return codings


def _build_patient_preparations(preps, org_id: str, actor_id: str):
    result = []
    for p in preps or []:
        item = SpecimenDefinitionPatientPreparation(
            text=getattr(p, "text", None),
            tenant_id=org_id,
            created_by=actor_id,
        )
        codings = []
        for c in getattr(p, "coding", None) or []:
            codings.append(
                SpecimenDefinitionPatientPreparationCoding(
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                    tenant_id=org_id,
                    created_by=actor_id,
                )
            )
        item.codings = codings
        result.append(item)
    return result


def _build_collections(colls, org_id: str, actor_id: str):
    result = []
    for c_item in colls or []:
        item = SpecimenDefinitionCollection(
            text=getattr(c_item, "text", None),
            tenant_id=org_id,
            created_by=actor_id,
        )
        codings = []
        for c in getattr(c_item, "coding", None) or []:
            codings.append(
                SpecimenDefinitionCollectionCoding(
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                    tenant_id=org_id,
                    created_by=actor_id,
                )
            )
        item.codings = codings
        result.append(item)
    return result


def _build_types_tested(tts, org_id: str, actor_id: str):
    result = []
    for tt in tts or []:
        type_obj = getattr(tt, "type", None)
        tt_model = SpecimenDefinitionTypeTested(
            is_derived=getattr(tt, "is_derived", None),
            type_text=getattr(type_obj, "text", None) if type_obj else None,
            preference=_to_db_preference(getattr(tt, "preference", None)),
            requirement=getattr(tt, "requirement", None),
            retention_time_value=getattr(tt, "retention_time_value", None),
            retention_time_comparator=_to_db_comparator(getattr(tt, "retention_time_comparator", None)),
            retention_time_unit=getattr(tt, "retention_time_unit", None),
            retention_time_system=getattr(tt, "retention_time_system", None),
            retention_time_code=getattr(tt, "retention_time_code", None),
            tenant_id=org_id,
            created_by=actor_id,
        )

        # type.coding
        type_codings = []
        for c in (getattr(type_obj, "coding", None) if type_obj else None) or []:
            type_codings.append(
                SpecimenDefinitionTypeTestedTypeCoding(
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                    tenant_id=org_id,
                    created_by=actor_id,
                )
            )
        tt_model.type_codings = type_codings

        # container
        c = getattr(tt, "container", None)
        if c:
            mat_obj = getattr(c, "material", None)
            c_type_obj = getattr(c, "type", None)
            cap_obj = getattr(c, "cap", None)

            tt_model.container_description = getattr(c, "description", None)
            tt_model.container_preparation = getattr(c, "preparation", None)
            tt_model.container_material_text = getattr(mat_obj, "text", None) if mat_obj else None
            tt_model.container_type_text = getattr(c_type_obj, "text", None) if c_type_obj else None
            tt_model.container_cap_text = getattr(cap_obj, "text", None) if cap_obj else None

            tt_model.container_capacity_value = getattr(c, "capacity_value", None)
            tt_model.container_capacity_unit = getattr(c, "capacity_unit", None)
            tt_model.container_capacity_system = getattr(c, "capacity_system", None)
            tt_model.container_capacity_code = getattr(c, "capacity_code", None)

            tt_model.container_minimum_volume_string = getattr(c, "minimum_volume_string", None)
            tt_model.container_minimum_volume_quantity_value = getattr(c, "minimum_volume_quantity_value", None)
            tt_model.container_minimum_volume_quantity_comparator = _to_db_comparator(getattr(c, "minimum_volume_quantity_comparator", None))
            tt_model.container_minimum_volume_quantity_unit = getattr(c, "minimum_volume_quantity_unit", None)
            tt_model.container_minimum_volume_quantity_system = getattr(c, "minimum_volume_quantity_system", None)
            tt_model.container_minimum_volume_quantity_code = getattr(c, "minimum_volume_quantity_code", None)

            # container codings
            mat_codings = []
            for cd in (getattr(mat_obj, "coding", None) if mat_obj else None) or []:
                mat_codings.append(
                    SpecimenDefinitionContainerMaterialCoding(
                        system=getattr(cd, "system", None),
                        version=getattr(cd, "version", None),
                        code=getattr(cd, "code", None),
                        display=getattr(cd, "display", None),
                        user_selected=getattr(cd, "user_selected", None),
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                )
            tt_model.container_material_codings = mat_codings

            c_type_codings = []
            for cd in (getattr(c_type_obj, "coding", None) if c_type_obj else None) or []:
                c_type_codings.append(
                    SpecimenDefinitionContainerTypeCoding(
                        system=getattr(cd, "system", None),
                        version=getattr(cd, "version", None),
                        code=getattr(cd, "code", None),
                        display=getattr(cd, "display", None),
                        user_selected=getattr(cd, "user_selected", None),
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                )
            tt_model.container_type_codings = c_type_codings

            cap_codings = []
            for cd in (getattr(cap_obj, "coding", None) if cap_obj else None) or []:
                cap_codings.append(
                    SpecimenDefinitionContainerCapCoding(
                        system=getattr(cd, "system", None),
                        version=getattr(cd, "version", None),
                        code=getattr(cd, "code", None),
                        display=getattr(cd, "display", None),
                        user_selected=getattr(cd, "user_selected", None),
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                )
            tt_model.container_cap_codings = cap_codings

            # additives
            additives = []
            for a in getattr(c, "additive", None) or []:
                a_cc = getattr(a, "additive_codeable_concept", None)
                a_ref = getattr(a, "additive_reference", None)
                ref_kw = _single_reference_kwargs("additive_reference", a_ref, SpecimenDefinitionAdditiveReferenceType)

                ad_model = SpecimenDefinitionContainerAdditive(
                    additive_codeable_concept_text=getattr(a_cc, "text", None) if a_cc else None,
                    tenant_id=org_id,
                    created_by=actor_id,
                    **ref_kw,
                )
                ad_codings = []
                for cd in (getattr(a_cc, "coding", None) if a_cc else None) or []:
                    ad_codings.append(
                        SpecimenDefinitionContainerAdditiveCoding(
                            system=getattr(cd, "system", None),
                            version=getattr(cd, "version", None),
                            code=getattr(cd, "code", None),
                            display=getattr(cd, "display", None),
                            user_selected=getattr(cd, "user_selected", None),
                            tenant_id=org_id,
                            created_by=actor_id,
                        )
                    )
                ad_model.additive_codings = ad_codings
                additives.append(ad_model)
            tt_model.container_additives = additives

        # rejectionCriterion
        rejections = []
        for rc in getattr(tt, "rejection_criterion", None) or []:
            rc_model = SpecimenDefinitionTypeTestedRejectionCriterion(
                text=getattr(rc, "text", None),
                tenant_id=org_id,
                created_by=actor_id,
            )
            rc_codings = []
            for cd in getattr(rc, "coding", None) or []:
                rc_codings.append(
                    SpecimenDefinitionTypeTestedRejectionCriterionCoding(
                        system=getattr(cd, "system", None),
                        version=getattr(cd, "version", None),
                        code=getattr(cd, "code", None),
                        display=getattr(cd, "display", None),
                        user_selected=getattr(cd, "user_selected", None),
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                )
            rc_model.codings = rc_codings
            rejections.append(rc_model)
        tt_model.rejection_criteria = rejections

        # handling
        handlings = []
        for h in getattr(tt, "handling", None) or []:
            t_qual = getattr(h, "temperature_qualifier", None)
            h_model = SpecimenDefinitionTypeTestedHandling(
                temperature_qualifier_text=getattr(t_qual, "text", None) if t_qual else None,
                temperature_range_low_value=getattr(h, "temperature_range_low_value", None),
                temperature_range_low_unit=getattr(h, "temperature_range_low_unit", None),
                temperature_range_low_system=getattr(h, "temperature_range_low_system", None),
                temperature_range_low_code=getattr(h, "temperature_range_low_code", None),
                temperature_range_high_value=getattr(h, "temperature_range_high_value", None),
                temperature_range_high_unit=getattr(h, "temperature_range_high_unit", None),
                temperature_range_high_system=getattr(h, "temperature_range_high_system", None),
                temperature_range_high_code=getattr(h, "temperature_range_high_code", None),
                max_duration_value=getattr(h, "max_duration_value", None),
                max_duration_comparator=_to_db_comparator(getattr(h, "max_duration_comparator", None)),
                max_duration_unit=getattr(h, "max_duration_unit", None),
                max_duration_system=getattr(h, "max_duration_system", None),
                max_duration_code=getattr(h, "max_duration_code", None),
                instruction=getattr(h, "instruction", None),
                tenant_id=org_id,
                created_by=actor_id,
            )
            tq_codings = []
            for cd in (getattr(t_qual, "coding", None) if t_qual else None) or []:
                tq_codings.append(
                    SpecimenDefinitionHandlingTempQualCoding(
                        system=getattr(cd, "system", None),
                        version=getattr(cd, "version", None),
                        code=getattr(cd, "code", None),
                        display=getattr(cd, "display", None),
                        user_selected=getattr(cd, "user_selected", None),
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                )
            h_model.temperature_qualifier_codings = tq_codings
            handlings.append(h_model)
        tt_model.handlings = handlings

        result.append(tt_model)
    return result


class _FullMixin:
    """Atomic full Create & Patch operations for SpecimenDefinition."""

    async def create(
        self,
        payload: SpecimenDefinitionCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> SpecimenDefinitionModel:
        async with self.session_factory() as session:
            # 1. References validation
            ident = payload.identifier
            ident_cols, ident_codings = _build_identifier_fields(ident, org_id, actor_id)
            if ident and ident_cols.get("identifier_assigner_type") and ident_cols.get("identifier_assigner_id"):
                await _validate_ref(
                    session,
                    ident_cols["identifier_assigner_type"],
                    ident_cols["identifier_assigner_id"],
                    org_id,
                    "identifier.assigner",
                )

            tc = payload.type_collected
            tc_codings = _build_type_collected_codings(tc, org_id, actor_id)
            preps = _build_patient_preparations(payload.patient_preparation, org_id, actor_id)
            colls = _build_collections(payload.collection, org_id, actor_id)
            tts = _build_types_tested(payload.type_tested, org_id, actor_id)

            model = SpecimenDefinitionModel(
                time_aspect=payload.time_aspect,
                type_collected_text=tc.text if tc else None,
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                **ident_cols,
            )
            model.identifier_type_codings = ident_codings
            model.type_collected_codings = tc_codings
            model.patient_preparations = preps
            model.collections = colls
            model.types_tested = tts

            session.add(model)
            await session.commit()
            await session.refresh(model)
            res_id = model.specimen_definition_id

        return await self.get_by_specimen_definition_id(res_id)

    async def patch(
        self,
        specimen_definition_id: int,
        payload: SpecimenDefinitionPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> SpecimenDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(SpecimenDefinitionModel).where(
                    SpecimenDefinitionModel.specimen_definition_id == specimen_definition_id,
                    SpecimenDefinitionModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set

            if "time_aspect" in provided:
                model.time_aspect = payload.time_aspect

            if "type_collected" in provided:
                tc = payload.type_collected
                model.type_collected_text = tc.text if tc else None
                model.type_collected_codings = _build_type_collected_codings(tc, org_id, actor_id)

            if "identifier" in provided:
                ident = payload.identifier
                ident_cols, ident_codings = _build_identifier_fields(ident, org_id, actor_id)
                if ident and ident_cols.get("identifier_assigner_type") and ident_cols.get("identifier_assigner_id"):
                    await _validate_ref(
                        session,
                        ident_cols["identifier_assigner_type"],
                        ident_cols["identifier_assigner_id"],
                        org_id,
                        "identifier.assigner",
                    )
                for k, v in ident_cols.items():
                    setattr(model, k, v)
                model.identifier_type_codings = ident_codings

            if "patient_preparation" in provided:
                model.patient_preparations = _build_patient_preparations(payload.patient_preparation, org_id, actor_id)

            if "collection" in provided:
                model.collections = _build_collections(payload.collection, org_id, actor_id)

            if "type_tested" in provided:
                model.types_tested = _build_types_tested(payload.type_tested, org_id, actor_id)

            model.updated_by = actor_id
            await session.commit()
            await session.refresh(model)
            res_id = model.specimen_definition_id

        return await self.get_by_specimen_definition_id(res_id)

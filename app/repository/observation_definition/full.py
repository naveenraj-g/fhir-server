from __future__ import annotations

import datetime as dt

from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.enums import IdentifierUse
from app.models.observation_definition import (
    ObservationDefinitionCategory,
    ObservationDefinitionCategoryCoding,
    ObservationDefinitionCodeCoding,
    ObservationDefinitionGender,
    ObservationDefinitionIdentifier,
    ObservationDefinitionIdentifierTypeCoding,
    ObservationDefinitionMethodCoding,
    ObservationDefinitionModel,
    ObservationDefinitionPermittedDataType,
    ObservationDefinitionQualifiedInterval,
    ObservationDefinitionQualifiedIntervalAppliesTo,
    ObservationDefinitionQualifiedIntervalAppliesToCoding,
    ObservationDefinitionQualifiedIntervalCategory,
    ObservationDefinitionQualifiedIntervalContextCoding,
    ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding,
    ObservationDefinitionQuantitativeDetailsUnitCoding,
)
from app.schemas.observation_definition import (
    ObservationDefinitionCreateSchema,
    ObservationDefinitionPatchSchema,
)

from ._shared import (
    _parse_assigner_ref,
    _parse_value_set_ref,
    _validate_ref,
    _with_relationships,
)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    if isinstance(coding, dict):
        return {
            "tenant_id": org_id,
            "created_by": created_by,
            "system": coding.get("system"),
            "version": coding.get("version"),
            "code": coding.get("code"),
            "display": coding.get("display"),
            "user_selected": coding.get("user_selected"),
        }
    return {
        "tenant_id": org_id,
        "created_by": created_by,
        "system": getattr(coding, "system", None),
        "version": getattr(coding, "version", None),
        "code": getattr(coding, "code", None),
        "display": getattr(coding, "display", None),
        "user_selected": getattr(coding, "user_selected", None),
    }


async def _add_identifiers(
    session, observation_definition_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = ObservationDefinitionIdentifier(
            observation_definition_pk=observation_definition_pk,
            tenant_id=org_id,
            use=(
                IdentifierUse(i.use.value)
                if (i.use and hasattr(i.use, "value"))
                else IdentifierUse(i.use)
                if i.use
                else None
            ),
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    ObservationDefinitionIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_categories(
    session, observation_definition_pk: int, org_id: str, categories, created_by: str
) -> None:
    for cat in categories or []:
        category_row = ObservationDefinitionCategory(
            observation_definition_pk=observation_definition_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(category_row)
        await session.flush()

        for c in cat.coding or []:
            session.add(
                ObservationDefinitionCategoryCoding(
                    category_id=category_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_code_codings(
    session, observation_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ObservationDefinitionCodeCoding(
                observation_definition_pk=observation_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_method_codings(
    session, observation_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ObservationDefinitionMethodCoding(
                observation_definition_pk=observation_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_quantitative_details_codings(
    session, observation_definition_pk: int, org_id: str, qd, created_by: str
) -> None:
    if not qd:
        return
    if qd.customary_unit and qd.customary_unit.coding:
        for c in qd.customary_unit.coding:
            session.add(
                ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding(
                    observation_definition_pk=observation_definition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
    if qd.unit and qd.unit.coding:
        for c in qd.unit.coding:
            session.add(
                ObservationDefinitionQuantitativeDetailsUnitCoding(
                    observation_definition_pk=observation_definition_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_qualified_intervals(
    session, observation_definition_pk: int, org_id: str, intervals, created_by: str
) -> None:
    for qi in intervals or []:
        qi_row = ObservationDefinitionQualifiedInterval(
            observation_definition_pk=observation_definition_pk,
            tenant_id=org_id,
            category=(
                ObservationDefinitionQualifiedIntervalCategory(qi.category.value)
                if (qi.category and hasattr(qi.category, "value"))
                else ObservationDefinitionQualifiedIntervalCategory(qi.category)
                if qi.category
                else None
            ),
            range_low_value=qi.range_low_value,
            range_low_unit=qi.range_low_unit,
            range_low_system=qi.range_low_system,
            range_low_code=qi.range_low_code,
            range_high_value=qi.range_high_value,
            range_high_unit=qi.range_high_unit,
            range_high_system=qi.range_high_system,
            range_high_code=qi.range_high_code,
            context_text=qi.context.text if qi.context else None,
            gender=(
                ObservationDefinitionGender(qi.gender.value)
                if (qi.gender and hasattr(qi.gender, "value"))
                else ObservationDefinitionGender(qi.gender)
                if qi.gender
                else None
            ),
            age_low_value=qi.age_low_value,
            age_low_unit=qi.age_low_unit,
            age_low_system=qi.age_low_system,
            age_low_code=qi.age_low_code,
            age_high_value=qi.age_high_value,
            age_high_unit=qi.age_high_unit,
            age_high_system=qi.age_high_system,
            age_high_code=qi.age_high_code,
            gestational_age_low_value=qi.gestational_age_low_value,
            gestational_age_low_unit=qi.gestational_age_low_unit,
            gestational_age_low_system=qi.gestational_age_low_system,
            gestational_age_low_code=qi.gestational_age_low_code,
            gestational_age_high_value=qi.gestational_age_high_value,
            gestational_age_high_unit=qi.gestational_age_high_unit,
            gestational_age_high_system=qi.gestational_age_high_system,
            gestational_age_high_code=qi.gestational_age_high_code,
            condition=qi.condition,
            created_by=created_by,
        )
        session.add(qi_row)
        await session.flush()

        if qi.context and qi.context.coding:
            for c in qi.context.coding:
                session.add(
                    ObservationDefinitionQualifiedIntervalContextCoding(
                        qualified_interval_id=qi_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if qi.applies_to:
            for at in qi.applies_to:
                at_row = ObservationDefinitionQualifiedIntervalAppliesTo(
                    qualified_interval_id=qi_row.id,
                    tenant_id=org_id,
                    text=at.text,
                    created_by=created_by,
                )
                session.add(at_row)
                await session.flush()

                for c in at.coding or []:
                    session.add(
                        ObservationDefinitionQualifiedIntervalAppliesToCoding(
                            applies_to_id=at_row.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )


class _FullMixin:
    """Write operations for ObservationDefinition."""

    async def create_full(
        self,
        payload: ObservationDefinitionCreateSchema,
        org_id: str,
        created_by: str,
    ) -> ObservationDefinitionModel:
        async with self.session_factory() as session:
            v_type, v_id = (
                _parse_value_set_ref(payload.valid_coded_value_set)
                if payload.valid_coded_value_set
                else (None, None)
            )
            n_type, n_id = (
                _parse_value_set_ref(payload.normal_coded_value_set)
                if payload.normal_coded_value_set
                else (None, None)
            )
            a_type, a_id = (
                _parse_value_set_ref(payload.abnormal_coded_value_set)
                if payload.abnormal_coded_value_set
                else (None, None)
            )
            c_type, c_id = (
                _parse_value_set_ref(payload.critical_coded_value_set)
                if payload.critical_coded_value_set
                else (None, None)
            )

            qd = payload.quantitative_details
            cu_text = qd.customary_unit.text if (qd and qd.customary_unit) else None
            u_text = qd.unit.text if (qd and qd.unit) else None
            conv_fac = qd.conversion_factor if qd else None
            dec_prec = qd.decimal_precision if qd else None

            pdt = (
                [
                    ObservationDefinitionPermittedDataType(x.value)
                    if hasattr(x, "value")
                    else ObservationDefinitionPermittedDataType(x)
                    for x in payload.permitted_data_type
                ]
                if payload.permitted_data_type
                else None
            )

            model = ObservationDefinitionModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                code_text=payload.code.text if payload.code else None,
                permitted_data_type=pdt,
                multiple_results_allowed=payload.multiple_results_allowed,
                method_text=payload.method.text if payload.method else None,
                preferred_report_name=payload.preferred_report_name,
                quantitative_details_customary_unit_text=cu_text,
                quantitative_details_unit_text=u_text,
                quantitative_details_conversion_factor=conv_fac,
                quantitative_details_decimal_precision=dec_prec,
                valid_coded_value_set_reference=payload.valid_coded_value_set,
                valid_coded_value_set_type=v_type,
                valid_coded_value_set_id=v_id,
                valid_coded_value_set_display=payload.valid_coded_value_set_display,
                normal_coded_value_set_reference=payload.normal_coded_value_set,
                normal_coded_value_set_type=n_type,
                normal_coded_value_set_id=n_id,
                normal_coded_value_set_display=payload.normal_coded_value_set_display,
                abnormal_coded_value_set_reference=payload.abnormal_coded_value_set,
                abnormal_coded_value_set_type=a_type,
                abnormal_coded_value_set_id=a_id,
                abnormal_coded_value_set_display=payload.abnormal_coded_value_set_display,
                critical_coded_value_set_reference=payload.critical_coded_value_set,
                critical_coded_value_set_type=c_type,
                critical_coded_value_set_id=c_id,
                critical_coded_value_set_display=payload.critical_coded_value_set_display,
            )
            session.add(model)
            await session.flush()

            if payload.code and payload.code.coding:
                _add_code_codings(session, model.id, org_id, payload.code.coding, created_by)

            if payload.category:
                await _add_categories(session, model.id, org_id, payload.category, created_by)

            if payload.identifier:
                await _add_identifiers(session, model.id, org_id, payload.identifier, created_by)

            if payload.method and payload.method.coding:
                _add_method_codings(session, model.id, org_id, payload.method.coding, created_by)

            if payload.quantitative_details:
                _add_quantitative_details_codings(session, model.id, org_id, payload.quantitative_details, created_by)

            if payload.qualified_interval:
                await _add_qualified_intervals(session, model.id, org_id, payload.qualified_interval, created_by)

            await session.commit()

            stmt = select(ObservationDefinitionModel).where(
                ObservationDefinitionModel.id == model.id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def patch_full(
        self,
        observation_definition_id: int,
        payload: ObservationDefinitionPatchSchema,
        org_id: str,
        updated_by: str | None = None,
    ) -> ObservationDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ObservationDefinitionModel).where(
                ObservationDefinitionModel.observation_definition_id
                == observation_definition_id,
                ObservationDefinitionModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            fields_set = payload.model_fields_set

            if "multiple_results_allowed" in fields_set:
                model.multiple_results_allowed = payload.multiple_results_allowed
            if "preferred_report_name" in fields_set:
                model.preferred_report_name = payload.preferred_report_name
            if "permitted_data_type" in fields_set:
                model.permitted_data_type = (
                    [
                        ObservationDefinitionPermittedDataType(x.value)
                        if hasattr(x, "value")
                        else ObservationDefinitionPermittedDataType(x)
                        for x in payload.permitted_data_type
                    ]
                    if payload.permitted_data_type
                    else None
                )
            if "extension" in fields_set:
                model.extension = payload.extension or []

            # ValueSet references
            if "valid_coded_value_set" in fields_set or "valid_coded_value_set_display" in fields_set:
                v_type, v_id = (
                    _parse_value_set_ref(payload.valid_coded_value_set)
                    if payload.valid_coded_value_set
                    else (None, None)
                )
                model.valid_coded_value_set_reference = payload.valid_coded_value_set
                model.valid_coded_value_set_type = v_type
                model.valid_coded_value_set_id = v_id
                model.valid_coded_value_set_display = payload.valid_coded_value_set_display

            if "normal_coded_value_set" in fields_set or "normal_coded_value_set_display" in fields_set:
                n_type, n_id = (
                    _parse_value_set_ref(payload.normal_coded_value_set)
                    if payload.normal_coded_value_set
                    else (None, None)
                )
                model.normal_coded_value_set_reference = payload.normal_coded_value_set
                model.normal_coded_value_set_type = n_type
                model.normal_coded_value_set_id = n_id
                model.normal_coded_value_set_display = payload.normal_coded_value_set_display

            if "abnormal_coded_value_set" in fields_set or "abnormal_coded_value_set_display" in fields_set:
                a_type, a_id = (
                    _parse_value_set_ref(payload.abnormal_coded_value_set)
                    if payload.abnormal_coded_value_set
                    else (None, None)
                )
                model.abnormal_coded_value_set_reference = payload.abnormal_coded_value_set
                model.abnormal_coded_value_set_type = a_type
                model.abnormal_coded_value_set_id = a_id
                model.abnormal_coded_value_set_display = payload.abnormal_coded_value_set_display

            if "critical_coded_value_set" in fields_set or "critical_coded_value_set_display" in fields_set:
                c_type, c_id = (
                    _parse_value_set_ref(payload.critical_coded_value_set)
                    if payload.critical_coded_value_set
                    else (None, None)
                )
                model.critical_coded_value_set_reference = payload.critical_coded_value_set
                model.critical_coded_value_set_type = c_type
                model.critical_coded_value_set_id = c_id
                model.critical_coded_value_set_display = payload.critical_coded_value_set_display

            # code
            if "code" in fields_set:
                model.code_text = payload.code.text if payload.code else None
                await session.execute(
                    delete(ObservationDefinitionCodeCoding).where(
                        ObservationDefinitionCodeCoding.observation_definition_pk == model.id
                    )
                )
                if payload.code and payload.code.coding:
                    _add_code_codings(session, model.id, org_id, payload.code.coding, updated_by or model.created_by)

            # category
            if "category" in fields_set:
                cat_subq = select(ObservationDefinitionCategory.id).where(
                    ObservationDefinitionCategory.observation_definition_pk == model.id
                )
                await session.execute(
                    delete(ObservationDefinitionCategoryCoding).where(
                        ObservationDefinitionCategoryCoding.category_id.in_(cat_subq)
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionCategory).where(
                        ObservationDefinitionCategory.observation_definition_pk == model.id
                    )
                )
                if payload.category:
                    await _add_categories(session, model.id, org_id, payload.category, updated_by or model.created_by)

            # method
            if "method" in fields_set:
                model.method_text = payload.method.text if payload.method else None
                await session.execute(
                    delete(ObservationDefinitionMethodCoding).where(
                        ObservationDefinitionMethodCoding.observation_definition_pk == model.id
                    )
                )
                if payload.method and payload.method.coding:
                    _add_method_codings(session, model.id, org_id, payload.method.coding, updated_by or model.created_by)

            # quantitative_details
            if "quantitative_details" in fields_set:
                qd = payload.quantitative_details
                model.quantitative_details_customary_unit_text = qd.customary_unit.text if (qd and qd.customary_unit) else None
                model.quantitative_details_unit_text = qd.unit.text if (qd and qd.unit) else None
                model.quantitative_details_conversion_factor = qd.conversion_factor if qd else None
                model.quantitative_details_decimal_precision = qd.decimal_precision if qd else None

                await session.execute(
                    delete(ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding).where(
                        ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding.observation_definition_pk == model.id
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionQuantitativeDetailsUnitCoding).where(
                        ObservationDefinitionQuantitativeDetailsUnitCoding.observation_definition_pk == model.id
                    )
                )
                if qd:
                    _add_quantitative_details_codings(session, model.id, org_id, qd, updated_by or model.created_by)

            # qualified_interval
            if "qualified_interval" in fields_set:
                qi_subq = select(ObservationDefinitionQualifiedInterval.id).where(
                    ObservationDefinitionQualifiedInterval.observation_definition_pk == model.id
                )
                at_subq = select(ObservationDefinitionQualifiedIntervalAppliesTo.id).where(
                    ObservationDefinitionQualifiedIntervalAppliesTo.qualified_interval_id.in_(qi_subq)
                )
                await session.execute(
                    delete(ObservationDefinitionQualifiedIntervalAppliesToCoding).where(
                        ObservationDefinitionQualifiedIntervalAppliesToCoding.applies_to_id.in_(at_subq)
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionQualifiedIntervalAppliesTo).where(
                        ObservationDefinitionQualifiedIntervalAppliesTo.qualified_interval_id.in_(qi_subq)
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionQualifiedIntervalContextCoding).where(
                        ObservationDefinitionQualifiedIntervalContextCoding.qualified_interval_id.in_(qi_subq)
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionQualifiedInterval).where(
                        ObservationDefinitionQualifiedInterval.observation_definition_pk == model.id
                    )
                )
                if payload.qualified_interval:
                    await _add_qualified_intervals(session, model.id, org_id, payload.qualified_interval, updated_by or model.created_by)

            # identifier
            if "identifier" in fields_set:
                ident_subq = select(ObservationDefinitionIdentifier.id).where(
                    ObservationDefinitionIdentifier.observation_definition_pk == model.id
                )
                await session.execute(
                    delete(ObservationDefinitionIdentifierTypeCoding).where(
                        ObservationDefinitionIdentifierTypeCoding.identifier_id.in_(ident_subq)
                    )
                )
                await session.execute(
                    delete(ObservationDefinitionIdentifier).where(
                        ObservationDefinitionIdentifier.observation_definition_pk == model.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(session, model.id, org_id, payload.identifier, updated_by or model.created_by)

            if updated_by:
                model.updated_by = updated_by

            await session.commit()

            stmt = select(ObservationDefinitionModel).where(
                ObservationDefinitionModel.id == model.id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one()

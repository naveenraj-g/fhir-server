from sqlalchemy import delete, select

from app.core.filters import parse_reference
from app.core.logging import get_logger
from app.models.enums import (
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
)
from app.models.immunization_evaluation import (
    ImmunizationEvaluationAuthorityReferenceType,
    ImmunizationEvaluationDoseStatusCodingModel,
    ImmunizationEvaluationDoseStatusReasonCodingModel,
    ImmunizationEvaluationDoseStatusReasonModel,
    ImmunizationEvaluationIdentifierModel,
    ImmunizationEvaluationIdentifierTypeCodingModel,
    ImmunizationEvaluationImmunizationEventReferenceType,
    ImmunizationEvaluationModel,
    ImmunizationEvaluationPatientReferenceType,
    ImmunizationEvaluationTargetDiseaseCodingModel,
)
from app.schemas.immunization_evaluation import (
    ImmunizationEvaluationCreateSchema,
    ImmunizationEvaluationPatchSchema,
)

from ._shared import (
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _FullMixin:
    """Atomic full Create & Patch operations for ImmunizationEvaluation."""

    async def create(
        self,
        payload: ImmunizationEvaluationCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> ImmunizationEvaluationModel:
        async with self.session_factory() as session:
            # 1. References validation
            patient_kwargs = _single_reference_kwargs(
                "patient", payload.patient, ImmunizationEvaluationPatientReferenceType
            )
            if payload.patient:
                await _validate_ref(
                    session,
                    patient_kwargs["patient_type"],
                    patient_kwargs["patient_id"],
                    org_id,
                    "patient",
                )

            authority_kwargs = _single_reference_kwargs(
                "authority", payload.authority, ImmunizationEvaluationAuthorityReferenceType
            )
            if payload.authority:
                await _validate_ref(
                    session,
                    authority_kwargs["authority_type"],
                    authority_kwargs["authority_id"],
                    org_id,
                    "authority",
                )

            ie_kwargs = _single_reference_kwargs(
                "immunization_event",
                payload.immunization_event,
                ImmunizationEvaluationImmunizationEventReferenceType,
            )
            if payload.immunization_event:
                await _validate_ref(
                    session,
                    ie_kwargs["immunization_event_type"],
                    ie_kwargs["immunization_event_id"],
                    org_id,
                    "immunization_event",
                )

            if payload.identifier:
                for ident in payload.identifier:
                    assigner_kwargs = _single_reference_kwargs(
                        "assigner", ident, OrganizationReferenceType
                    )
                    if assigner_kwargs.get("assigner_type") and assigner_kwargs.get("assigner_id"):
                        await _validate_ref(
                            session,
                            assigner_kwargs["assigner_type"],
                            assigner_kwargs["assigner_id"],
                            org_id,
                            "assigner",
                        )

            # 2. Main record
            model = ImmunizationEvaluationModel(
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                status=payload.status,
                **patient_kwargs,
                date=payload.date,
                **authority_kwargs,
                target_disease_text=(
                    payload.target_disease.text if payload.target_disease else None
                ),
                **ie_kwargs,
                dose_status_text=(
                    payload.dose_status.text if payload.dose_status else None
                ),
                description=payload.description,
                series=payload.series,
                dose_number_positive_int=payload.dose_number_positive_int,
                dose_number_string=payload.dose_number_string,
                series_doses_positive_int=payload.series_doses_positive_int,
                series_doses_string=payload.series_doses_string,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            # 3. Target disease codings
            if payload.target_disease and payload.target_disease.coding:
                for c in payload.target_disease.coding:
                    session.add(
                        ImmunizationEvaluationTargetDiseaseCodingModel(
                            immunization_evaluation_pk=model.id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                            tenant_id=org_id,
                            created_by=actor_id,
                        )
                    )

            # 4. Dose status codings
            if payload.dose_status and payload.dose_status.coding:
                for c in payload.dose_status.coding:
                    session.add(
                        ImmunizationEvaluationDoseStatusCodingModel(
                            immunization_evaluation_pk=model.id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                            tenant_id=org_id,
                            created_by=actor_id,
                        )
                    )

            # 5. Dose status reasons
            if payload.dose_status_reason:
                for r in payload.dose_status_reason:
                    reason_row = ImmunizationEvaluationDoseStatusReasonModel(
                        immunization_evaluation_pk=model.id,
                        text=r.text,
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                    session.add(reason_row)
                    await session.flush()
                    if r.coding:
                        for c in r.coding:
                            session.add(
                                ImmunizationEvaluationDoseStatusReasonCodingModel(
                                    dose_status_reason_id=reason_row.id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                )
                            )

            # 6. Identifiers
            if payload.identifier:
                for ident in payload.identifier:
                    assigner_kwargs = _single_reference_kwargs(
                        "assigner", ident, OrganizationReferenceType
                    )
                    use_val = ident.use
                    if use_val is not None and hasattr(use_val, "name"):
                        use_val = IdentifierUseModel[use_val.name]

                    ident_row = ImmunizationEvaluationIdentifierModel(
                        immunization_evaluation_pk=model.id,
                        use=use_val,
                        type_text=ident.type.text if ident.type else None,
                        system=ident.system,
                        value=ident.value,
                        period_start=ident.period_start,
                        period_end=ident.period_end,
                        **assigner_kwargs,
                        tenant_id=org_id,
                        created_by=actor_id,
                    )
                    session.add(ident_row)
                    await session.flush()

                    if ident.type and ident.type.coding:
                        for c in ident.type.coding:
                            session.add(
                                ImmunizationEvaluationIdentifierTypeCodingModel(
                                    identifier_id=ident_row.id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                )
                            )

            await session.commit()
            eval_id = model.immunization_evaluation_id

        # Reload in fresh session with all relationships
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id == eval_id,
                    ImmunizationEvaluationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def patch(
        self,
        immunization_evaluation_id: int,
        payload: ImmunizationEvaluationPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> ImmunizationEvaluationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id
                    == immunization_evaluation_id,
                    ImmunizationEvaluationModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            data = payload.model_dump(exclude_unset=True)

            if "patient" in data:
                patient_kwargs = _single_reference_kwargs(
                    "patient", payload.patient, ImmunizationEvaluationPatientReferenceType
                )
                if payload.patient:
                    await _validate_ref(
                        session,
                        patient_kwargs["patient_type"],
                        patient_kwargs["patient_id"],
                        org_id,
                        "patient",
                    )
                for k, v in patient_kwargs.items():
                    setattr(model, k, v)

            if "authority" in data:
                authority_kwargs = _single_reference_kwargs(
                    "authority", payload.authority, ImmunizationEvaluationAuthorityReferenceType
                )
                if payload.authority:
                    await _validate_ref(
                        session,
                        authority_kwargs["authority_type"],
                        authority_kwargs["authority_id"],
                        org_id,
                        "authority",
                    )
                for k, v in authority_kwargs.items():
                    setattr(model, k, v)

            if "immunization_event" in data:
                ie_kwargs = _single_reference_kwargs(
                    "immunization_event",
                    payload.immunization_event,
                    ImmunizationEvaluationImmunizationEventReferenceType,
                )
                if payload.immunization_event:
                    await _validate_ref(
                        session,
                        ie_kwargs["immunization_event_type"],
                        ie_kwargs["immunization_event_id"],
                        org_id,
                        "immunization_event",
                    )
                for k, v in ie_kwargs.items():
                    setattr(model, k, v)

            if "status" in data:
                model.status = payload.status

            if "date" in data:
                model.date = payload.date

            if "target_disease" in data:
                model.target_disease_text = (
                    payload.target_disease.text if payload.target_disease else None
                )
                await session.execute(
                    delete(ImmunizationEvaluationTargetDiseaseCodingModel).where(
                        ImmunizationEvaluationTargetDiseaseCodingModel.immunization_evaluation_pk
                        == model.id
                    )
                )
                if payload.target_disease and payload.target_disease.coding:
                    for c in payload.target_disease.coding:
                        session.add(
                            ImmunizationEvaluationTargetDiseaseCodingModel(
                                immunization_evaluation_pk=model.id,
                                system=c.system,
                                version=c.version,
                                code=c.code,
                                display=c.display,
                                user_selected=c.user_selected,
                                tenant_id=org_id,
                                created_by=actor_id,
                            )
                        )

            if "dose_status" in data:
                model.dose_status_text = (
                    payload.dose_status.text if payload.dose_status else None
                )
                await session.execute(
                    delete(ImmunizationEvaluationDoseStatusCodingModel).where(
                        ImmunizationEvaluationDoseStatusCodingModel.immunization_evaluation_pk
                        == model.id
                    )
                )
                if payload.dose_status and payload.dose_status.coding:
                    for c in payload.dose_status.coding:
                        session.add(
                            ImmunizationEvaluationDoseStatusCodingModel(
                                immunization_evaluation_pk=model.id,
                                system=c.system,
                                version=c.version,
                                code=c.code,
                                display=c.display,
                                user_selected=c.user_selected,
                                tenant_id=org_id,
                                created_by=actor_id,
                            )
                        )

            if "dose_status_reason" in data:
                existing_reasons = (
                    await session.execute(
                        select(ImmunizationEvaluationDoseStatusReasonModel).where(
                            ImmunizationEvaluationDoseStatusReasonModel.immunization_evaluation_pk
                            == model.id
                        )
                    )
                ).scalars().all()
                for r in existing_reasons:
                    await session.execute(
                        delete(ImmunizationEvaluationDoseStatusReasonCodingModel).where(
                            ImmunizationEvaluationDoseStatusReasonCodingModel.dose_status_reason_id
                            == r.id
                        )
                    )
                    await session.delete(r)

                if payload.dose_status_reason:
                    for r in payload.dose_status_reason:
                        reason_row = ImmunizationEvaluationDoseStatusReasonModel(
                            immunization_evaluation_pk=model.id,
                            text=r.text,
                            tenant_id=org_id,
                            created_by=actor_id,
                        )
                        session.add(reason_row)
                        await session.flush()
                        if r.coding:
                            for c in r.coding:
                                session.add(
                                    ImmunizationEvaluationDoseStatusReasonCodingModel(
                                        dose_status_reason_id=reason_row.id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                    )
                                )

            if "identifier" in data:
                existing_idents = (
                    await session.execute(
                        select(ImmunizationEvaluationIdentifierModel).where(
                            ImmunizationEvaluationIdentifierModel.immunization_evaluation_pk
                            == model.id
                        )
                    )
                ).scalars().all()
                for i in existing_idents:
                    await session.execute(
                        delete(ImmunizationEvaluationIdentifierTypeCodingModel).where(
                            ImmunizationEvaluationIdentifierTypeCodingModel.identifier_id
                            == i.id
                        )
                    )
                    await session.delete(i)

                if payload.identifier:
                    for ident in payload.identifier:
                        assigner_kwargs = _single_reference_kwargs(
                            "assigner", ident, OrganizationReferenceType
                        )
                        if assigner_kwargs.get("assigner_type") and assigner_kwargs.get("assigner_id"):
                            await _validate_ref(
                                session,
                                assigner_kwargs["assigner_type"],
                                assigner_kwargs["assigner_id"],
                                org_id,
                                "assigner",
                            )

                        use_val = ident.use
                        if use_val is not None and hasattr(use_val, "name"):
                            use_val = IdentifierUseModel[use_val.name]

                        ident_row = ImmunizationEvaluationIdentifierModel(
                            immunization_evaluation_pk=model.id,
                            use=use_val,
                            type_text=ident.type.text if ident.type else None,
                            system=ident.system,
                            value=ident.value,
                            period_start=ident.period_start,
                            period_end=ident.period_end,
                            **assigner_kwargs,
                            tenant_id=org_id,
                            created_by=actor_id,
                        )
                        session.add(ident_row)
                        await session.flush()

                        if ident.type and ident.type.coding:
                            for c in ident.type.coding:
                                session.add(
                                    ImmunizationEvaluationIdentifierTypeCodingModel(
                                        identifier_id=ident_row.id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                    )
                                )

            for field in [
                "description",
                "series",
                "dose_number_positive_int",
                "dose_number_string",
                "series_doses_positive_int",
                "series_doses_string",
                "extension",
            ]:
                if field in data:
                    setattr(model, field, data[field])

            model.updated_by = actor_id
            await session.commit()

        # Reload fresh
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationEvaluationModel).where(
                    ImmunizationEvaluationModel.immunization_evaluation_id
                    == immunization_evaluation_id,
                    ImmunizationEvaluationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    create_full = create
    patch_full = patch


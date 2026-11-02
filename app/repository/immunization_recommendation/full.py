from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.immunization_recommendation import (
    ImmunizationRecommendationAuthorityReferenceType,
    ImmunizationRecommendationContraindicatedCodeCodingModel,
    ImmunizationRecommendationContraindicatedCodeModel,
    ImmunizationRecommendationDateCriterionCodeCodingModel,
    ImmunizationRecommendationDateCriterionModel,
    ImmunizationRecommendationForecastReasonCodingModel,
    ImmunizationRecommendationForecastReasonModel,
    ImmunizationRecommendationForecastStatusCodingModel,
    ImmunizationRecommendationIdentifierModel,
    ImmunizationRecommendationIdentifierTypeCodingModel,
    ImmunizationRecommendationModel,
    ImmunizationRecommendationPatientReferenceType,
    ImmunizationRecommendationRecommendationModel,
    ImmunizationRecommendationSupportingImmunizationModel,
    ImmunizationRecommendationSupportingImmunizationReferenceType,
    ImmunizationRecommendationSupportingPatientInformationModel,
    ImmunizationRecommendationSupportingPatientInformationReferenceType,
    ImmunizationRecommendationTargetDiseaseCodingModel,
    ImmunizationRecommendationVaccineCodeCodingModel,
    ImmunizationRecommendationVaccineCodeModel,
)
from app.schemas.immunization_recommendation import (
    ImmunizationRecommendationCreateSchema,
    ImmunizationRecommendationPatchSchema,
)

from ._shared import (
    _list_reference_kwargs,
    _ref_kwargs,
    _single_reference_kwargs,
    _validate_ref,
)

logger = get_logger(__name__)


class _FullMixin:
    """Full-model write operations (create, patch) for ImmunizationRecommendation."""

    async def create(
        self,
        payload: ImmunizationRecommendationCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> ImmunizationRecommendationModel:
        async with self.session_factory() as session:
            # 1. Validate root references
            pat_kwargs = _single_reference_kwargs(
                "patient", payload.patient, ImmunizationRecommendationPatientReferenceType
            )
            await _validate_ref(
                session,
                pat_kwargs["patient_type"],
                pat_kwargs["patient_id"],
                org_id,
                "patient",
            )

            auth_kwargs = _single_reference_kwargs(
                "authority", payload.authority, ImmunizationRecommendationAuthorityReferenceType
            )
            if payload.authority:
                await _validate_ref(
                    session,
                    auth_kwargs["authority_type"],
                    auth_kwargs["authority_id"],
                    org_id,
                    "authority",
                )

            # 2. Construct root model
            model = ImmunizationRecommendationModel(
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                date=payload.date,
                **pat_kwargs,
                **auth_kwargs,
            )
            session.add(model)
            await session.flush()

            # 3. Insert identifiers
            await self._insert_identifiers(
                session, model.id, payload.identifier, org_id, actor_id
            )

            # 4. Insert recommendations
            await self._insert_recommendations(
                session, model.id, payload.recommendation, org_id, actor_id
            )

            await session.commit()
            return await self.get_by_immunization_recommendation_id_in_org(
                model.immunization_recommendation_id, org_id
            )

    async def patch(
        self,
        immunization_recommendation_id: int,
        patch: ImmunizationRecommendationPatchSchema,
        org_id: str,
        actor_id: str,
    ) -> ImmunizationRecommendationModel | None:
        async with self.session_factory() as session:
            stmt = select(ImmunizationRecommendationModel).where(
                ImmunizationRecommendationModel.immunization_recommendation_id
                == immunization_recommendation_id,
                ImmunizationRecommendationModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            data = patch.model_dump(exclude_unset=True)
            imm_rec_pk = model.id

            if "patient" in data and patch.patient is not None:
                pat_kwargs = _single_reference_kwargs(
                    "patient", patch.patient, ImmunizationRecommendationPatientReferenceType
                )
                await _validate_ref(
                    session,
                    pat_kwargs["patient_type"],
                    pat_kwargs["patient_id"],
                    org_id,
                    "patient",
                )
                for k, v in pat_kwargs.items():
                    setattr(model, k, v)

            if "authority" in data:
                if patch.authority is not None:
                    auth_kwargs = _single_reference_kwargs(
                        "authority", patch.authority, ImmunizationRecommendationAuthorityReferenceType
                    )
                    await _validate_ref(
                        session,
                        auth_kwargs["authority_type"],
                        auth_kwargs["authority_id"],
                        org_id,
                        "authority",
                    )
                    for k, v in auth_kwargs.items():
                        setattr(model, k, v)
                else:
                    empty_auth = _single_reference_kwargs(
                        "authority", None, ImmunizationRecommendationAuthorityReferenceType
                    )
                    for k, v in empty_auth.items():
                        setattr(model, k, v)

            if "date" in data and patch.date is not None:
                model.date = patch.date

            if "identifier" in data:
                ident_ids = (
                    await session.execute(
                        select(ImmunizationRecommendationIdentifierModel.id).where(
                            ImmunizationRecommendationIdentifierModel.immunization_recommendation_pk
                            == imm_rec_pk
                        )
                    )
                ).scalars().all()
                if ident_ids:
                    await session.execute(
                        delete(ImmunizationRecommendationIdentifierTypeCodingModel).where(
                            ImmunizationRecommendationIdentifierTypeCodingModel.identifier_id.in_(ident_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationRecommendationIdentifierModel).where(
                        ImmunizationRecommendationIdentifierModel.immunization_recommendation_pk
                        == imm_rec_pk
                    )
                )
                await self._insert_identifiers(session, imm_rec_pk, patch.identifier, org_id, actor_id)

            if "recommendation" in data and patch.recommendation is not None:
                await self._delete_existing_recommendations(session, imm_rec_pk)
                await self._insert_recommendations(
                    session, imm_rec_pk, patch.recommendation, org_id, actor_id
                )

            model.updated_by = actor_id
            await session.commit()
            return await self.get_by_immunization_recommendation_id_in_org(
                immunization_recommendation_id, org_id
            )

    create_full = create
    patch_full = patch

    async def _delete_existing_recommendations(self, session, imm_rec_pk: int):
        rec_ids = (
            await session.execute(
                select(ImmunizationRecommendationRecommendationModel.id).where(
                    ImmunizationRecommendationRecommendationModel.immunization_recommendation_pk
                    == imm_rec_pk
                )
            )
        ).scalars().all()
        if not rec_ids:
            return

        # 1. vaccine codes
        vc_ids = (
            await session.execute(
                select(ImmunizationRecommendationVaccineCodeModel.id).where(
                    ImmunizationRecommendationVaccineCodeModel.recommendation_id.in_(rec_ids)
                )
            )
        ).scalars().all()
        if vc_ids:
            await session.execute(
                delete(ImmunizationRecommendationVaccineCodeCodingModel).where(
                    ImmunizationRecommendationVaccineCodeCodingModel.vaccine_code_id.in_(vc_ids)
                )
            )
            await session.execute(
                delete(ImmunizationRecommendationVaccineCodeModel).where(
                    ImmunizationRecommendationVaccineCodeModel.id.in_(vc_ids)
                )
            )

        # 2. target disease
        await session.execute(
            delete(ImmunizationRecommendationTargetDiseaseCodingModel).where(
                ImmunizationRecommendationTargetDiseaseCodingModel.recommendation_id.in_(rec_ids)
            )
        )

        # 3. contraindicated vaccine codes
        cvc_ids = (
            await session.execute(
                select(ImmunizationRecommendationContraindicatedCodeModel.id).where(
                    ImmunizationRecommendationContraindicatedCodeModel.recommendation_id.in_(rec_ids)
                )
            )
        ).scalars().all()
        if cvc_ids:
            await session.execute(
                delete(ImmunizationRecommendationContraindicatedCodeCodingModel).where(
                    ImmunizationRecommendationContraindicatedCodeCodingModel.contraindicated_code_id.in_(cvc_ids)
                )
            )
            await session.execute(
                delete(ImmunizationRecommendationContraindicatedCodeModel).where(
                    ImmunizationRecommendationContraindicatedCodeModel.id.in_(cvc_ids)
                )
            )

        # 4. forecast status
        await session.execute(
            delete(ImmunizationRecommendationForecastStatusCodingModel).where(
                ImmunizationRecommendationForecastStatusCodingModel.recommendation_id.in_(rec_ids)
            )
        )

        # 5. forecast reason
        fr_ids = (
            await session.execute(
                select(ImmunizationRecommendationForecastReasonModel.id).where(
                    ImmunizationRecommendationForecastReasonModel.recommendation_id.in_(rec_ids)
                )
            )
        ).scalars().all()
        if fr_ids:
            await session.execute(
                delete(ImmunizationRecommendationForecastReasonCodingModel).where(
                    ImmunizationRecommendationForecastReasonCodingModel.forecast_reason_id.in_(fr_ids)
                )
            )
            await session.execute(
                delete(ImmunizationRecommendationForecastReasonModel).where(
                    ImmunizationRecommendationForecastReasonModel.id.in_(fr_ids)
                )
            )

        # 6. date criteria
        dc_ids = (
            await session.execute(
                select(ImmunizationRecommendationDateCriterionModel.id).where(
                    ImmunizationRecommendationDateCriterionModel.recommendation_id.in_(rec_ids)
                )
            )
        ).scalars().all()
        if dc_ids:
            await session.execute(
                delete(ImmunizationRecommendationDateCriterionCodeCodingModel).where(
                    ImmunizationRecommendationDateCriterionCodeCodingModel.date_criterion_id.in_(dc_ids)
                )
            )
            await session.execute(
                delete(ImmunizationRecommendationDateCriterionModel).where(
                    ImmunizationRecommendationDateCriterionModel.id.in_(dc_ids)
                )
            )

        # 7. supporting immunizations
        await session.execute(
            delete(ImmunizationRecommendationSupportingImmunizationModel).where(
                ImmunizationRecommendationSupportingImmunizationModel.recommendation_id.in_(rec_ids)
            )
        )

        # 8. supporting patient info
        await session.execute(
            delete(ImmunizationRecommendationSupportingPatientInformationModel).where(
                ImmunizationRecommendationSupportingPatientInformationModel.recommendation_id.in_(rec_ids)
            )
        )

        # 9. recommendations root
        await session.execute(
            delete(ImmunizationRecommendationRecommendationModel).where(
                ImmunizationRecommendationRecommendationModel.id.in_(rec_ids)
            )
        )

    async def _insert_identifiers(
        self, session, imm_rec_pk: int, identifiers, org_id: str, actor: str
    ):
        if not identifiers:
            return
        for i in identifiers:
            assigner_type = None
            assigner_id = None
            if i.assigner:
                assigner_type, assigner_id = _ref_kwargs(
                    "assigner", i.assigner, i.assigner_display, OrganizationReferenceType
                )["assigner_type"], _ref_kwargs(
                    "assigner", i.assigner, i.assigner_display, OrganizationReferenceType
                )["assigner_id"]
                await _validate_ref(session, assigner_type, assigner_id, org_id, "identifier.assigner")

            row = ImmunizationRecommendationIdentifierModel(
                immunization_recommendation_pk=imm_rec_pk,
                tenant_id=org_id,
                created_by=actor,
                use=IdentifierUseModel[i.use.name] if i.use else None,
                type_text=i.type.text if i.type else None,
                system=i.system,
                value=i.value,
                period_start=i.period_start,
                period_end=i.period_end,
                assigner_reference=i.assigner,
                assigner_type=assigner_type,
                assigner_id=assigner_id,
                assigner_display=i.assigner_display,
                assigner_identifier_use=(
                    IdentifierUseModel[i.assigner_identifier_use.name]
                    if i.assigner_identifier_use
                    else None
                ),
                assigner_identifier_type_system=i.assigner_identifier_type_system,
                assigner_identifier_type_version=i.assigner_identifier_type_version,
                assigner_identifier_type_code=i.assigner_identifier_type_code,
                assigner_identifier_type_display=i.assigner_identifier_type_display,
                assigner_identifier_type_user_selected=i.assigner_identifier_type_user_selected,
                assigner_identifier_type_text=i.assigner_identifier_type_text,
                assigner_identifier_system=i.assigner_identifier_system,
                assigner_identifier_value=i.assigner_identifier_value,
                assigner_identifier_period_start=i.assigner_identifier_period_start,
                assigner_identifier_period_end=i.assigner_identifier_period_end,
            )
            session.add(row)
            await session.flush()

            if i.type and i.type.coding:
                for c in i.type.coding:
                    session.add(
                        ImmunizationRecommendationIdentifierTypeCodingModel(
                            identifier_id=row.id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

    async def _insert_recommendations(
        self, session, imm_rec_pk: int, recommendations, org_id: str, actor: str
    ):
        if not recommendations:
            return
        for r in recommendations:
            td_text = r.target_disease.text if r.target_disease else None
            fs_text = r.forecast_status.text if r.forecast_status else None

            rec_row = ImmunizationRecommendationRecommendationModel(
                immunization_recommendation_pk=imm_rec_pk,
                tenant_id=org_id,
                created_by=actor,
                target_disease_text=td_text,
                forecast_status_text=fs_text,
                description=r.description,
                series=r.series,
                dose_number_positive_int=r.dose_number_positive_int,
                dose_number_string=r.dose_number_string,
                series_doses_positive_int=r.series_doses_positive_int,
                series_doses_string=r.series_doses_string,
            )
            session.add(rec_row)
            await session.flush()
            rec_id = rec_row.id

            # 1. vaccine_code
            if r.vaccine_code:
                for vc in r.vaccine_code:
                    vc_row = ImmunizationRecommendationVaccineCodeModel(
                        recommendation_id=rec_id,
                        tenant_id=org_id,
                        created_by=actor,
                        text=vc.text,
                    )
                    session.add(vc_row)
                    await session.flush()

                    if vc.coding:
                        for c in vc.coding:
                            session.add(
                                ImmunizationRecommendationVaccineCodeCodingModel(
                                    vaccine_code_id=vc_row.id,
                                    tenant_id=org_id,
                                    created_by=actor,
                                    system=getattr(c, "system", None),
                                    version=getattr(c, "version", None),
                                    code=getattr(c, "code", None),
                                    display=getattr(c, "display", None),
                                    user_selected=getattr(c, "user_selected", None),
                                )
                            )

            # 2. target_disease
            if r.target_disease and r.target_disease.coding:
                for c in r.target_disease.coding:
                    session.add(
                        ImmunizationRecommendationTargetDiseaseCodingModel(
                            recommendation_id=rec_id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

            # 3. contraindicated_vaccine_code
            if r.contraindicated_vaccine_code:
                for cvc in r.contraindicated_vaccine_code:
                    cvc_row = ImmunizationRecommendationContraindicatedCodeModel(
                        recommendation_id=rec_id,
                        tenant_id=org_id,
                        created_by=actor,
                        text=cvc.text,
                    )
                    session.add(cvc_row)
                    await session.flush()

                    if cvc.coding:
                        for c in cvc.coding:
                            session.add(
                                ImmunizationRecommendationContraindicatedCodeCodingModel(
                                    contraindicated_code_id=cvc_row.id,
                                    tenant_id=org_id,
                                    created_by=actor,
                                    system=getattr(c, "system", None),
                                    version=getattr(c, "version", None),
                                    code=getattr(c, "code", None),
                                    display=getattr(c, "display", None),
                                    user_selected=getattr(c, "user_selected", None),
                                )
                            )

            # 4. forecast_status
            if r.forecast_status and r.forecast_status.coding:
                for c in r.forecast_status.coding:
                    session.add(
                        ImmunizationRecommendationForecastStatusCodingModel(
                            recommendation_id=rec_id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

            # 5. forecast_reason
            if r.forecast_reason:
                for fr in r.forecast_reason:
                    fr_row = ImmunizationRecommendationForecastReasonModel(
                        recommendation_id=rec_id,
                        tenant_id=org_id,
                        created_by=actor,
                        text=fr.text,
                    )
                    session.add(fr_row)
                    await session.flush()

                    if fr.coding:
                        for c in fr.coding:
                            session.add(
                                ImmunizationRecommendationForecastReasonCodingModel(
                                    forecast_reason_id=fr_row.id,
                                    tenant_id=org_id,
                                    created_by=actor,
                                    system=getattr(c, "system", None),
                                    version=getattr(c, "version", None),
                                    code=getattr(c, "code", None),
                                    display=getattr(c, "display", None),
                                    user_selected=getattr(c, "user_selected", None),
                                )
                            )

            # 6. date_criterion
            if r.date_criterion:
                for dc in r.date_criterion:
                    dc_row = ImmunizationRecommendationDateCriterionModel(
                        recommendation_id=rec_id,
                        tenant_id=org_id,
                        created_by=actor,
                        code_text=dc.code.text if dc.code else None,
                        value=dc.value,
                    )
                    session.add(dc_row)
                    await session.flush()

                    if dc.code and dc.code.coding:
                        for c in dc.code.coding:
                            session.add(
                                ImmunizationRecommendationDateCriterionCodeCodingModel(
                                    date_criterion_id=dc_row.id,
                                    tenant_id=org_id,
                                    created_by=actor,
                                    system=getattr(c, "system", None),
                                    version=getattr(c, "version", None),
                                    code=getattr(c, "code", None),
                                    display=getattr(c, "display", None),
                                    user_selected=getattr(c, "user_selected", None),
                                )
                            )

            # 7. supporting_immunization
            if r.supporting_immunization:
                for si in r.supporting_immunization:
                    si_kwargs = _list_reference_kwargs(
                        si, ImmunizationRecommendationSupportingImmunizationReferenceType
                    )
                    await _validate_ref(
                        session,
                        si_kwargs["reference_type"],
                        si_kwargs["reference_id"],
                        org_id,
                        "recommendation.supporting_immunization",
                    )
                    session.add(
                        ImmunizationRecommendationSupportingImmunizationModel(
                            recommendation_id=rec_id,
                            tenant_id=org_id,
                            created_by=actor,
                            **si_kwargs,
                        )
                    )

            # 8. supporting_patient_information
            if r.supporting_patient_information:
                for spi in r.supporting_patient_information:
                    spi_kwargs = _list_reference_kwargs(
                        spi, ImmunizationRecommendationSupportingPatientInformationReferenceType
                    )
                    await _validate_ref(
                        session,
                        spi_kwargs["reference_type"],
                        spi_kwargs["reference_id"],
                        org_id,
                        "recommendation.supporting_patient_information",
                    )
                    session.add(
                        ImmunizationRecommendationSupportingPatientInformationModel(
                            recommendation_id=rec_id,
                            tenant_id=org_id,
                            created_by=actor,
                            **spi_kwargs,
                        )
                    )

from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.immunization import (
    ImmunizationEducationModel,
    ImmunizationEncounterReferenceType,
    ImmunizationFundingSourceCodingModel,
    ImmunizationIdentifierModel,
    ImmunizationIdentifierTypeCodingModel,
    ImmunizationLocationReferenceType,
    ImmunizationManufacturerReferenceType,
    ImmunizationModel,
    ImmunizationNoteAuthorReferenceType,
    ImmunizationNoteModel,
    ImmunizationPatientReferenceType,
    ImmunizationPerformerActorReferenceType,
    ImmunizationPerformerFunctionCodingModel,
    ImmunizationPerformerModel,
    ImmunizationProgramEligibilityCodingModel,
    ImmunizationProgramEligibilityModel,
    ImmunizationProtocolAppliedAuthorityReferenceType,
    ImmunizationProtocolAppliedModel,
    ImmunizationProtocolAppliedTargetDiseaseCodingModel,
    ImmunizationProtocolAppliedTargetDiseaseModel,
    ImmunizationReactionDetailReferenceType,
    ImmunizationReactionModel,
    ImmunizationReasonCodeCodingModel,
    ImmunizationReasonCodeModel,
    ImmunizationReasonReferenceModel,
    ImmunizationReasonReferenceType,
    ImmunizationReportOriginCodingModel,
    ImmunizationRouteCodingModel,
    ImmunizationSiteCodingModel,
    ImmunizationStatus as ImmunizationStatusModel,
    ImmunizationStatusReasonCodingModel,
    ImmunizationSubpotentReasonCodingModel,
    ImmunizationSubpotentReasonModel,
    ImmunizationVaccineCodingModel,
)
from app.schemas.immunization import (
    ImmunizationCreateSchema,
    ImmunizationPatchSchema,
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

_SUB_COLLECTIONS = {
    "identifier",
    "status_reason",
    "vaccine_code",
    "report_origin",
    "site",
    "route",
    "funding_source",
    "performer",
    "note",
    "reason_code",
    "reason_reference",
    "subpotent_reason",
    "education",
    "program_eligibility",
    "reaction",
    "protocol_applied",
}


class _FullMixin:
    """Full nested create and patch cascades for Immunization."""

    async def create_full(
        self,
        payload: ImmunizationCreateSchema,
        org_id: str,
        created_by: str,
    ) -> ImmunizationModel:
        async with self.session_factory() as session:
            patient_kwargs = _single_reference_kwargs(
                "patient", payload.patient, ImmunizationPatientReferenceType
            )
            await _validate_ref(
                session,
                patient_kwargs["patient_type"],
                patient_kwargs["patient_id"],
                org_id,
                "patient",
            )

            encounter_kwargs = _single_reference_kwargs(
                "encounter", payload.encounter, ImmunizationEncounterReferenceType
            )
            await _validate_ref(
                session,
                encounter_kwargs["encounter_type"],
                encounter_kwargs["encounter_id"],
                org_id,
                "encounter",
            )

            location_kwargs = _single_reference_kwargs(
                "location", payload.location, ImmunizationLocationReferenceType
            )
            await _validate_ref(
                session,
                location_kwargs["location_type"],
                location_kwargs["location_id"],
                org_id,
                "location",
            )

            manufacturer_kwargs = _single_reference_kwargs(
                "manufacturer", payload.manufacturer, ImmunizationManufacturerReferenceType
            )
            await _validate_ref(
                session,
                manufacturer_kwargs["manufacturer_type"],
                manufacturer_kwargs["manufacturer_id"],
                org_id,
                "manufacturer",
            )

            status_val = payload.status
            if hasattr(status_val, "value"):
                status_model = ImmunizationStatusModel(status_val.value)
            elif status_val:
                status_model = ImmunizationStatusModel(status_val)
            else:
                status_model = ImmunizationStatusModel.completed

            dose_val = payload.dose_quantity.value if payload.dose_quantity else None
            dose_unit = payload.dose_quantity.unit if payload.dose_quantity else None
            dose_system = payload.dose_quantity.system if payload.dose_quantity else None
            dose_code = payload.dose_quantity.code if payload.dose_quantity else None

            model = ImmunizationModel(
                tenant_id=org_id,
                created_by=created_by,
                status=status_model,
                status_reason_text=payload.status_reason.text if payload.status_reason else None,
                vaccine_code_text=payload.vaccine_code.text if payload.vaccine_code else None,
                occurrence_date_time=payload.occurrence_date_time,
                occurrence_string=payload.occurrence_string,
                recorded=payload.recorded,
                primary_source=payload.primary_source,
                report_origin_text=payload.report_origin.text if payload.report_origin else None,
                lot_number=payload.lot_number,
                expiration_date=payload.expiration_date,
                site_text=payload.site.text if payload.site else None,
                route_text=payload.route.text if payload.route else None,
                dose_quantity_value=dose_val,
                dose_quantity_unit=dose_unit,
                dose_quantity_system=dose_system,
                dose_quantity_code=dose_code,
                is_subpotent=payload.is_subpotent,
                funding_source_text=payload.funding_source.text if payload.funding_source else None,
                **patient_kwargs,
                **encounter_kwargs,
                **location_kwargs,
                **manufacturer_kwargs,
            )
            session.add(model)
            await session.flush()

            imm_pk = model.id

            await self._insert_status_reason_codings(session, imm_pk, payload.status_reason, org_id, created_by)
            await self._insert_vaccine_codings(session, imm_pk, payload.vaccine_code, org_id, created_by)
            await self._insert_report_origin_codings(session, imm_pk, payload.report_origin, org_id, created_by)
            await self._insert_site_codings(session, imm_pk, payload.site, org_id, created_by)
            await self._insert_route_codings(session, imm_pk, payload.route, org_id, created_by)
            await self._insert_funding_source_codings(session, imm_pk, payload.funding_source, org_id, created_by)

            await self._insert_identifiers(session, imm_pk, payload.identifier, org_id, created_by)
            await self._insert_performers(session, imm_pk, payload.performer, org_id, created_by)
            await self._insert_notes(session, imm_pk, payload.note, org_id, created_by)
            await self._insert_reason_codes(session, imm_pk, payload.reason_code, org_id, created_by)
            await self._insert_reason_references(session, imm_pk, payload.reason_reference, org_id, created_by)
            await self._insert_subpotent_reasons(session, imm_pk, payload.subpotent_reason, org_id, created_by)
            await self._insert_education(session, imm_pk, payload.education, org_id, created_by)
            await self._insert_program_eligibility(session, imm_pk, payload.program_eligibility, org_id, created_by)
            await self._insert_reactions(session, imm_pk, payload.reaction, org_id, created_by)
            await self._insert_protocol_applied(session, imm_pk, payload.protocol_applied, org_id, created_by)

            await session.commit()
            return await self.get_by_immunization_id_in_org(model.immunization_id, org_id)

    async def patch_full(
        self,
        immunization_id: int,
        payload: ImmunizationPatchSchema,
        org_id: str,
        updated_by: str | None = None,
    ) -> ImmunizationModel | None:
        async with self.session_factory() as session:
            stmt = select(ImmunizationModel).where(
                ImmunizationModel.immunization_id == immunization_id,
                ImmunizationModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            imm_pk = model.id
            data = payload.model_dump(exclude_unset=True)

            if "patient" in data and payload.patient is not None:
                patient_kwargs = _single_reference_kwargs(
                    "patient", payload.patient, ImmunizationPatientReferenceType
                )
                await _validate_ref(
                    session,
                    patient_kwargs["patient_type"],
                    patient_kwargs["patient_id"],
                    org_id,
                    "patient",
                )
                for k, v in patient_kwargs.items():
                    setattr(model, k, v)

            if "encounter" in data:
                encounter_kwargs = _single_reference_kwargs(
                    "encounter", payload.encounter, ImmunizationEncounterReferenceType
                )
                if payload.encounter is not None:
                    await _validate_ref(
                        session,
                        encounter_kwargs["encounter_type"],
                        encounter_kwargs["encounter_id"],
                        org_id,
                        "encounter",
                    )
                for k, v in encounter_kwargs.items():
                    setattr(model, k, v)

            if "location" in data:
                location_kwargs = _single_reference_kwargs(
                    "location", payload.location, ImmunizationLocationReferenceType
                )
                if payload.location is not None:
                    await _validate_ref(
                        session,
                        location_kwargs["location_type"],
                        location_kwargs["location_id"],
                        org_id,
                        "location",
                    )
                for k, v in location_kwargs.items():
                    setattr(model, k, v)

            if "manufacturer" in data:
                manufacturer_kwargs = _single_reference_kwargs(
                    "manufacturer", payload.manufacturer, ImmunizationManufacturerReferenceType
                )
                if payload.manufacturer is not None:
                    await _validate_ref(
                        session,
                        manufacturer_kwargs["manufacturer_type"],
                        manufacturer_kwargs["manufacturer_id"],
                        org_id,
                        "manufacturer",
                    )
                for k, v in manufacturer_kwargs.items():
                    setattr(model, k, v)

            if "status" in data and payload.status is not None:
                status_val = payload.status
                model.status = (
                    ImmunizationStatusModel(status_val.value)
                    if hasattr(status_val, "value")
                    else ImmunizationStatusModel(status_val)
                )

            if "dose_quantity" in data:
                dq = payload.dose_quantity
                model.dose_quantity_value = dq.value if dq else None
                model.dose_quantity_unit = dq.unit if dq else None
                model.dose_quantity_system = dq.system if dq else None
                model.dose_quantity_code = dq.code if dq else None

            # Scalar fields
            _scalar_fields = [
                "occurrence_date_time",
                "occurrence_string",
                "recorded",
                "primary_source",
                "lot_number",
                "expiration_date",
                "is_subpotent",
            ]
            for field in _scalar_fields:
                if field in data:
                    setattr(model, field, data[field])

            actor_user = updated_by or "system"

            if "status_reason" in data:
                model.status_reason_text = payload.status_reason.text if payload.status_reason else None
                await session.execute(
                    delete(ImmunizationStatusReasonCodingModel).where(
                        ImmunizationStatusReasonCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_status_reason_codings(session, imm_pk, payload.status_reason, org_id, actor_user)

            if "vaccine_code" in data:
                model.vaccine_code_text = payload.vaccine_code.text if payload.vaccine_code else None
                await session.execute(
                    delete(ImmunizationVaccineCodingModel).where(
                        ImmunizationVaccineCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_vaccine_codings(session, imm_pk, payload.vaccine_code, org_id, actor_user)

            if "report_origin" in data:
                model.report_origin_text = payload.report_origin.text if payload.report_origin else None
                await session.execute(
                    delete(ImmunizationReportOriginCodingModel).where(
                        ImmunizationReportOriginCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_report_origin_codings(session, imm_pk, payload.report_origin, org_id, actor_user)

            if "site" in data:
                model.site_text = payload.site.text if payload.site else None
                await session.execute(
                    delete(ImmunizationSiteCodingModel).where(
                        ImmunizationSiteCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_site_codings(session, imm_pk, payload.site, org_id, actor_user)

            if "route" in data:
                model.route_text = payload.route.text if payload.route else None
                await session.execute(
                    delete(ImmunizationRouteCodingModel).where(
                        ImmunizationRouteCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_route_codings(session, imm_pk, payload.route, org_id, actor_user)

            if "funding_source" in data:
                model.funding_source_text = payload.funding_source.text if payload.funding_source else None
                await session.execute(
                    delete(ImmunizationFundingSourceCodingModel).where(
                        ImmunizationFundingSourceCodingModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_funding_source_codings(session, imm_pk, payload.funding_source, org_id, actor_user)

            if "identifier" in data:
                sub_ids = (
                    await session.execute(
                        select(ImmunizationIdentifierModel.id).where(
                            ImmunizationIdentifierModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if sub_ids:
                    await session.execute(
                        delete(ImmunizationIdentifierTypeCodingModel).where(
                            ImmunizationIdentifierTypeCodingModel.identifier_id.in_(sub_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationIdentifierModel).where(
                        ImmunizationIdentifierModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_identifiers(session, imm_pk, payload.identifier, org_id, actor_user)

            if "performer" in data:
                sub_ids = (
                    await session.execute(
                        select(ImmunizationPerformerModel.id).where(
                            ImmunizationPerformerModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if sub_ids:
                    await session.execute(
                        delete(ImmunizationPerformerFunctionCodingModel).where(
                            ImmunizationPerformerFunctionCodingModel.performer_id.in_(sub_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationPerformerModel).where(
                        ImmunizationPerformerModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_performers(session, imm_pk, payload.performer, org_id, actor_user)

            if "note" in data:
                await session.execute(
                    delete(ImmunizationNoteModel).where(
                        ImmunizationNoteModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_notes(session, imm_pk, payload.note, org_id, actor_user)

            if "reason_code" in data:
                sub_ids = (
                    await session.execute(
                        select(ImmunizationReasonCodeModel.id).where(
                            ImmunizationReasonCodeModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if sub_ids:
                    await session.execute(
                        delete(ImmunizationReasonCodeCodingModel).where(
                            ImmunizationReasonCodeCodingModel.reason_code_id.in_(sub_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationReasonCodeModel).where(
                        ImmunizationReasonCodeModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_reason_codes(session, imm_pk, payload.reason_code, org_id, actor_user)

            if "reason_reference" in data:
                await session.execute(
                    delete(ImmunizationReasonReferenceModel).where(
                        ImmunizationReasonReferenceModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_reason_references(session, imm_pk, payload.reason_reference, org_id, actor_user)

            if "subpotent_reason" in data:
                sub_ids = (
                    await session.execute(
                        select(ImmunizationSubpotentReasonModel.id).where(
                            ImmunizationSubpotentReasonModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if sub_ids:
                    await session.execute(
                        delete(ImmunizationSubpotentReasonCodingModel).where(
                            ImmunizationSubpotentReasonCodingModel.subpotent_reason_id.in_(sub_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationSubpotentReasonModel).where(
                        ImmunizationSubpotentReasonModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_subpotent_reasons(session, imm_pk, payload.subpotent_reason, org_id, actor_user)

            if "education" in data:
                await session.execute(
                    delete(ImmunizationEducationModel).where(
                        ImmunizationEducationModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_education(session, imm_pk, payload.education, org_id, actor_user)

            if "program_eligibility" in data:
                sub_ids = (
                    await session.execute(
                        select(ImmunizationProgramEligibilityModel.id).where(
                            ImmunizationProgramEligibilityModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if sub_ids:
                    await session.execute(
                        delete(ImmunizationProgramEligibilityCodingModel).where(
                            ImmunizationProgramEligibilityCodingModel.program_eligibility_id.in_(sub_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationProgramEligibilityModel).where(
                        ImmunizationProgramEligibilityModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_program_eligibility(session, imm_pk, payload.program_eligibility, org_id, actor_user)

            if "reaction" in data:
                await session.execute(
                    delete(ImmunizationReactionModel).where(
                        ImmunizationReactionModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_reactions(session, imm_pk, payload.reaction, org_id, actor_user)

            if "protocol_applied" in data:
                pa_ids = (
                    await session.execute(
                        select(ImmunizationProtocolAppliedModel.id).where(
                            ImmunizationProtocolAppliedModel.immunization_pk == imm_pk
                        )
                    )
                ).scalars().all()
                if pa_ids:
                    td_ids = (
                        await session.execute(
                            select(ImmunizationProtocolAppliedTargetDiseaseModel.id).where(
                                ImmunizationProtocolAppliedTargetDiseaseModel.protocol_applied_id.in_(pa_ids)
                            )
                        )
                    ).scalars().all()
                    if td_ids:
                        await session.execute(
                            delete(ImmunizationProtocolAppliedTargetDiseaseCodingModel).where(
                                ImmunizationProtocolAppliedTargetDiseaseCodingModel.target_disease_id.in_(td_ids)
                            )
                        )
                    await session.execute(
                        delete(ImmunizationProtocolAppliedTargetDiseaseModel).where(
                            ImmunizationProtocolAppliedTargetDiseaseModel.protocol_applied_id.in_(pa_ids)
                        )
                    )
                await session.execute(
                    delete(ImmunizationProtocolAppliedModel).where(
                        ImmunizationProtocolAppliedModel.immunization_pk == imm_pk
                    )
                )
                await self._insert_protocol_applied(session, imm_pk, payload.protocol_applied, org_id, actor_user)

            if updated_by:
                model.updated_by = updated_by

            await session.commit()
            return await self.get_by_immunization_id_in_org(immunization_id, org_id)

    # ── Insertion Helpers ─────────────────────────────────────────────────────

    async def _insert_status_reason_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationStatusReasonCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_vaccine_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationVaccineCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_report_origin_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationReportOriginCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_site_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationSiteCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_route_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationRouteCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_funding_source_codings(self, session, imm_pk: int, cc, org_id: str, actor: str):
        if not cc or not getattr(cc, "coding", None):
            return
        for c in cc.coding or []:
            session.add(
                ImmunizationFundingSourceCodingModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    system=getattr(c, "system", None),
                    version=getattr(c, "version", None),
                    code=getattr(c, "code", None),
                    display=getattr(c, "display", None),
                    user_selected=getattr(c, "user_selected", None),
                )
            )

    async def _insert_identifiers(self, session, imm_pk: int, identifiers, org_id: str, actor: str):
        if not identifiers:
            return
        for item in identifiers:
            assigner_type, assigner_id = _parse_org_ref(item.assigner)
            await _validate_ref(session, assigner_type, assigner_id, org_id, "identifier.assigner")
            use_val = item.use
            if hasattr(use_val, "name"):
                use_val = IdentifierUseModel[use_val.name]

            row = ImmunizationIdentifierModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                use=use_val,
                type_text=item.type.text if item.type else None,
                system=item.system,
                value=item.value,
                period_start=item.period_start,
                period_end=item.period_end,
                assigner_reference=item.assigner,
                assigner_type=assigner_type,
                assigner_id=assigner_id,
                assigner_display=item.assigner_display,
                assigner_identifier_use=(
                    IdentifierUseModel[item.assigner_identifier_use.name]
                    if hasattr(item.assigner_identifier_use, "name")
                    else item.assigner_identifier_use
                ),
                assigner_identifier_type_system=item.assigner_identifier_type_system,
                assigner_identifier_type_version=item.assigner_identifier_type_version,
                assigner_identifier_type_code=item.assigner_identifier_type_code,
                assigner_identifier_type_display=item.assigner_identifier_type_display,
                assigner_identifier_type_user_selected=item.assigner_identifier_type_user_selected,
                assigner_identifier_type_text=item.assigner_identifier_type_text,
                assigner_identifier_system=item.assigner_identifier_system,
                assigner_identifier_value=item.assigner_identifier_value,
                assigner_identifier_period_start=item.assigner_identifier_period_start,
                assigner_identifier_period_end=item.assigner_identifier_period_end,
            )
            session.add(row)
            await session.flush()

            if item.type and item.type.coding:
                for c in item.type.coding:
                    session.add(
                        ImmunizationIdentifierTypeCodingModel(
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

    async def _insert_performers(self, session, imm_pk: int, performers, org_id: str, actor: str):
        if not performers:
            return
        for p in performers:
            actor_kwargs = _single_reference_kwargs(
                "actor", p.actor, ImmunizationPerformerActorReferenceType
            )
            await _validate_ref(
                session,
                actor_kwargs["actor_type"],
                actor_kwargs["actor_id"],
                org_id,
                "performer.actor",
            )
            row = ImmunizationPerformerModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                function_text=p.function.text if p.function else None,
                **actor_kwargs,
            )
            session.add(row)
            await session.flush()

            if p.function and p.function.coding:
                for c in p.function.coding:
                    session.add(
                        ImmunizationPerformerFunctionCodingModel(
                            performer_id=row.id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

    async def _insert_notes(self, session, imm_pk: int, notes, org_id: str, actor: str):
        if not notes:
            return
        for n in notes:
            author_ref = getattr(n, "author_reference", None)
            author_disp = getattr(n, "author_display", None)
            ref_info = _ref_kwargs("author", author_ref, author_disp, ImmunizationNoteAuthorReferenceType)
            await _validate_ref(session, ref_info["author_type"], ref_info["author_id"], org_id, "note.author")

            row = ImmunizationNoteModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference=author_ref,
                **ref_info,
                author_identifier_use=(
                    IdentifierUseModel[n.author_identifier_use.name]
                    if hasattr(n.author_identifier_use, "name")
                    else n.author_identifier_use
                ),
                author_identifier_type_system=n.author_identifier_type_system,
                author_identifier_type_version=n.author_identifier_type_version,
                author_identifier_type_code=n.author_identifier_type_code,
                author_identifier_type_display=n.author_identifier_type_display,
                author_identifier_type_user_selected=n.author_identifier_type_user_selected,
                author_identifier_type_text=n.author_identifier_type_text,
                author_identifier_system=n.author_identifier_system,
                author_identifier_value=n.author_identifier_value,
                author_identifier_period_start=n.author_identifier_period_start,
                author_identifier_period_end=n.author_identifier_period_end,
            )
            session.add(row)

    async def _insert_reason_codes(self, session, imm_pk: int, reason_codes, org_id: str, actor: str):
        if not reason_codes:
            return
        for rc in reason_codes:
            row = ImmunizationReasonCodeModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                text=rc.text,
            )
            session.add(row)
            await session.flush()

            if rc.coding:
                for c in rc.coding:
                    session.add(
                        ImmunizationReasonCodeCodingModel(
                            reason_code_id=row.id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

    async def _insert_reason_references(self, session, imm_pk: int, reason_references, org_id: str, actor: str):
        if not reason_references:
            return
        for rr in reason_references:
            rr_kwargs = _list_reference_kwargs(rr, ImmunizationReasonReferenceType)
            await _validate_ref(
                session,
                rr_kwargs["reference_type"],
                rr_kwargs["reference_id"],
                org_id,
                "reason_reference",
            )
            session.add(
                ImmunizationReasonReferenceModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    **rr_kwargs,
                )
            )

    async def _insert_subpotent_reasons(self, session, imm_pk: int, subpotent_reasons, org_id: str, actor: str):
        if not subpotent_reasons:
            return
        for sr in subpotent_reasons:
            row = ImmunizationSubpotentReasonModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                text=sr.text,
            )
            session.add(row)
            await session.flush()

            if sr.coding:
                for c in sr.coding:
                    session.add(
                        ImmunizationSubpotentReasonCodingModel(
                            subpotent_reason_id=row.id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

    async def _insert_education(self, session, imm_pk: int, education, org_id: str, actor: str):
        if not education:
            return
        for e in education:
            session.add(
                ImmunizationEducationModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    document_type=e.document_type,
                    reference=e.reference,
                    publication_date=e.publication_date,
                    presentation_date=e.presentation_date,
                )
            )

    async def _insert_program_eligibility(self, session, imm_pk: int, program_eligibilities, org_id: str, actor: str):
        if not program_eligibilities:
            return
        for pe in program_eligibilities:
            row = ImmunizationProgramEligibilityModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                text=pe.text,
            )
            session.add(row)
            await session.flush()

            if pe.coding:
                for c in pe.coding:
                    session.add(
                        ImmunizationProgramEligibilityCodingModel(
                            program_eligibility_id=row.id,
                            tenant_id=org_id,
                            created_by=actor,
                            system=getattr(c, "system", None),
                            version=getattr(c, "version", None),
                            code=getattr(c, "code", None),
                            display=getattr(c, "display", None),
                            user_selected=getattr(c, "user_selected", None),
                        )
                    )

    async def _insert_reactions(self, session, imm_pk: int, reactions, org_id: str, actor: str):
        if not reactions:
            return
        for r in reactions:
            detail_kwargs = _single_reference_kwargs(
                "detail", r.detail, ImmunizationReactionDetailReferenceType
            )
            if r.detail:
                await _validate_ref(
                    session,
                    detail_kwargs["detail_type"],
                    detail_kwargs["detail_id"],
                    org_id,
                    "reaction.detail",
                )
            session.add(
                ImmunizationReactionModel(
                    immunization_pk=imm_pk,
                    tenant_id=org_id,
                    created_by=actor,
                    date=r.date,
                    reported=r.reported,
                    **detail_kwargs,
                )
            )

    async def _insert_protocol_applied(self, session, imm_pk: int, protocol_applied, org_id: str, actor: str):
        if not protocol_applied:
            return
        for pa in protocol_applied:
            auth_kwargs = _single_reference_kwargs(
                "authority", pa.authority, ImmunizationProtocolAppliedAuthorityReferenceType
            )
            if pa.authority:
                await _validate_ref(
                    session,
                    auth_kwargs["authority_type"],
                    auth_kwargs["authority_id"],
                    org_id,
                    "protocol_applied.authority",
                )
            row = ImmunizationProtocolAppliedModel(
                immunization_pk=imm_pk,
                tenant_id=org_id,
                created_by=actor,
                series=pa.series,
                dose_number_positive_int=pa.dose_number_positive_int,
                dose_number_string=pa.dose_number_string,
                series_doses_positive_int=pa.series_doses_positive_int,
                series_doses_string=pa.series_doses_string,
                **auth_kwargs,
            )
            session.add(row)
            await session.flush()

            if pa.target_disease:
                for td in pa.target_disease:
                    td_row = ImmunizationProtocolAppliedTargetDiseaseModel(
                        protocol_applied_id=row.id,
                        tenant_id=org_id,
                        created_by=actor,
                        text=td.text,
                    )
                    session.add(td_row)
                    await session.flush()

                    if td.coding:
                        for c in td.coding:
                            session.add(
                                ImmunizationProtocolAppliedTargetDiseaseCodingModel(
                                    target_disease_id=td_row.id,
                                    tenant_id=org_id,
                                    created_by=actor,
                                    system=getattr(c, "system", None),
                                    version=getattr(c, "version", None),
                                    code=getattr(c, "code", None),
                                    display=getattr(c, "display", None),
                                    user_selected=getattr(c, "user_selected", None),
                                )
                            )

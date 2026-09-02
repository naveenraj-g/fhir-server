from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.healthcare_service import (
    HealthcareServiceAvailableTime,
    HealthcareServiceCategory,
    HealthcareServiceCharacteristic,
    HealthcareServiceCommunication,
    HealthcareServiceCoverageArea,
    HealthcareServiceEligibility,
    HealthcareServiceEndpoint,
    HealthcareServiceIdentifier,
    HealthcareServiceLocation,
    HealthcareServiceModel,
    HealthcareServiceNotAvailable,
    HealthcareServiceProgram,
    HealthcareServiceReferralMethod,
    HealthcareServiceServiceProvisionCode,
    HealthcareServiceSpecialty,
    HealthcareServiceTelecom,
    HealthcareServiceType,
)
from app.schemas.healthcare_service import (
    HealthcareServiceCreateSchema,
    HealthcareServicePatchSchema,
)

from ._shared import (
    _coverage_area_ref_kwargs,
    _location_ref_kwargs,
    _org_ref_kwargs,
    _parse_coverage_area_ref,
    _parse_endpoint_ref,
    _parse_location_ref,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)


def _days_of_week(days) -> str | None:
    return ",".join(d.value for d in days) if days else None


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 16 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: HealthcareServiceCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> HealthcareServiceModel:
        """Create a HealthcareService plus any combination of its 16
        sub-resource lists, atomically in one DB transaction. Every list on
        the payload is optional; only the ones supplied get inserted."""
        pb_type, pb_id = (
            _parse_org_ref(payload.provided_by) if payload.provided_by else (None, None)
        )
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, pb_type, pb_id, "providedBy")
            hs = HealthcareServiceModel(
                org_id=org_id,
                created_by=created_by,
                active=payload.active,
                name=payload.name,
                **_org_ref_kwargs(
                    "provided_by", payload.provided_by, payload.provided_by_display
                ),
                **_reference_kwargs("provided_by", payload),
                comment=payload.comment,
                extra_details=payload.extra_details,
                photo_content_type=payload.photo_content_type,
                photo_language=payload.photo_language,
                photo_data=payload.photo_data,
                photo_url=payload.photo_url,
                photo_size=payload.photo_size,
                photo_hash=payload.photo_hash,
                photo_title=payload.photo_title,
                photo_creation=payload.photo_creation,
                appointment_required=payload.appointment_required,
                availability_exceptions=payload.availability_exceptions,
            )
            session.add(hs)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        HealthcareServiceIdentifier(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=created_by,
                        )
                    )

            if payload.category:
                for c in payload.category:
                    session.add(
                        HealthcareServiceCategory(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=c.coding_system,
                            coding_version=c.coding_version,
                            coding_code=c.coding_code,
                            coding_display=c.coding_display,
                            text=c.text,
                            coding_user_selected=c.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.type:
                for t in payload.type:
                    session.add(
                        HealthcareServiceType(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=t.coding_system,
                            coding_version=t.coding_version,
                            coding_code=t.coding_code,
                            coding_display=t.coding_display,
                            text=t.text,
                            coding_user_selected=t.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.specialty:
                for sp in payload.specialty:
                    session.add(
                        HealthcareServiceSpecialty(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=sp.coding_system,
                            coding_version=sp.coding_version,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                            coding_user_selected=sp.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.location:
                for loc in payload.location:
                    loc_type, loc_id = (
                        _parse_location_ref(loc.reference)
                        if loc.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, loc_type, loc_id, "location"
                    )
                    session.add(
                        HealthcareServiceLocation(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            **_location_ref_kwargs(
                                "reference", loc.reference, loc.reference_display
                            ),
                            **_reference_kwargs("reference", loc),
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
                    session.add(
                        HealthcareServiceTelecom(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=created_by,
                        )
                    )

            if payload.coverage_area:
                for ca in payload.coverage_area:
                    ca_type, ca_id = (
                        _parse_coverage_area_ref(ca.reference)
                        if ca.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, ca_type, ca_id, "coverageArea"
                    )
                    session.add(
                        HealthcareServiceCoverageArea(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            **_coverage_area_ref_kwargs(
                                "reference", ca.reference, ca.reference_display
                            ),
                            **_reference_kwargs("reference", ca),
                            created_by=created_by,
                        )
                    )

            if payload.service_provision_code:
                for spc in payload.service_provision_code:
                    session.add(
                        HealthcareServiceServiceProvisionCode(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=spc.coding_system,
                            coding_version=spc.coding_version,
                            coding_code=spc.coding_code,
                            coding_display=spc.coding_display,
                            text=spc.text,
                            coding_user_selected=spc.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.eligibility:
                for e in payload.eligibility:
                    session.add(
                        HealthcareServiceEligibility(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            code_system=e.code_system,
                            code_version=e.code_version,
                            code_code=e.code_code,
                            code_display=e.code_display,
                            code_text=e.code_text,
                            code_user_selected=e.code_user_selected,
                            comment=e.comment,
                            created_by=created_by,
                        )
                    )

            if payload.program:
                for p in payload.program:
                    session.add(
                        HealthcareServiceProgram(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=p.coding_system,
                            coding_version=p.coding_version,
                            coding_code=p.coding_code,
                            coding_display=p.coding_display,
                            text=p.text,
                            coding_user_selected=p.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.characteristic:
                for c in payload.characteristic:
                    session.add(
                        HealthcareServiceCharacteristic(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=c.coding_system,
                            coding_version=c.coding_version,
                            coding_code=c.coding_code,
                            coding_display=c.coding_display,
                            text=c.text,
                            coding_user_selected=c.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.communication:
                for cm in payload.communication:
                    session.add(
                        HealthcareServiceCommunication(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=cm.coding_system,
                            coding_version=cm.coding_version,
                            coding_code=cm.coding_code,
                            coding_display=cm.coding_display,
                            text=cm.text,
                            coding_user_selected=cm.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.referral_method:
                for rm in payload.referral_method:
                    session.add(
                        HealthcareServiceReferralMethod(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            coding_system=rm.coding_system,
                            coding_version=rm.coding_version,
                            coding_code=rm.coding_code,
                            coding_display=rm.coding_display,
                            text=rm.text,
                            coding_user_selected=rm.coding_user_selected,
                            created_by=created_by,
                        )
                    )

            if payload.available_time:
                for at in payload.available_time:
                    session.add(
                        HealthcareServiceAvailableTime(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            days_of_week=_days_of_week(at.days_of_week),
                            all_day=at.all_day,
                            available_start_time=at.available_start_time,
                            available_end_time=at.available_end_time,
                            created_by=created_by,
                        )
                    )

            if payload.not_available:
                for na in payload.not_available:
                    session.add(
                        HealthcareServiceNotAvailable(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            description=na.description,
                            during_start=na.during_start,
                            during_end=na.during_end,
                            created_by=created_by,
                        )
                    )

            if payload.endpoint:
                for e in payload.endpoint:
                    ep_type, ep_id = (
                        _parse_endpoint_ref(e.reference)
                        if e.reference
                        else (None, None)
                    )
                    session.add(
                        HealthcareServiceEndpoint(
                            healthcare_service_id=hs.id,
                            org_id=org_id,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_display=e.reference_display,
                            **_reference_kwargs("reference", e),
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
                await session.refresh(hs)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_healthcare_service_id(hs.healthcare_service_id)

    async def patch_full(
        self,
        healthcare_service_id: int,
        payload: HealthcareServicePatchSchema,
        updated_by: str | None = None,
    ) -> HealthcareServiceModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(HealthcareServiceModel).where(
                HealthcareServiceModel.healthcare_service_id == healthcare_service_id
            )
            hs = (await session.execute(stmt)).scalars().first()
            if not hs:
                return None

            _SUB = {
                "identifier",
                "category",
                "type",
                "specialty",
                "location",
                "telecom",
                "coverage_area",
                "service_provision_code",
                "eligibility",
                "program",
                "characteristic",
                "communication",
                "referral_method",
                "available_time",
                "not_available",
                "endpoint",
            }
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                if field == "provided_by":
                    if value is not None:
                        pb_type, pb_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, hs.org_id, pb_type, pb_id, "providedBy"
                        )
                        hs.provided_by_type = pb_type
                        hs.provided_by_id = pb_id
                    else:
                        hs.provided_by_type = None
                        hs.provided_by_id = None
                else:
                    setattr(hs, field, value)
            if updated_by is not None:
                hs.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(HealthcareServiceIdentifier).where(
                        HealthcareServiceIdentifier.healthcare_service_id == hs.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, hs.org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        HealthcareServiceIdentifier(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=updated_by,
                        )
                    )

            if payload.category is not None:
                await session.execute(
                    delete(HealthcareServiceCategory).where(
                        HealthcareServiceCategory.healthcare_service_id == hs.id
                    )
                )
                for c in payload.category:
                    session.add(
                        HealthcareServiceCategory(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=c.coding_system,
                            coding_version=c.coding_version,
                            coding_code=c.coding_code,
                            coding_display=c.coding_display,
                            text=c.text,
                            coding_user_selected=c.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.type is not None:
                await session.execute(
                    delete(HealthcareServiceType).where(
                        HealthcareServiceType.healthcare_service_id == hs.id
                    )
                )
                for t in payload.type:
                    session.add(
                        HealthcareServiceType(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=t.coding_system,
                            coding_version=t.coding_version,
                            coding_code=t.coding_code,
                            coding_display=t.coding_display,
                            text=t.text,
                            coding_user_selected=t.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.specialty is not None:
                await session.execute(
                    delete(HealthcareServiceSpecialty).where(
                        HealthcareServiceSpecialty.healthcare_service_id == hs.id
                    )
                )
                for sp in payload.specialty:
                    session.add(
                        HealthcareServiceSpecialty(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=sp.coding_system,
                            coding_version=sp.coding_version,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                            coding_user_selected=sp.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.location is not None:
                await session.execute(
                    delete(HealthcareServiceLocation).where(
                        HealthcareServiceLocation.healthcare_service_id == hs.id
                    )
                )
                for loc in payload.location:
                    loc_type, loc_id = (
                        _parse_location_ref(loc.reference)
                        if loc.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, hs.org_id, loc_type, loc_id, "location"
                    )
                    session.add(
                        HealthcareServiceLocation(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            **_location_ref_kwargs(
                                "reference", loc.reference, loc.reference_display
                            ),
                            **_reference_kwargs("reference", loc),
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(HealthcareServiceTelecom).where(
                        HealthcareServiceTelecom.healthcare_service_id == hs.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        HealthcareServiceTelecom(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.coverage_area is not None:
                await session.execute(
                    delete(HealthcareServiceCoverageArea).where(
                        HealthcareServiceCoverageArea.healthcare_service_id == hs.id
                    )
                )
                for ca in payload.coverage_area:
                    ca_type, ca_id = (
                        _parse_coverage_area_ref(ca.reference)
                        if ca.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, hs.org_id, ca_type, ca_id, "coverageArea"
                    )
                    session.add(
                        HealthcareServiceCoverageArea(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            **_coverage_area_ref_kwargs(
                                "reference", ca.reference, ca.reference_display
                            ),
                            **_reference_kwargs("reference", ca),
                            created_by=updated_by,
                        )
                    )

            if payload.service_provision_code is not None:
                await session.execute(
                    delete(HealthcareServiceServiceProvisionCode).where(
                        HealthcareServiceServiceProvisionCode.healthcare_service_id
                        == hs.id
                    )
                )
                for spc in payload.service_provision_code:
                    session.add(
                        HealthcareServiceServiceProvisionCode(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=spc.coding_system,
                            coding_version=spc.coding_version,
                            coding_code=spc.coding_code,
                            coding_display=spc.coding_display,
                            text=spc.text,
                            coding_user_selected=spc.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.eligibility is not None:
                await session.execute(
                    delete(HealthcareServiceEligibility).where(
                        HealthcareServiceEligibility.healthcare_service_id == hs.id
                    )
                )
                for e in payload.eligibility:
                    session.add(
                        HealthcareServiceEligibility(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            code_system=e.code_system,
                            code_version=e.code_version,
                            code_code=e.code_code,
                            code_display=e.code_display,
                            code_text=e.code_text,
                            code_user_selected=e.code_user_selected,
                            comment=e.comment,
                            created_by=updated_by,
                        )
                    )

            if payload.program is not None:
                await session.execute(
                    delete(HealthcareServiceProgram).where(
                        HealthcareServiceProgram.healthcare_service_id == hs.id
                    )
                )
                for p in payload.program:
                    session.add(
                        HealthcareServiceProgram(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=p.coding_system,
                            coding_version=p.coding_version,
                            coding_code=p.coding_code,
                            coding_display=p.coding_display,
                            text=p.text,
                            coding_user_selected=p.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.characteristic is not None:
                await session.execute(
                    delete(HealthcareServiceCharacteristic).where(
                        HealthcareServiceCharacteristic.healthcare_service_id == hs.id
                    )
                )
                for c in payload.characteristic:
                    session.add(
                        HealthcareServiceCharacteristic(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=c.coding_system,
                            coding_version=c.coding_version,
                            coding_code=c.coding_code,
                            coding_display=c.coding_display,
                            text=c.text,
                            coding_user_selected=c.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.communication is not None:
                await session.execute(
                    delete(HealthcareServiceCommunication).where(
                        HealthcareServiceCommunication.healthcare_service_id == hs.id
                    )
                )
                for cm in payload.communication:
                    session.add(
                        HealthcareServiceCommunication(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=cm.coding_system,
                            coding_version=cm.coding_version,
                            coding_code=cm.coding_code,
                            coding_display=cm.coding_display,
                            text=cm.text,
                            coding_user_selected=cm.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.referral_method is not None:
                await session.execute(
                    delete(HealthcareServiceReferralMethod).where(
                        HealthcareServiceReferralMethod.healthcare_service_id == hs.id
                    )
                )
                for rm in payload.referral_method:
                    session.add(
                        HealthcareServiceReferralMethod(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            coding_system=rm.coding_system,
                            coding_version=rm.coding_version,
                            coding_code=rm.coding_code,
                            coding_display=rm.coding_display,
                            text=rm.text,
                            coding_user_selected=rm.coding_user_selected,
                            created_by=updated_by,
                        )
                    )

            if payload.available_time is not None:
                await session.execute(
                    delete(HealthcareServiceAvailableTime).where(
                        HealthcareServiceAvailableTime.healthcare_service_id == hs.id
                    )
                )
                for at in payload.available_time:
                    session.add(
                        HealthcareServiceAvailableTime(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            days_of_week=_days_of_week(at.days_of_week),
                            all_day=at.all_day,
                            available_start_time=at.available_start_time,
                            available_end_time=at.available_end_time,
                            created_by=updated_by,
                        )
                    )

            if payload.not_available is not None:
                await session.execute(
                    delete(HealthcareServiceNotAvailable).where(
                        HealthcareServiceNotAvailable.healthcare_service_id == hs.id
                    )
                )
                for na in payload.not_available:
                    session.add(
                        HealthcareServiceNotAvailable(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            description=na.description,
                            during_start=na.during_start,
                            during_end=na.during_end,
                            created_by=updated_by,
                        )
                    )

            if payload.endpoint is not None:
                await session.execute(
                    delete(HealthcareServiceEndpoint).where(
                        HealthcareServiceEndpoint.healthcare_service_id == hs.id
                    )
                )
                for e in payload.endpoint:
                    ep_type, ep_id = (
                        _parse_endpoint_ref(e.reference)
                        if e.reference
                        else (None, None)
                    )
                    session.add(
                        HealthcareServiceEndpoint(
                            healthcare_service_id=hs.id,
                            org_id=hs.org_id,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_display=e.reference_display,
                            **_reference_kwargs("reference", e),
                            created_by=updated_by,
                        )
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "HealthcareService sub-resource lists replaced",
                    extra={
                        "event": "healthcare_service.sublists_replaced",
                        "healthcare_service_id": healthcare_service_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_healthcare_service_id(healthcare_service_id)

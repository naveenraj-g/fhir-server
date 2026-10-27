from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.healthcare_service import (
    HealthcareServiceAvailableTime,
    HealthcareServiceCategory,
    HealthcareServiceCategoryCoding,
    HealthcareServiceCharacteristic,
    HealthcareServiceCharacteristicCoding,
    HealthcareServiceCommunication,
    HealthcareServiceCommunicationCoding,
    HealthcareServiceCoverageArea,
    HealthcareServiceEligibility,
    HealthcareServiceEligibilityCodeCoding,
    HealthcareServiceEndpoint,
    HealthcareServiceIdentifier,
    HealthcareServiceIdentifierTypeCoding,
    HealthcareServiceLocation,
    HealthcareServiceModel,
    HealthcareServiceNotAvailable,
    HealthcareServiceProgram,
    HealthcareServiceProgramCoding,
    HealthcareServiceReferralMethod,
    HealthcareServiceReferralMethodCoding,
    HealthcareServiceServiceProvisionCode,
    HealthcareServiceServiceProvisionCodeCoding,
    HealthcareServiceSpecialty,
    HealthcareServiceSpecialtyCoding,
    HealthcareServiceTelecom,
    HealthcareServiceType,
    HealthcareServiceTypeCoding,
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

# Sub-resource list fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is untouched.
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


def _days_of_week(days) -> list[str] | None:
    """availableTime.daysOfWeek[] is a real Postgres ARRAY(String) column."""
    return [d.value for d in days] if days else None


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput entry,
    targeting any of the ten dedicated coding[] child tables — all share
    the same shape via FhirCodingMixin, so one helper covers all of them.
    Mirrors app.repository.organization.full._coding_kwargs."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


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
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                active=payload.active,
                name=payload.name,
                provided_by_reference=payload.provided_by,
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
                    identifier = HealthcareServiceIdentifier(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs(
                            "assigner", i.assigner, i.assigner_display
                        ),
                        **_reference_kwargs("assigner", i),
                        created_by=created_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                HealthcareServiceIdentifierTypeCoding(
                                    healthcare_service_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.category:
                for c in payload.category:
                    category = HealthcareServiceCategory(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=c.text,
                        created_by=created_by,
                    )
                    session.add(category)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                HealthcareServiceCategoryCoding(
                                    healthcare_service_category_id=category.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.type:
                for t in payload.type:
                    hs_type = HealthcareServiceType(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=t.text,
                        created_by=created_by,
                    )
                    session.add(hs_type)
                    if t.coding:
                        await session.flush()
                        for coding in t.coding:
                            session.add(
                                HealthcareServiceTypeCoding(
                                    healthcare_service_type_id=hs_type.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.specialty:
                for sp in payload.specialty:
                    specialty = HealthcareServiceSpecialty(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=sp.text,
                        created_by=created_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                HealthcareServiceSpecialtyCoding(
                                    healthcare_service_specialty_id=specialty.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
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
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
                            reference_reference=loc.reference,
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
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
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
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
                            reference_reference=ca.reference,
                            **_coverage_area_ref_kwargs(
                                "reference", ca.reference, ca.reference_display
                            ),
                            **_reference_kwargs("reference", ca),
                            created_by=created_by,
                        )
                    )

            if payload.service_provision_code:
                for spc in payload.service_provision_code:
                    service_provision_code = HealthcareServiceServiceProvisionCode(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=spc.text,
                        created_by=created_by,
                    )
                    session.add(service_provision_code)
                    if spc.coding:
                        await session.flush()
                        for coding in spc.coding:
                            session.add(
                                HealthcareServiceServiceProvisionCodeCoding(
                                    healthcare_service_service_provision_code_id=service_provision_code.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.eligibility:
                for e in payload.eligibility:
                    eligibility = HealthcareServiceEligibility(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        code_text=e.code_text,
                        comment=e.comment,
                        created_by=created_by,
                    )
                    session.add(eligibility)
                    if e.code_coding:
                        await session.flush()
                        for coding in e.code_coding:
                            session.add(
                                HealthcareServiceEligibilityCodeCoding(
                                    healthcare_service_eligibility_id=eligibility.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.program:
                for p in payload.program:
                    program = HealthcareServiceProgram(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=p.text,
                        created_by=created_by,
                    )
                    session.add(program)
                    if p.coding:
                        await session.flush()
                        for coding in p.coding:
                            session.add(
                                HealthcareServiceProgramCoding(
                                    healthcare_service_program_id=program.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.characteristic:
                for c in payload.characteristic:
                    characteristic = HealthcareServiceCharacteristic(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=c.text,
                        created_by=created_by,
                    )
                    session.add(characteristic)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                HealthcareServiceCharacteristicCoding(
                                    healthcare_service_characteristic_id=characteristic.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.communication:
                for cm in payload.communication:
                    communication = HealthcareServiceCommunication(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=cm.text,
                        created_by=created_by,
                    )
                    session.add(communication)
                    if cm.coding:
                        await session.flush()
                        for coding in cm.coding:
                            session.add(
                                HealthcareServiceCommunicationCoding(
                                    healthcare_service_communication_id=communication.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.referral_method:
                for rm in payload.referral_method:
                    referral_method = HealthcareServiceReferralMethod(
                        healthcare_service_pk=hs.id,
                        tenant_id=org_id,
                        text=rm.text,
                        created_by=created_by,
                    )
                    session.add(referral_method)
                    if rm.coding:
                        await session.flush()
                        for coding in rm.coding:
                            session.add(
                                HealthcareServiceReferralMethodCoding(
                                    healthcare_service_referral_method_id=referral_method.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.available_time:
                for at in payload.available_time:
                    session.add(
                        HealthcareServiceAvailableTime(
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
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
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
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
                            healthcare_service_pk=hs.id,
                            tenant_id=org_id,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_reference=e.reference,
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

            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                if field == "provided_by":
                    hs.provided_by_reference = value
                    if value is not None:
                        pb_type, pb_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, hs.tenant_id, pb_type, pb_id, "providedBy"
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
                        HealthcareServiceIdentifier.healthcare_service_pk == hs.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, hs.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = HealthcareServiceIdentifier(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs(
                            "assigner", i.assigner, i.assigner_display
                        ),
                        **_reference_kwargs("assigner", i),
                        created_by=updated_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                HealthcareServiceIdentifierTypeCoding(
                                    healthcare_service_identifier_id=identifier.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.category is not None:
                await session.execute(
                    delete(HealthcareServiceCategory).where(
                        HealthcareServiceCategory.healthcare_service_pk == hs.id
                    )
                )
                for c in payload.category:
                    category = HealthcareServiceCategory(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=c.text,
                        created_by=updated_by,
                    )
                    session.add(category)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                HealthcareServiceCategoryCoding(
                                    healthcare_service_category_id=category.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.type is not None:
                await session.execute(
                    delete(HealthcareServiceType).where(
                        HealthcareServiceType.healthcare_service_pk == hs.id
                    )
                )
                for t in payload.type:
                    hs_type = HealthcareServiceType(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=t.text,
                        created_by=updated_by,
                    )
                    session.add(hs_type)
                    if t.coding:
                        await session.flush()
                        for coding in t.coding:
                            session.add(
                                HealthcareServiceTypeCoding(
                                    healthcare_service_type_id=hs_type.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.specialty is not None:
                await session.execute(
                    delete(HealthcareServiceSpecialty).where(
                        HealthcareServiceSpecialty.healthcare_service_pk == hs.id
                    )
                )
                for sp in payload.specialty:
                    specialty = HealthcareServiceSpecialty(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=sp.text,
                        created_by=updated_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                HealthcareServiceSpecialtyCoding(
                                    healthcare_service_specialty_id=specialty.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.location is not None:
                await session.execute(
                    delete(HealthcareServiceLocation).where(
                        HealthcareServiceLocation.healthcare_service_pk == hs.id
                    )
                )
                for loc in payload.location:
                    loc_type, loc_id = (
                        _parse_location_ref(loc.reference)
                        if loc.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, hs.tenant_id, loc_type, loc_id, "location"
                    )
                    session.add(
                        HealthcareServiceLocation(
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
                            reference_reference=loc.reference,
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
                        HealthcareServiceTelecom.healthcare_service_pk == hs.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        HealthcareServiceTelecom(
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
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
                        HealthcareServiceCoverageArea.healthcare_service_pk == hs.id
                    )
                )
                for ca in payload.coverage_area:
                    ca_type, ca_id = (
                        _parse_coverage_area_ref(ca.reference)
                        if ca.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, hs.tenant_id, ca_type, ca_id, "coverageArea"
                    )
                    session.add(
                        HealthcareServiceCoverageArea(
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
                            reference_reference=ca.reference,
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
                        HealthcareServiceServiceProvisionCode.healthcare_service_pk
                        == hs.id
                    )
                )
                for spc in payload.service_provision_code:
                    service_provision_code = HealthcareServiceServiceProvisionCode(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=spc.text,
                        created_by=updated_by,
                    )
                    session.add(service_provision_code)
                    if spc.coding:
                        await session.flush()
                        for coding in spc.coding:
                            session.add(
                                HealthcareServiceServiceProvisionCodeCoding(
                                    healthcare_service_service_provision_code_id=service_provision_code.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.eligibility is not None:
                await session.execute(
                    delete(HealthcareServiceEligibility).where(
                        HealthcareServiceEligibility.healthcare_service_pk == hs.id
                    )
                )
                for e in payload.eligibility:
                    eligibility = HealthcareServiceEligibility(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        code_text=e.code_text,
                        comment=e.comment,
                        created_by=updated_by,
                    )
                    session.add(eligibility)
                    if e.code_coding:
                        await session.flush()
                        for coding in e.code_coding:
                            session.add(
                                HealthcareServiceEligibilityCodeCoding(
                                    healthcare_service_eligibility_id=eligibility.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.program is not None:
                await session.execute(
                    delete(HealthcareServiceProgram).where(
                        HealthcareServiceProgram.healthcare_service_pk == hs.id
                    )
                )
                for p in payload.program:
                    program = HealthcareServiceProgram(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=p.text,
                        created_by=updated_by,
                    )
                    session.add(program)
                    if p.coding:
                        await session.flush()
                        for coding in p.coding:
                            session.add(
                                HealthcareServiceProgramCoding(
                                    healthcare_service_program_id=program.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.characteristic is not None:
                await session.execute(
                    delete(HealthcareServiceCharacteristic).where(
                        HealthcareServiceCharacteristic.healthcare_service_pk == hs.id
                    )
                )
                for c in payload.characteristic:
                    characteristic = HealthcareServiceCharacteristic(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=c.text,
                        created_by=updated_by,
                    )
                    session.add(characteristic)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                HealthcareServiceCharacteristicCoding(
                                    healthcare_service_characteristic_id=characteristic.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.communication is not None:
                await session.execute(
                    delete(HealthcareServiceCommunication).where(
                        HealthcareServiceCommunication.healthcare_service_pk == hs.id
                    )
                )
                for cm in payload.communication:
                    communication = HealthcareServiceCommunication(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=cm.text,
                        created_by=updated_by,
                    )
                    session.add(communication)
                    if cm.coding:
                        await session.flush()
                        for coding in cm.coding:
                            session.add(
                                HealthcareServiceCommunicationCoding(
                                    healthcare_service_communication_id=communication.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.referral_method is not None:
                await session.execute(
                    delete(HealthcareServiceReferralMethod).where(
                        HealthcareServiceReferralMethod.healthcare_service_pk == hs.id
                    )
                )
                for rm in payload.referral_method:
                    referral_method = HealthcareServiceReferralMethod(
                        healthcare_service_pk=hs.id,
                        tenant_id=hs.tenant_id,
                        text=rm.text,
                        created_by=updated_by,
                    )
                    session.add(referral_method)
                    if rm.coding:
                        await session.flush()
                        for coding in rm.coding:
                            session.add(
                                HealthcareServiceReferralMethodCoding(
                                    healthcare_service_referral_method_id=referral_method.id,
                                    tenant_id=hs.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.available_time is not None:
                await session.execute(
                    delete(HealthcareServiceAvailableTime).where(
                        HealthcareServiceAvailableTime.healthcare_service_pk == hs.id
                    )
                )
                for at in payload.available_time:
                    session.add(
                        HealthcareServiceAvailableTime(
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
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
                        HealthcareServiceNotAvailable.healthcare_service_pk == hs.id
                    )
                )
                for na in payload.not_available:
                    session.add(
                        HealthcareServiceNotAvailable(
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
                            description=na.description,
                            during_start=na.during_start,
                            during_end=na.during_end,
                            created_by=updated_by,
                        )
                    )

            if payload.endpoint is not None:
                await session.execute(
                    delete(HealthcareServiceEndpoint).where(
                        HealthcareServiceEndpoint.healthcare_service_pk == hs.id
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
                            healthcare_service_pk=hs.id,
                            tenant_id=hs.tenant_id,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_reference=e.reference,
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

from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.practitioner_role import (
    PractitionerRoleAvailableTime,
    PractitionerRoleCode,
    PractitionerRoleCodeCoding,
    PractitionerRoleEndpoint,
    PractitionerRoleHealthcareService,
    PractitionerRoleIdentifier,
    PractitionerRoleIdentifierTypeCoding,
    PractitionerRoleLocation,
    PractitionerRoleModel,
    PractitionerRoleNotAvailable,
    PractitionerRoleSpecialty,
    PractitionerRoleSpecialtyCoding,
    PractitionerRoleTelecom,
)
from app.schemas.practitioner_role import (
    PractitionerRoleCreateSchema,
    PractitionerRolePatchSchema,
)

from ._shared import (
    _healthcare_service_ref_kwargs,
    _location_ref_kwargs,
    _org_ref_kwargs,
    _parse_endpoint_ref,
    _parse_healthcare_service_ref,
    _parse_location_ref,
    _parse_org_ref,
    _parse_practitioner_ref,
    _practitioner_ref_kwargs,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource list fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is untouched.
_SUB = {
    "identifier",
    "code",
    "specialty",
    "location",
    "healthcare_service",
    "telecom",
    "available_time",
    "not_available",
    "endpoint",
}


def _days_of_week(days) -> str | None:
    return ",".join(d.value for d in days) if days else None


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput entry,
    targeting either of the two dedicated coding[] child tables — both share
    the same shape via FhirCodingMixin. Mirrors
    app.repository.healthcare_service.full._coding_kwargs."""
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
    that touch all 9 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: PractitionerRoleCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> PractitionerRoleModel:
        """Create a PractitionerRole plus any combination of its 9
        sub-resource lists, atomically in one DB transaction. Every list on
        the payload is optional; only the ones supplied get inserted."""
        p_type, p_id = (
            _parse_practitioner_ref(payload.practitioner)
            if payload.practitioner
            else (None, None)
        )
        o_type, o_id = (
            _parse_org_ref(payload.organization) if payload.organization else (None, None)
        )
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, p_type, p_id, "practitioner")
            await _validate_reference(session, org_id, o_type, o_id, "organization")
            pr = PractitionerRoleModel(
                tenant_id=org_id,
                created_by=created_by,
                active=payload.active,
                period_start=payload.period_start,
                period_end=payload.period_end,
                **_practitioner_ref_kwargs(
                    "practitioner", payload.practitioner, payload.practitioner_display
                ),
                **_reference_kwargs("practitioner", payload),
                **_org_ref_kwargs(
                    "organization", payload.organization, payload.organization_display
                ),
                **_reference_kwargs("organization", payload),
                availability_exceptions=payload.availability_exceptions,
            )
            session.add(pr)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = PractitionerRoleIdentifier(
                        practitioner_role_pk=pr.id,
                        tenant_id=org_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=created_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                PractitionerRoleIdentifierTypeCoding(
                                    practitioner_role_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.code:
                for c in payload.code:
                    code = PractitionerRoleCode(
                        practitioner_role_pk=pr.id,
                        tenant_id=org_id,
                        text=c.text,
                        created_by=created_by,
                    )
                    session.add(code)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                PractitionerRoleCodeCoding(
                                    practitioner_role_code_id=code.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.specialty:
                for sp in payload.specialty:
                    specialty = PractitionerRoleSpecialty(
                        practitioner_role_pk=pr.id,
                        tenant_id=org_id,
                        text=sp.text,
                        created_by=created_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                PractitionerRoleSpecialtyCoding(
                                    practitioner_role_specialty_id=specialty.id,
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
                        PractitionerRoleLocation(
                            practitioner_role_pk=pr.id,
                            tenant_id=org_id,
                            **_location_ref_kwargs(
                                "reference", loc.reference, loc.reference_display
                            ),
                            **_reference_kwargs("reference", loc),
                            created_by=created_by,
                        )
                    )

            if payload.healthcare_service:
                for hs in payload.healthcare_service:
                    hs_type, hs_id = (
                        _parse_healthcare_service_ref(hs.reference)
                        if hs.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, hs_type, hs_id, "healthcareService"
                    )
                    session.add(
                        PractitionerRoleHealthcareService(
                            practitioner_role_pk=pr.id,
                            tenant_id=org_id,
                            **_healthcare_service_ref_kwargs(
                                "reference", hs.reference, hs.reference_display
                            ),
                            **_reference_kwargs("reference", hs),
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
                    session.add(
                        PractitionerRoleTelecom(
                            practitioner_role_pk=pr.id,
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

            if payload.available_time:
                for at in payload.available_time:
                    session.add(
                        PractitionerRoleAvailableTime(
                            practitioner_role_pk=pr.id,
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
                        PractitionerRoleNotAvailable(
                            practitioner_role_pk=pr.id,
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
                        PractitionerRoleEndpoint(
                            practitioner_role_pk=pr.id,
                            tenant_id=org_id,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_display=e.reference_display,
                            **_reference_kwargs("reference", e),
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
                await session.refresh(pr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_role_id(pr.practitioner_role_id)

    async def patch_full(
        self,
        practitioner_role_id: int,
        payload: PractitionerRolePatchSchema,
        updated_by: str | None = None,
    ) -> PractitionerRoleModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(PractitionerRoleModel).where(
                PractitionerRoleModel.practitioner_role_id == practitioner_role_id
            )
            pr = (await session.execute(stmt)).scalars().first()
            if not pr:
                return None

            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                if field == "practitioner":
                    if value is not None:
                        p_type, p_id = _parse_practitioner_ref(value)
                        await _validate_reference(
                            session, pr.tenant_id, p_type, p_id, "practitioner"
                        )
                        pr.practitioner_type = p_type
                        pr.practitioner_id = p_id
                    else:
                        pr.practitioner_type = None
                        pr.practitioner_id = None
                elif field == "organization":
                    if value is not None:
                        o_type, o_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, pr.tenant_id, o_type, o_id, "organization"
                        )
                        pr.organization_type = o_type
                        pr.organization_id = o_id
                    else:
                        pr.organization_type = None
                        pr.organization_id = None
                else:
                    setattr(pr, field, value)
            if updated_by is not None:
                pr.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(PractitionerRoleIdentifier).where(
                        PractitionerRoleIdentifier.practitioner_role_pk == pr.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, pr.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = PractitionerRoleIdentifier(
                        practitioner_role_pk=pr.id,
                        tenant_id=pr.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=updated_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                PractitionerRoleIdentifierTypeCoding(
                                    practitioner_role_identifier_id=identifier.id,
                                    tenant_id=pr.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.code is not None:
                await session.execute(
                    delete(PractitionerRoleCode).where(
                        PractitionerRoleCode.practitioner_role_pk == pr.id
                    )
                )
                for c in payload.code:
                    code = PractitionerRoleCode(
                        practitioner_role_pk=pr.id,
                        tenant_id=pr.tenant_id,
                        text=c.text,
                        created_by=updated_by,
                    )
                    session.add(code)
                    if c.coding:
                        await session.flush()
                        for coding in c.coding:
                            session.add(
                                PractitionerRoleCodeCoding(
                                    practitioner_role_code_id=code.id,
                                    tenant_id=pr.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.specialty is not None:
                await session.execute(
                    delete(PractitionerRoleSpecialty).where(
                        PractitionerRoleSpecialty.practitioner_role_pk == pr.id
                    )
                )
                for sp in payload.specialty:
                    specialty = PractitionerRoleSpecialty(
                        practitioner_role_pk=pr.id,
                        tenant_id=pr.tenant_id,
                        text=sp.text,
                        created_by=updated_by,
                    )
                    session.add(specialty)
                    if sp.coding:
                        await session.flush()
                        for coding in sp.coding:
                            session.add(
                                PractitionerRoleSpecialtyCoding(
                                    practitioner_role_specialty_id=specialty.id,
                                    tenant_id=pr.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.location is not None:
                await session.execute(
                    delete(PractitionerRoleLocation).where(
                        PractitionerRoleLocation.practitioner_role_pk == pr.id
                    )
                )
                for loc in payload.location:
                    loc_type, loc_id = (
                        _parse_location_ref(loc.reference)
                        if loc.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, pr.tenant_id, loc_type, loc_id, "location"
                    )
                    session.add(
                        PractitionerRoleLocation(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
                            **_location_ref_kwargs(
                                "reference", loc.reference, loc.reference_display
                            ),
                            **_reference_kwargs("reference", loc),
                            created_by=updated_by,
                        )
                    )

            if payload.healthcare_service is not None:
                await session.execute(
                    delete(PractitionerRoleHealthcareService).where(
                        PractitionerRoleHealthcareService.practitioner_role_pk == pr.id
                    )
                )
                for hs in payload.healthcare_service:
                    hs_type, hs_id = (
                        _parse_healthcare_service_ref(hs.reference)
                        if hs.reference
                        else (None, None)
                    )
                    await _validate_reference(
                        session, pr.tenant_id, hs_type, hs_id, "healthcareService"
                    )
                    session.add(
                        PractitionerRoleHealthcareService(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
                            **_healthcare_service_ref_kwargs(
                                "reference", hs.reference, hs.reference_display
                            ),
                            **_reference_kwargs("reference", hs),
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(PractitionerRoleTelecom).where(
                        PractitionerRoleTelecom.practitioner_role_pk == pr.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        PractitionerRoleTelecom(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.available_time is not None:
                await session.execute(
                    delete(PractitionerRoleAvailableTime).where(
                        PractitionerRoleAvailableTime.practitioner_role_pk == pr.id
                    )
                )
                for at in payload.available_time:
                    session.add(
                        PractitionerRoleAvailableTime(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
                            days_of_week=_days_of_week(at.days_of_week),
                            all_day=at.all_day,
                            available_start_time=at.available_start_time,
                            available_end_time=at.available_end_time,
                            created_by=updated_by,
                        )
                    )

            if payload.not_available is not None:
                await session.execute(
                    delete(PractitionerRoleNotAvailable).where(
                        PractitionerRoleNotAvailable.practitioner_role_pk == pr.id
                    )
                )
                for na in payload.not_available:
                    session.add(
                        PractitionerRoleNotAvailable(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
                            description=na.description,
                            during_start=na.during_start,
                            during_end=na.during_end,
                            created_by=updated_by,
                        )
                    )

            if payload.endpoint is not None:
                await session.execute(
                    delete(PractitionerRoleEndpoint).where(
                        PractitionerRoleEndpoint.practitioner_role_pk == pr.id
                    )
                )
                for e in payload.endpoint:
                    ep_type, ep_id = (
                        _parse_endpoint_ref(e.reference)
                        if e.reference
                        else (None, None)
                    )
                    session.add(
                        PractitionerRoleEndpoint(
                            practitioner_role_pk=pr.id,
                            tenant_id=pr.tenant_id,
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
                    "PractitionerRole sub-resource lists replaced",
                    extra={
                        "event": "practitioner_role.sublists_replaced",
                        "practitioner_role_id": practitioner_role_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_practitioner_role_id(practitioner_role_id)

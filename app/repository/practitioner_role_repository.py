from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.enums import OrganizationReferenceType
from app.models.healthcare_service.healthcare_service import (
    HealthcareServiceModel,
    HealthcareServiceCategory,
)
from app.models.location import LocationModel, LocationTelecom
from app.models.organization import OrganizationModel
from app.models.practitioner import (
    PractitionerModel,
    PractitionerName,
    PractitionerQualification,
    PractitionerTelecom,
    PractitionerPhoto,
)
from app.models.practitioner_role.enums import (
    PractitionerRoleEndpointReferenceType,
    PractitionerRoleHealthcareServiceReferenceType,
    PractitionerRoleLocationReferenceType,
)
from app.models.practitioner_role.practitioner_role import (
    PractitionerRoleAvailabilityTime,
    PractitionerRoleCode,
    PractitionerRoleEndpoint,
    PractitionerRoleHealthcareService,
    PractitionerRoleIdentifier,
    PractitionerRoleLocation,
    PractitionerRoleModel,
    PractitionerRoleNotAvailableTime,
    PractitionerRoleSpecialty,
    PractitionerRoleTelecom,
)
from app.schemas.practitioner_role import (
    PractitionerRoleCreateSchema,
    PractitionerRolePatchSchema,
)


def _with_relationships(stmt):
    return stmt.options(
        selectinload(PractitionerRoleModel.identifiers),
        selectinload(PractitionerRoleModel.codes),
        selectinload(PractitionerRoleModel.specialties),
        selectinload(PractitionerRoleModel.locations).selectinload(PractitionerRoleLocation.reference),
        selectinload(PractitionerRoleModel.healthcare_services).selectinload(PractitionerRoleHealthcareService.reference),
        selectinload(PractitionerRoleModel.telecoms),
        selectinload(PractitionerRoleModel.available_times),
        selectinload(PractitionerRoleModel.not_available_times),
        selectinload(PractitionerRoleModel.endpoints),
        selectinload(PractitionerRoleModel.organization),
    )


def _with_booking_relationships(stmt):
    """Extends _with_relationships to also eager-load all linked Practitioner sub-resources."""
    return stmt.options(
        selectinload(PractitionerRoleModel.identifiers),
        selectinload(PractitionerRoleModel.codes),
        selectinload(PractitionerRoleModel.specialties),
        selectinload(PractitionerRoleModel.locations),
        selectinload(PractitionerRoleModel.healthcare_services),
        selectinload(PractitionerRoleModel.telecoms),
        selectinload(PractitionerRoleModel.available_times),
        selectinload(PractitionerRoleModel.not_available_times),
        selectinload(PractitionerRoleModel.endpoints),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.names),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.identifiers),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.telecoms),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.addresses),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.photos),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.qualifications).selectinload(PractitionerQualification.identifiers),
        selectinload(PractitionerRoleModel.practitioner).selectinload(PractitionerModel.communications),
    )


def _parse_ref(ref: str, enum_cls, field: str):
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )
    try:
        ref_type = enum_cls(parts[0])
    except ValueError:
        allowed = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference type '{parts[0]}' for {field}. Allowed: {allowed}.",
        )
    return ref_type, ref_id


async def _resolve_organization_pk(session: AsyncSession, ref: str):
    """Resolve 'Organization/<public_id>' to the internal organization.id PK."""
    ref_type, public_id = _parse_ref(ref, OrganizationReferenceType, "organization")
    result = await session.execute(
        select(OrganizationModel.id).where(OrganizationModel.organization_id == public_id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Organization/{public_id} not found.",
        )
    return ref_type, pk


async def _resolve_location_pk(session: AsyncSession, ref: str):
    """Resolve 'Location/<public_id>' to the internal location.id PK."""
    ref_type, public_id = _parse_ref(ref, PractitionerRoleLocationReferenceType, "location")
    result = await session.execute(
        select(LocationModel.id).where(LocationModel.location_id == public_id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Location/{public_id} not found.",
        )
    return ref_type, pk


async def _resolve_healthcare_service_pk(session: AsyncSession, ref: str):
    """Resolve 'HealthcareService/<public_id>' to the internal healthcare_service.id PK."""
    ref_type, public_id = _parse_ref(ref, PractitionerRoleHealthcareServiceReferenceType, "healthcareService")
    result = await session.execute(
        select(HealthcareServiceModel.id).where(HealthcareServiceModel.healthcare_service_id == public_id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"HealthcareService/{public_id} not found.",
        )
    return ref_type, pk


class PractitionerRoleRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_practitioner_role_id(
        self, practitioner_role_id: int
    ) -> Optional[PractitionerRoleModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerRoleModel).where(
                    PractitionerRoleModel.practitioner_role_id == practitioner_role_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, active, practitioner_id):
        if user_id:
            stmt = stmt.where(PractitionerRoleModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PractitionerRoleModel.org_id == org_id)
        if active is not None:
            stmt = stmt.where(PractitionerRoleModel.active == active)
        if practitioner_id is not None:
            sub = (
                select(PractitionerModel.id)
                .where(PractitionerModel.practitioner_id == practitioner_id)
                .scalar_subquery()
            )
            stmt = stmt.where(PractitionerRoleModel.practitioner_id == sub)
        return stmt

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        active: Optional[bool] = None,
        practitioner_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerRoleModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerRoleModel)),
                user_id, org_id, active, practitioner_id,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerRoleModel),
                user_id, org_id, active, practitioner_id,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(PractitionerRoleModel.practitioner_role_id.desc())
                    .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        active: Optional[bool] = None,
        practitioner_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerRoleModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerRoleModel)),
                user_id, org_id, active, practitioner_id,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerRoleModel),
                user_id, org_id, active, practitioner_id,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(PractitionerRoleModel.practitioner_role_id.desc())
                    .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def list_for_booking(
        self,
        org_id: Optional[str] = None,
        active: Optional[bool] = True,
        specialty_code: Optional[str] = None,
        day_of_week: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerRoleModel], int]:
        async with self.session_factory() as session:
            base = _with_booking_relationships(select(PractitionerRoleModel))
            count_base = select(func.count()).select_from(PractitionerRoleModel)

            if org_id:
                base = base.where(PractitionerRoleModel.org_id == org_id)
                count_base = count_base.where(PractitionerRoleModel.org_id == org_id)
            if active is not None:
                base = base.where(PractitionerRoleModel.active == active)
                count_base = count_base.where(PractitionerRoleModel.active == active)
            if specialty_code:
                sp_sub = (
                    select(PractitionerRoleSpecialty.practitioner_role_id)
                    .where(PractitionerRoleSpecialty.coding_code == specialty_code)
                    .scalar_subquery()
                )
                base = base.where(PractitionerRoleModel.id.in_(sp_sub))
                count_base = count_base.where(PractitionerRoleModel.id.in_(sp_sub))
            if day_of_week:
                avt_sub = (
                    select(PractitionerRoleAvailabilityTime.practitioner_role_id)
                    .where(or_(
                        PractitionerRoleAvailabilityTime.days_of_week.any(day_of_week),
                        PractitionerRoleAvailabilityTime.all_day == True,  # noqa: E712
                    ))
                    .scalar_subquery()
                )
                base = base.where(PractitionerRoleModel.id.in_(avt_sub))
                count_base = count_base.where(PractitionerRoleModel.id.in_(avt_sub))

            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(PractitionerRoleModel.practitioner_role_id)
                    .offset(offset).limit(limit)
            )).scalars().all())

            # Batch-load Location and HealthcareService details for booking enrichment
            loc_pub_ids = {
                loc.reference_id for pr in rows for loc in pr.locations if loc.reference_id
            }
            hs_pub_ids = {
                hs.reference_id for pr in rows for hs in pr.healthcare_services if hs.reference_id
            }

            # loc_pub_ids/hs_pub_ids are now internal PKs (reference_id resolves to the
            # target row's PK, not its public sequence id) — match on .id, but keep the
            # lookup dicts keyed by public id so downstream consumers (which read the
            # mapper-produced public reference_id) don't need to change.
            loc_lookup: dict = {}
            if loc_pub_ids:
                loc_rows = (await session.execute(
                    select(LocationModel)
                    .options(selectinload(LocationModel.telecoms))
                    .where(LocationModel.id.in_(loc_pub_ids))
                )).scalars().all()
                loc_lookup = {lm.location_id: lm for lm in loc_rows}

            hs_lookup: dict = {}
            if hs_pub_ids:
                hs_rows = (await session.execute(
                    select(HealthcareServiceModel)
                    .options(selectinload(HealthcareServiceModel.categories))
                    .where(HealthcareServiceModel.id.in_(hs_pub_ids))
                )).scalars().all()
                hs_lookup = {hm.healthcare_service_id: hm for hm in hs_rows}

        return rows, total, loc_lookup, hs_lookup

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: PractitionerRoleCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> PractitionerRoleModel:
        async with self.session_factory() as session:
            # Resolve practitioner reference to its internal PK
            prac_pk = None
            if payload.practitioner:
                parts = payload.practitioner.split("/", 1)
                if len(parts) != 2 or parts[0] != "Practitioner":
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid practitioner reference: '{payload.practitioner}'. Expected 'Practitioner/<id>'.",
                    )
                try:
                    prac_ref_id = int(parts[1])
                except ValueError:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid practitioner id in: '{payload.practitioner}'.",
                    )
                prac_row = (await session.execute(
                    select(PractitionerModel).where(PractitionerModel.practitioner_id == prac_ref_id)
                )).scalars().first()
                if not prac_row:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Practitioner '{payload.practitioner}' not found.",
                    )
                prac_pk = prac_row.id

            org_type = None
            org_id_val = None
            if payload.organization:
                org_type, org_id_val = await _resolve_organization_pk(session, payload.organization)

            pr = PractitionerRoleModel(
                user_id=user_id,
                org_id=org_id,
                created_by=created_by,
                active=payload.active,
                period_start=payload.period_start,
                period_end=payload.period_end,
                practitioner_id=prac_pk,
                practitioner_display=payload.practitioner_display,
                organization_type=org_type,
                organization_id=org_id_val,
                organization_display=payload.organization_display,
                availability_exceptions=payload.availability_exceptions,
            )
            session.add(pr)

            for item in (payload.identifier or []):
                session.add(PractitionerRoleIdentifier(
                    practitioner_role=pr, org_id=org_id,
                    use=item.use,
                    type_system=item.type_system, type_code=item.type_code,
                    type_display=item.type_display, type_text=item.type_text,
                    system=item.system, value=item.value,
                    period_start=item.period_start, period_end=item.period_end,
                    assigner=item.assigner,
                ))

            for item in (payload.code or []):
                session.add(PractitionerRoleCode(
                    practitioner_role=pr, org_id=org_id,
                    coding_system=item.coding_system, coding_code=item.coding_code,
                    coding_display=item.coding_display, text=item.text,
                ))

            for item in (payload.specialty or []):
                session.add(PractitionerRoleSpecialty(
                    practitioner_role=pr, org_id=org_id,
                    coding_system=item.coding_system, coding_code=item.coding_code,
                    coding_display=item.coding_display, text=item.text,
                ))

            for item in (payload.location or []):
                ref_type, ref_id = await _resolve_location_pk(session, item.reference)
                session.add(PractitionerRoleLocation(
                    practitioner_role=pr, org_id=org_id,
                    reference_type=ref_type, reference_id=ref_id,
                    reference_display=item.reference_display,
                ))

            for item in (payload.healthcare_service or []):
                ref_type, ref_id = await _resolve_healthcare_service_pk(session, item.reference)
                session.add(PractitionerRoleHealthcareService(
                    practitioner_role=pr, org_id=org_id,
                    reference_type=ref_type, reference_id=ref_id,
                    reference_display=item.reference_display,
                ))

            for item in (payload.telecom or []):
                session.add(PractitionerRoleTelecom(
                    practitioner_role=pr, org_id=org_id,
                    system=item.system, value=item.value, use=item.use,
                    rank=item.rank,
                    period_start=item.period_start, period_end=item.period_end,
                ))

            for at_item in (payload.available_time or []):
                session.add(PractitionerRoleAvailabilityTime(
                    practitioner_role=pr, org_id=org_id,
                    days_of_week=at_item.days_of_week,
                    all_day=at_item.all_day,
                    available_start_time=at_item.available_start_time,
                    available_end_time=at_item.available_end_time,
                ))

            for nat_item in (payload.not_available or []):
                session.add(PractitionerRoleNotAvailableTime(
                    practitioner_role=pr, org_id=org_id,
                    description=nat_item.description,
                    during_start=nat_item.during_start,
                    during_end=nat_item.during_end,
                ))

            for item in (payload.endpoint or []):
                ref_type, ref_id = _parse_ref(
                    item.reference, PractitionerRoleEndpointReferenceType, "endpoint"
                )
                session.add(PractitionerRoleEndpoint(
                    practitioner_role=pr, org_id=org_id,
                    reference_type=ref_type, reference_id=ref_id,
                    reference_display=item.reference_display,
                ))

            await session.commit()
            await session.refresh(pr)

            stmt = _with_relationships(
                select(PractitionerRoleModel).where(PractitionerRoleModel.id == pr.id)
            )
            result = await session.execute(stmt)
            return result.scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self,
        practitioner_role_id: int,
        payload: PractitionerRolePatchSchema,
        updated_by: Optional[str],
    ) -> Optional[PractitionerRoleModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerRoleModel).where(
                    PractitionerRoleModel.practitioner_role_id == practitioner_role_id
                )
            )
            result = await session.execute(stmt)
            pr = result.scalars().first()
            if not pr:
                return None

            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(pr, field, value)
            pr.updated_by = updated_by

            await session.commit()
            await session.refresh(pr)

            stmt = _with_relationships(
                select(PractitionerRoleModel).where(PractitionerRoleModel.id == pr.id)
            )
            result = await session.execute(stmt)
            return result.scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, practitioner_role_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(PractitionerRoleModel).where(
                PractitionerRoleModel.practitioner_role_id == practitioner_role_id
            )
            result = await session.execute(stmt)
            pr = result.scalars().first()
            if pr:
                await session.delete(pr)
                await session.commit()

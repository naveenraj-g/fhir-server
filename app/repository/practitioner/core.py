from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.pagination import resolve_sort
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerName,
    PractitionerQualification,
    PractitionerTelecom,
)
from app.schemas.enums import ContactPointSystem
from app.schemas.practitioner import PractitionerCreateSchema, PractitionerPatchSchema

from ._shared import _SORTABLE_FIELDS, _with_relationships


class _CoreMixin:
    """Core CRUD for the Practitioner parent row (no sub-resources)."""

    async def get_by_practitioner_id(
        self, practitioner_id: int
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.practitioner_id == practitioner_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_practitioner_id_in_org(
        self, practitioner_id: int, org_id: str
    ) -> PractitionerModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the practitioner exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.practitioner_id == practitioner_id,
                    PractitionerModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def practitioner_belongs_to_org(
        self, practitioner_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the practitioner exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel.id).where(
                PractitionerModel.practitioner_id == practitioner_id,
                PractitionerModel.org_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_user_id(self, user_id: str) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(PractitionerModel.user_id == user_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.user_id == user_id,
                    PractitionerModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(
        self,
        stmt,
        user_id,
        org_id,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender=None,
        active: bool | None = None,
        identifier: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        qualification_code: str | None = None,
    ):
        if user_id:
            stmt = stmt.where(PractitionerModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PractitionerModel.org_id == org_id)
        if family:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_id == PractitionerModel.id,
                    PractitionerName.family.ilike(f"%{family}%"),
                ),
            )
        if given:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_id == PractitionerModel.id,
                    PractitionerName.given.ilike(f"%{given}%"),
                ),
            )
        if name:
            # FHIR "name" — a single term matched against any HumanName
            # sub-field (family, given, prefix, suffix, text), unlike
            # family/given above which each target one specific sub-field.
            pattern = f"%{name}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_id == PractitionerModel.id,
                    or_(
                        PractitionerName.family.ilike(pattern),
                        PractitionerName.given.ilike(pattern),
                        PractitionerName.prefix.ilike(pattern),
                        PractitionerName.suffix.ilike(pattern),
                        PractitionerName.text.ilike(pattern),
                    ),
                ),
            )
        stmt = apply_token_filter(stmt, PractitionerModel.gender, gender)
        stmt = apply_token_filter(stmt, PractitionerModel.active, active)
        if identifier:
            # Exact business-identifier match (NPI/license/etc.), not a
            # substring search — matches Patient's identifier filter semantics.
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerIdentifier.id).where(
                    PractitionerIdentifier.practitioner_id == PractitionerModel.id,
                    PractitionerIdentifier.value == identifier,
                ),
            )
        if communication:
            # Practitioner's FHIR R4 name for the language filter (Patient's
            # equivalent search parameter is literally named "language").
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerCommunication.id).where(
                    PractitionerCommunication.practitioner_id == PractitionerModel.id,
                    PractitionerCommunication.language_code == communication,
                ),
            )
        if address:
            # Composite string search across every Address sub-field, per the
            # FHIR "address" search parameter (as opposed to address-city
            # etc. below, which each target one specific sub-field).
            pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    or_(
                        PractitionerAddress.line.ilike(pattern),
                        PractitionerAddress.city.ilike(pattern),
                        PractitionerAddress.district.ilike(pattern),
                        PractitionerAddress.state.ilike(pattern),
                        PractitionerAddress.country.ilike(pattern),
                        PractitionerAddress.postal_code.ilike(pattern),
                        PractitionerAddress.text.ilike(pattern),
                    ),
                ),
            )
        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    PractitionerAddress.city.ilike(f"%{address_city}%"),
                ),
            )
        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    PractitionerAddress.state.ilike(f"%{address_state}%"),
                ),
            )
        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    PractitionerAddress.postal_code == address_postal_code,
                ),
            )
        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    PractitionerAddress.country.ilike(f"%{address_country}%"),
                ),
            )
        if address_use is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_id == PractitionerModel.id,
                    PractitionerAddress.use == address_use,
                ),
            )
        if telecom:
            # Any telecom system — unlike email/phone below, which are each
            # scoped to one specific system.
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_id == PractitionerModel.id,
                    PractitionerTelecom.value.ilike(f"%{telecom}%"),
                ),
            )
        if email:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_id == PractitionerModel.id,
                    PractitionerTelecom.system == ContactPointSystem.email,
                    PractitionerTelecom.value.ilike(f"%{email}%"),
                ),
            )
        if phone:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_id == PractitionerModel.id,
                    PractitionerTelecom.system == ContactPointSystem.phone,
                    PractitionerTelecom.value.ilike(f"%{phone}%"),
                ),
            )
        if qualification_code:
            # No Patient precedent — Practitioner-only child table.
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerQualification.id).where(
                    PractitionerQualification.practitioner_id == PractitionerModel.id,
                    PractitionerQualification.code_code == qualification_code,
                ),
            )
        return stmt

    async def list(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender=None,
        active: bool | None = None,
        identifier: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        qualification_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PractitionerModel], int | None]:
        """Paginated, filtered, sorted list of practitioners. Backs GET /.
        Returns (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "user_id": user_id,
                "org_id": org_id,
                "family": family,
                "given": given,
                "name": name,
                "gender": gender,
                "active": active,
                "identifier": identifier,
                "communication": communication,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
                "telecom": telecom,
                "email": email,
                "phone": phone,
                "qualification_code": qualification_code,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PractitionerModel.practitioner_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        return rows, total

    async def create(
        self,
        payload: PractitionerCreateSchema,
        user_id: str | None = None,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PractitionerModel:
        async with self.session_factory() as session:
            practitioner = PractitionerModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                created_by=created_by,
            )
            try:
                session.add(practitioner)
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner.practitioner_id)

    async def patch(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(practitioner, field, value)
            if updated_by is not None:
                practitioner.updated_by = updated_by
            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def delete(self, practitioner_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return False
            try:
                await session.delete(practitioner)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

    async def _get_internal(
        self, session, practitioner_id: int
    ) -> PractitionerModel | None:
        stmt = select(PractitionerModel).where(
            PractitionerModel.practitioner_id == practitioner_id
        )
        return (await session.execute(stmt)).scalars().first()

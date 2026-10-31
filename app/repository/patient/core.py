from datetime import date, datetime

from sqlalchemy import String, func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.patient import (
    PatientAddress,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientModel,
    PatientName,
    PatientTelecom,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for the Patient parent row."""

    async def get_by_patient_id(self, patient_id: int) -> PatientModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.patient_id == patient_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_patient_id_in_org(
        self, patient_id: int, org_id: str
    ) -> PatientModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the patient exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(
                    PatientModel.patient_id == patient_id,
                    PatientModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def patient_belongs_to_org(self, patient_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the patient exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = select(PatientModel.id).where(
                PatientModel.patient_id == patient_id,
                PatientModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        user_id: str | None = None,
        active: bool | None = None,
        gender=None,
        birthdate: date | None = None,
        birthdate_from: date | datetime | None = None,
        birthdate_to: date | datetime | None = None,
        deceased: bool | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        general_practitioner: str | None = None,
        organization: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(PatientModel.tenant_id == org_id)
        if user_id:
            stmt = stmt.where(PatientModel.user_id == user_id)
        stmt = apply_token_filter(stmt, PatientModel.active, active)
        stmt = apply_token_filter(stmt, PatientModel.gender, gender)

        if birthdate:
            stmt = stmt.where(PatientModel.birth_date == birthdate)
        elif birthdate_from or birthdate_to:
            stmt = apply_date_range_filter(
                stmt,
                PatientModel.birth_date,
                date_from=birthdate_from,
                date_to=birthdate_to,
            )

        if deceased is not None:
            stmt = apply_token_filter(stmt, PatientModel.deceased_boolean, deceased)

        if family:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_pk == PatientModel.id,
                    PatientName.family.ilike(f"%{family}%"),
                ),
            )
        if given:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_pk == PatientModel.id,
                    func.array_to_string(PatientName.given, " ").ilike(f"%{given}%"),
                ),
            )
        if name or phonetic:
            pattern = f"%{name or phonetic}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_pk == PatientModel.id,
                    or_(
                        PatientName.text.ilike(pattern),
                        PatientName.family.ilike(pattern),
                        func.array_to_string(PatientName.given, " ").ilike(pattern),
                        func.array_to_string(PatientName.prefix, " ").ilike(pattern),
                        func.array_to_string(PatientName.suffix, " ").ilike(pattern),
                    ),
                ),
            )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientIdentifier.id).where(
                    PatientIdentifier.patient_pk == PatientModel.id,
                    PatientIdentifier.value == identifier,
                ),
            )
        if telecom:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_pk == PatientModel.id,
                    PatientTelecom.value == telecom,
                ),
            )
        if phone:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_pk == PatientModel.id,
                    PatientTelecom.system == "phone",
                    PatientTelecom.value == phone,
                ),
            )
        if email:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_pk == PatientModel.id,
                    PatientTelecom.system == "email",
                    PatientTelecom.value == email,
                ),
            )
        if address:
            pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    or_(
                        func.array_to_string(PatientAddress.line, " ").ilike(pattern),
                        PatientAddress.city.ilike(pattern),
                        PatientAddress.district.ilike(pattern),
                        PatientAddress.state.ilike(pattern),
                        PatientAddress.country.ilike(pattern),
                        PatientAddress.postal_code.ilike(pattern),
                        PatientAddress.text.ilike(pattern),
                    ),
                ),
            )
        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    PatientAddress.city.ilike(f"%{address_city}%"),
                ),
            )
        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    PatientAddress.state.ilike(f"%{address_state}%"),
                ),
            )
        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    PatientAddress.postal_code == address_postal_code,
                ),
            )
        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    PatientAddress.country.ilike(f"%{address_country}%"),
                ),
            )
        if address_use is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_pk == PatientModel.id,
                    PatientAddress.use == address_use,
                ),
            )
        if general_practitioner:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientGeneralPractitioner.id).where(
                    PatientGeneralPractitioner.patient_pk == PatientModel.id,
                    or_(
                        PatientGeneralPractitioner.reference_reference == general_practitioner,
                        func.cast(PatientGeneralPractitioner.reference_id, String) == str(general_practitioner),
                    ),
                ),
            )
        if organization:
            org_id_val = None
            if organization.startswith("Organization/"):
                try:
                    org_id_val = int(organization.split("/")[1])
                except ValueError:
                    pass
            elif organization.isdigit():
                org_id_val = int(organization)

            if org_id_val is not None:
                stmt = stmt.where(
                    or_(
                        PatientModel.managing_organization_reference == organization,
                        PatientModel.managing_organization_id == org_id_val,
                    )
                )
            else:
                stmt = stmt.where(
                    PatientModel.managing_organization_reference == organization
                )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        active: bool | None = None,
        gender=None,
        birthdate: date | None = None,
        birthdate_from: date | datetime | None = None,
        birthdate_to: date | datetime | None = None,
        deceased: bool | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        general_practitioner: str | None = None,
        organization: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PatientModel], int | None]:
        """Paginated, filtered, sorted list of patients. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "active": active,
                "gender": gender,
                "birthdate": birthdate,
                "birthdate_from": birthdate_from,
                "birthdate_to": birthdate_to,
                "deceased": deceased,
                "family": family,
                "given": given,
                "name": name,
                "phonetic": phonetic,
                "identifier": identifier,
                "telecom": telecom,
                "phone": phone,
                "email": email,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
                "general_practitioner": general_practitioner,
                "organization": organization,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PatientModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PatientModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PatientModel.patient_id,
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
        logger.debug(
            "Patients listed",
            extra={
                "event": "patient.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        **filters,
    ) -> tuple[list[PatientModel], int | None]:
        """Same filters as list(), always scoped to this user_id AND org_id."""
        return await self.list(org_id=org_id, user_id=user_id, **filters)

    async def delete(self, patient_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            p = (await session.execute(stmt)).scalars().first()
            if not p:
                return False
            try:
                await session.delete(p)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

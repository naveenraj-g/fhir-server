from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.immunization import (
    ImmunizationIdentifierModel,
    ImmunizationModel,
    ImmunizationPatientReferenceType,
    ImmunizationStatus,
    ImmunizationVaccineCodingModel,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Immunization."""

    async def get_by_immunization_id(
        self, immunization_id: int
    ) -> ImmunizationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationModel).where(
                    ImmunizationModel.immunization_id == immunization_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_immunization_id_in_org(
        self, immunization_id: int, org_id: str
    ) -> ImmunizationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ImmunizationModel).where(
                    ImmunizationModel.immunization_id == immunization_id,
                    ImmunizationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def immunization_belongs_to_org(
        self, immunization_id: int, org_id: str
    ) -> bool:
        """Cheap existence/ownership check (no joins, no sub-resources)."""
        async with self.session_factory() as session:
            stmt = select(func.count(ImmunizationModel.id)).where(
                ImmunizationModel.immunization_id == immunization_id,
                ImmunizationModel.tenant_id == org_id,
            )
            count = (await session.execute(stmt)).scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | ImmunizationStatus | None = None,
        patient: str | None = None,
        vaccine_code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ImmunizationModel.tenant_id == org_id)

        if status:
            val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(ImmunizationModel.status == val)

        if patient:
            if patient.isdigit():
                stmt = stmt.where(ImmunizationModel.patient_id == int(patient))
            else:
                p_type, p_id = parse_reference(patient, ImmunizationPatientReferenceType)
                if p_id:
                    stmt = stmt.where(ImmunizationModel.patient_id == p_id)
                else:
                    stmt = stmt.where(ImmunizationModel.patient_reference == patient)

        if vaccine_code:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationModel.vaccine_codings,
                ImmunizationVaccineCodingModel,
                lambda q: apply_token_filter(
                    q,
                    vaccine_code,
                    code_col=ImmunizationVaccineCodingModel.code,
                    system_col=ImmunizationVaccineCodingModel.system,
                ),
            )

        if date_val:
            val_str = date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val)
            stmt = stmt.where(
                or_(
                    func.date(ImmunizationModel.occurrence_date_time) == date_val,
                    ImmunizationModel.occurrence_string == val_str,
                )
            )
        elif date_from or date_to:
            stmt = apply_date_range_filter(
                stmt,
                ImmunizationModel.occurrence_date_time,
                date_from=date_from,
                date_to=date_to,
            )

        if location:
            if location.isdigit():
                stmt = stmt.where(ImmunizationModel.location_id == int(location))
            else:
                parts = location.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(ImmunizationModel.location_id == int(parts[1]))
                else:
                    stmt = stmt.where(ImmunizationModel.location_reference == location)

        if manufacturer:
            if manufacturer.isdigit():
                stmt = stmt.where(ImmunizationModel.manufacturer_id == int(manufacturer))
            else:
                parts = manufacturer.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    stmt = stmt.where(ImmunizationModel.manufacturer_id == int(parts[1]))
                else:
                    stmt = stmt.where(ImmunizationModel.manufacturer_reference == manufacturer)

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                ImmunizationModel.identifiers,
                ImmunizationIdentifierModel,
                lambda q: apply_token_filter(
                    q,
                    identifier,
                    code_col=ImmunizationIdentifierModel.value,
                    system_col=ImmunizationIdentifierModel.system,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        status: str | ImmunizationStatus | None = None,
        patient: str | None = None,
        vaccine_code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ImmunizationModel], int | None]:
        async with self.session_factory() as session:
            count_stmt = select(func.count(ImmunizationModel.id))
            count_stmt = self._apply_list_filters(
                count_stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                vaccine_code=vaccine_code,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                location=location,
                manufacturer=manufacturer,
                identifier=identifier,
            )
            total = (await session.execute(count_stmt)).scalar() if total_mode == "accurate" else None

            stmt = select(ImmunizationModel)
            stmt = self._apply_list_filters(
                stmt,
                org_id=org_id,
                status=status,
                patient=patient,
                vaccine_code=vaccine_code,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                location=location,
                manufacturer=manufacturer,
                identifier=identifier,
            )
            stmt = _with_relationships(stmt)
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ImmunizationModel.immunization_id,
                default_desc=False,
            )
            rows, total = await self._execute_paginated(
                session,
                stmt,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total

    async def delete(self, immunization_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ImmunizationModel).where(
                ImmunizationModel.immunization_id == immunization_id,
                ImmunizationModel.tenant_id == org_id,
            )
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return False
            await session.delete(row)
            await session.commit()
            return True

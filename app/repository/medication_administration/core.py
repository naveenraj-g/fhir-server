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
from app.models.medication_administration import (
    MedicationAdministrationCategoryCoding,
    MedicationAdministrationIdentifier,
    MedicationAdministrationMedicationCoding,
    MedicationAdministrationModel,
    MedicationAdministrationStatus,
    MedicationAdministrationSubjectReferenceType,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for MedicationAdministration."""

    async def get_by_medication_administration_id(
        self, medication_administration_id: int
    ) -> MedicationAdministrationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationAdministrationModel).where(
                    MedicationAdministrationModel.medication_administration_id
                    == medication_administration_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_medication_administration_id_in_org(
        self, medication_administration_id: int, org_id: str
    ) -> MedicationAdministrationModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationAdministrationModel).where(
                    MedicationAdministrationModel.medication_administration_id
                    == medication_administration_id,
                    MedicationAdministrationModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def medication_administration_belongs_to_org(
        self, medication_administration_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationAdministrationModel.id).where(
                MedicationAdministrationModel.medication_administration_id
                == medication_administration_id,
                MedicationAdministrationModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | MedicationAdministrationStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        effective_val: date | datetime | None = None,
        effective_from: date | datetime | None = None,
        effective_to: date | datetime | None = None,
        identifier: str | None = None,
        request: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationAdministrationModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, MedicationAdministrationModel.status, status)

        subj_filter = subject or patient
        if subj_filter:
            ref_type, ref_id = parse_reference(subj_filter, MedicationAdministrationSubjectReferenceType)
            if ref_id:
                stmt = stmt.where(MedicationAdministrationModel.subject_id == ref_id)
            else:
                stmt = stmt.where(MedicationAdministrationModel.subject_reference == subj_filter)

        if effective_val or effective_from or effective_to:
            stmt = apply_date_range_filter(
                stmt,
                col_exact=MedicationAdministrationModel.effective_date_time,
                col_start=MedicationAdministrationModel.effective_period_start,
                col_end=MedicationAdministrationModel.effective_period_end,
                val=effective_val,
                from_date=effective_from,
                to_date=effective_to,
            )

        if code:
            stmt = stmt.where(
                or_(
                    MedicationAdministrationModel.medication_codeable_concept_text.ilike(f"%{code}%"),
                    MedicationAdministrationModel.medication_reference.ilike(f"%{code}%"),
                    MedicationAdministrationModel.id.in_(
                        select(MedicationAdministrationMedicationCoding.medication_administration_pk).where(
                            or_(
                                MedicationAdministrationMedicationCoding.code == code,
                                MedicationAdministrationMedicationCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )

        if category:
            stmt = stmt.where(
                or_(
                    MedicationAdministrationModel.category_text.ilike(f"%{category}%"),
                    MedicationAdministrationModel.id.in_(
                        select(MedicationAdministrationCategoryCoding.medication_administration_pk).where(
                            or_(
                                MedicationAdministrationCategoryCoding.code == category,
                                MedicationAdministrationCategoryCoding.display.ilike(f"%{category}%"),
                            )
                        )
                    ),
                )
            )

        if identifier:
            stmt = stmt.where(
                MedicationAdministrationModel.id.in_(
                    select(MedicationAdministrationIdentifier.medication_administration_pk).where(
                        or_(
                            MedicationAdministrationIdentifier.value == identifier,
                            MedicationAdministrationIdentifier.system == identifier,
                        )
                    )
                )
            )

        if request:
            parts = request.split("/")
            if len(parts) == 2 and parts[1].isdigit():
                stmt = stmt.where(MedicationAdministrationModel.request_id == int(parts[1]))
            else:
                stmt = stmt.where(MedicationAdministrationModel.request_reference == request)

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: str | MedicationAdministrationStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        effective_val: date | datetime | None = None,
        effective_from: date | datetime | None = None,
        effective_to: date | datetime | None = None,
        identifier: str | None = None,
        request: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MedicationAdministrationModel], int]:
        async with self.session_factory() as session:
            base_stmt = select(MedicationAdministrationModel)
            filtered_stmt = self._apply_list_filters(
                base_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                patient=patient,
                code=code,
                category=category,
                effective_val=effective_val,
                effective_from=effective_from,
                effective_to=effective_to,
                identifier=identifier,
                request=request,
            )

            count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
            total = (await session.execute(count_stmt)).scalar_one()

            sort_col, is_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MedicationAdministrationModel.medication_administration_id,
            )
            order_expr = sort_col.desc() if is_desc else sort_col.asc()
            filtered_stmt = filtered_stmt.order_by(order_expr)

            data_stmt = (
                _with_relationships(filtered_stmt).limit(limit).offset(offset)
            )
            results = (await session.execute(data_stmt)).scalars().all()
            return list(results), total

    async def delete(self, medication_administration_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationAdministrationModel).where(
                MedicationAdministrationModel.medication_administration_id
                == medication_administration_id,
                MedicationAdministrationModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

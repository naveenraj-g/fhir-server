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
from app.models.medication_dispense import (
    MedicationDispenseCategoryCoding,
    MedicationDispenseDestinationReferenceType,
    MedicationDispenseIdentifier,
    MedicationDispenseLocationReferenceType,
    MedicationDispenseMedicationCoding,
    MedicationDispenseModel,
    MedicationDispenseReceiver,
    MedicationDispenseStatus,
    MedicationDispenseSubjectReferenceType,
    MedicationDispenseTypeCoding,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for MedicationDispense."""

    async def get_by_medication_dispense_id(
        self, medication_dispense_id: int
    ) -> MedicationDispenseModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationDispenseModel).where(
                    MedicationDispenseModel.medication_dispense_id
                    == medication_dispense_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_medication_dispense_id_in_org(
        self, medication_dispense_id: int, org_id: str
    ) -> MedicationDispenseModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationDispenseModel).where(
                    MedicationDispenseModel.medication_dispense_id
                    == medication_dispense_id,
                    MedicationDispenseModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def medication_dispense_belongs_to_org(
        self, medication_dispense_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationDispenseModel.id).where(
                MedicationDispenseModel.medication_dispense_id
                == medication_dispense_id,
                MedicationDispenseModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | MedicationDispenseStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        type: str | None = None,
        when_prepared_val: date | datetime | None = None,
        when_prepared_from: date | datetime | None = None,
        when_prepared_to: date | datetime | None = None,
        when_handed_over_val: date | datetime | None = None,
        when_handed_over_from: date | datetime | None = None,
        when_handed_over_to: date | datetime | None = None,
        identifier: str | None = None,
        destination: str | None = None,
        receiver: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationDispenseModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, MedicationDispenseModel.status, status)

        subj_filter = subject or patient
        if subj_filter:
            ref_type, ref_id = parse_reference(subj_filter, MedicationDispenseSubjectReferenceType)
            if ref_id:
                stmt = stmt.where(MedicationDispenseModel.subject_id == ref_id)
            else:
                stmt = stmt.where(MedicationDispenseModel.subject_reference == subj_filter)

        if code:
            stmt = stmt.where(
                or_(
                    MedicationDispenseModel.medication_codeable_concept_text.ilike(f"%{code}%"),
                    MedicationDispenseModel.medication_reference.ilike(f"%{code}%"),
                    MedicationDispenseModel.id.in_(
                        select(MedicationDispenseMedicationCoding.medication_dispense_pk).where(
                            or_(
                                MedicationDispenseMedicationCoding.code == code,
                                MedicationDispenseMedicationCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )

        if category:
            stmt = stmt.where(
                or_(
                    MedicationDispenseModel.category_text.ilike(f"%{category}%"),
                    MedicationDispenseModel.id.in_(
                        select(MedicationDispenseCategoryCoding.medication_dispense_pk).where(
                            or_(
                                MedicationDispenseCategoryCoding.code == category,
                                MedicationDispenseCategoryCoding.display.ilike(f"%{category}%"),
                            )
                        )
                    ),
                )
            )

        if type:
            stmt = stmt.where(
                or_(
                    MedicationDispenseModel.type_text.ilike(f"%{type}%"),
                    MedicationDispenseModel.id.in_(
                        select(MedicationDispenseTypeCoding.medication_dispense_pk).where(
                            or_(
                                MedicationDispenseTypeCoding.code == type,
                                MedicationDispenseTypeCoding.display.ilike(f"%{type}%"),
                            )
                        )
                    ),
                )
            )

        if when_prepared_val or when_prepared_from or when_prepared_to:
            stmt = apply_date_range_filter(
                stmt,
                MedicationDispenseModel.when_prepared,
                date_from=when_prepared_from or when_prepared_val,
                date_to=when_prepared_to or when_prepared_val,
            )

        if when_handed_over_val or when_handed_over_from or when_handed_over_to:
            stmt = apply_date_range_filter(
                stmt,
                MedicationDispenseModel.when_handed_over,
                date_from=when_handed_over_from or when_handed_over_val,
                date_to=when_handed_over_to or when_handed_over_val,
            )

        if identifier:
            parts = identifier.split("|", 1)
            if len(parts) == 2:
                sys, val = parts
                stmt = apply_child_exists_filter(
                    stmt,
                    select(MedicationDispenseIdentifier.id).where(
                        MedicationDispenseIdentifier.medication_dispense_pk == MedicationDispenseModel.id,
                        MedicationDispenseIdentifier.system == sys,
                        MedicationDispenseIdentifier.value == val,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(MedicationDispenseIdentifier.id).where(
                        MedicationDispenseIdentifier.medication_dispense_pk == MedicationDispenseModel.id,
                        MedicationDispenseIdentifier.value == identifier,
                    ),
                )

        if destination:
            ref_type, ref_id = parse_reference(destination, MedicationDispenseDestinationReferenceType)
            if ref_id:
                stmt = stmt.where(MedicationDispenseModel.destination_id == ref_id)
            else:
                stmt = stmt.where(MedicationDispenseModel.destination_reference == destination)

        if receiver:
            parts = receiver.split("/")
            if len(parts) == 2 and parts[1].isdigit():
                stmt = stmt.where(
                    MedicationDispenseModel.receivers.any(
                        MedicationDispenseReceiver.reference_id == int(parts[1])
                    )
                )
            else:
                stmt = stmt.where(
                    MedicationDispenseModel.receivers.any(
                        MedicationDispenseReceiver.reference_reference == receiver
                    )
                )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: str | MedicationDispenseStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        type: str | None = None,
        when_prepared_val: date | datetime | None = None,
        when_prepared_from: date | datetime | None = None,
        when_prepared_to: date | datetime | None = None,
        when_handed_over_val: date | datetime | None = None,
        when_handed_over_from: date | datetime | None = None,
        when_handed_over_to: date | datetime | None = None,
        identifier: str | None = None,
        destination: str | None = None,
        receiver: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MedicationDispenseModel], int]:
        async with self.session_factory() as session:
            base_stmt = select(MedicationDispenseModel)
            filtered_stmt = self._apply_list_filters(
                base_stmt,
                org_id=org_id,
                status=status,
                subject=subject,
                patient=patient,
                code=code,
                category=category,
                type=type,
                when_prepared_val=when_prepared_val,
                when_prepared_from=when_prepared_from,
                when_prepared_to=when_prepared_to,
                when_handed_over_val=when_handed_over_val,
                when_handed_over_from=when_handed_over_from,
                when_handed_over_to=when_handed_over_to,
                identifier=identifier,
                destination=destination,
                receiver=receiver,
            )

            count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
            total = (await session.execute(count_stmt)).scalar_one()

            sort_col, is_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MedicationDispenseModel.medication_dispense_id,
            )
            order_expr = sort_col.desc() if is_desc else sort_col.asc()
            filtered_stmt = filtered_stmt.order_by(order_expr)

            data_stmt = (
                _with_relationships(filtered_stmt).limit(limit).offset(offset)
            )
            results = (await session.execute(data_stmt)).scalars().all()
            return list(results), total

    async def delete(self, medication_dispense_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationDispenseModel).where(
                MedicationDispenseModel.medication_dispense_id
                == medication_dispense_id,
                MedicationDispenseModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

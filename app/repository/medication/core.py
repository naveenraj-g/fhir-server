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
from app.models.medication import (
    MedicationCodeCoding,
    MedicationFormCoding,
    MedicationIdentifier,
    MedicationIngredient,
    MedicationIngredientItemCoding,
    MedicationIngredientItemReferenceType,
    MedicationManufacturerReferenceType,
    MedicationModel,
    MedicationStatus,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Medication."""

    async def get_by_medication_id(
        self, medication_id: int
    ) -> MedicationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationModel).where(
                    MedicationModel.medication_id == medication_id
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_medication_id_in_org(
        self, medication_id: int, org_id: str
    ) -> MedicationModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationModel).where(
                    MedicationModel.medication_id == medication_id,
                    MedicationModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def medication_belongs_to_org(
        self, medication_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(func.count()).select_from(MedicationModel).where(
                MedicationModel.medication_id == medication_id,
                MedicationModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            count = res.scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        code: str | None = None,
        status: str | MedicationStatus | None = None,
        manufacturer: str | None = None,
        form: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
        lot_number: str | None = None,
        expiration_date: date | datetime | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, MedicationModel.status, status)

        if code:
            stmt = stmt.where(
                or_(
                    MedicationModel.code_text.ilike(f"%{code}%"),
                    MedicationModel.id.in_(
                        select(MedicationCodeCoding.medication_pk).where(
                            or_(
                                MedicationCodeCoding.code == code,
                                MedicationCodeCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )

        if manufacturer:
            ref_type, ref_id = parse_reference(manufacturer, MedicationManufacturerReferenceType)
            if ref_id:
                stmt = stmt.where(MedicationModel.manufacturer_id == ref_id)
            else:
                stmt = stmt.where(MedicationModel.manufacturer_reference == manufacturer)

        if form:
            stmt = stmt.where(
                or_(
                    MedicationModel.form_text.ilike(f"%{form}%"),
                    MedicationModel.id.in_(
                        select(MedicationFormCoding.medication_pk).where(
                            or_(
                                MedicationFormCoding.code == form,
                                MedicationFormCoding.display.ilike(f"%{form}%"),
                            )
                        )
                    ),
                )
            )

        if ingredient:
            ref_type, ref_id = parse_reference(ingredient, MedicationIngredientItemReferenceType)
            if ref_id:
                stmt = stmt.where(
                    MedicationModel.ingredients.any(
                        MedicationIngredient.item_id == ref_id
                    )
                )
            else:
                stmt = stmt.where(
                    MedicationModel.ingredients.any(
                        MedicationIngredient.item_reference == ingredient
                    )
                )

        if ingredient_code:
            stmt = stmt.where(
                MedicationModel.ingredients.any(
                    or_(
                        MedicationIngredient.item_codeable_concept_text.ilike(f"%{ingredient_code}%"),
                        MedicationIngredient.id.in_(
                            select(MedicationIngredientItemCoding.medication_ingredient_id).where(
                                or_(
                                    MedicationIngredientItemCoding.code == ingredient_code,
                                    MedicationIngredientItemCoding.display.ilike(f"%{ingredient_code}%"),
                                )
                            )
                        ),
                    )
                )
            )

        if lot_number:
            stmt = stmt.where(MedicationModel.batch_lot_number == lot_number)

        if expiration_date:
            stmt = apply_date_range_filter(
                stmt,
                MedicationModel.batch_expiration_date,
                date_from=expiration_date,
                date_to=expiration_date,
            )

        if identifier:
            parts = identifier.split("|", 1)
            if len(parts) == 2:
                sys, val = parts
                stmt = apply_child_exists_filter(
                    stmt,
                    select(MedicationIdentifier.id).where(
                        MedicationIdentifier.medication_pk == MedicationModel.id,
                        MedicationIdentifier.system == sys,
                        MedicationIdentifier.value == val,
                    ),
                )
            else:
                stmt = apply_child_exists_filter(
                    stmt,
                    select(MedicationIdentifier.id).where(
                        MedicationIdentifier.medication_pk == MedicationModel.id,
                        MedicationIdentifier.value == identifier,
                    ),
                )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        code: str | None = None,
        status: str | MedicationStatus | None = None,
        manufacturer: str | None = None,
        form: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
        lot_number: str | None = None,
        expiration_date: date | datetime | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MedicationModel], int]:
        async with self.session_factory() as session:
            base_stmt = select(MedicationModel)
            filtered_stmt = self._apply_list_filters(
                base_stmt,
                org_id=org_id,
                code=code,
                status=status,
                manufacturer=manufacturer,
                form=form,
                ingredient=ingredient,
                ingredient_code=ingredient_code,
                lot_number=lot_number,
                expiration_date=expiration_date,
                identifier=identifier,
            )

            count_stmt = select(func.count()).select_from(
                filtered_stmt.order_by(None).subquery()
            )
            count_res = await session.execute(count_stmt)
            total = count_res.scalar() or 0

            data_stmt = _with_relationships(filtered_stmt)
            sort_col, is_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                MedicationModel.medication_id,
            )
            order_expr = sort_col.desc() if is_desc else sort_col.asc()
            data_stmt = data_stmt.order_by(order_expr).limit(limit).offset(offset)

            res = await session.execute(data_stmt)
            models = list(res.scalars().all())
            return models, total

    async def delete(self, medication_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationModel).where(
                MedicationModel.medication_id == medication_id,
                MedicationModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.medication_knowledge import (
    MedicationKnowledgeCodeCoding,
    MedicationKnowledgeDoseFormCoding,
    MedicationKnowledgeIngredient,
    MedicationKnowledgeIngredientItemCoding,
    MedicationKnowledgeIngredientItemReferenceType,
    MedicationKnowledgeManufacturerReferenceType,
    MedicationKnowledgeModel,
    MedicationKnowledgeMonitoringProgram,
    MedicationKnowledgeStatus,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for MedicationKnowledge."""

    async def get_by_medication_knowledge_id(
        self, medication_knowledge_id: int
    ) -> MedicationKnowledgeModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationKnowledgeModel).where(
                    MedicationKnowledgeModel.medication_knowledge_id == medication_knowledge_id
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_medication_knowledge_id_in_org(
        self, medication_knowledge_id: int, org_id: str
    ) -> MedicationKnowledgeModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(MedicationKnowledgeModel).where(
                    MedicationKnowledgeModel.medication_knowledge_id == medication_knowledge_id,
                    MedicationKnowledgeModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def medication_knowledge_belongs_to_org(
        self, medication_knowledge_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(func.count()).select_from(MedicationKnowledgeModel).where(
                MedicationKnowledgeModel.medication_knowledge_id == medication_knowledge_id,
                MedicationKnowledgeModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            count = res.scalar() or 0
            return count > 0

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        code: str | None = None,
        status: str | MedicationKnowledgeStatus | None = None,
        manufacturer: str | None = None,
        dose_form: str | None = None,
        monitoring_program: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(MedicationKnowledgeModel.tenant_id == org_id)

        if status:
            stmt = apply_token_filter(stmt, MedicationKnowledgeModel.status, status)

        if code:
            stmt = stmt.where(
                or_(
                    MedicationKnowledgeModel.code_text.ilike(f"%{code}%"),
                    MedicationKnowledgeModel.id.in_(
                        select(MedicationKnowledgeCodeCoding.medication_knowledge_pk).where(
                            or_(
                                MedicationKnowledgeCodeCoding.code == code,
                                MedicationKnowledgeCodeCoding.display.ilike(f"%{code}%"),
                            )
                        )
                    ),
                )
            )

        if manufacturer:
            res_type, res_id = parse_reference(
                manufacturer, MedicationKnowledgeManufacturerReferenceType
            )
            if res_id:
                stmt = stmt.where(MedicationKnowledgeModel.manufacturer_id == res_id)
            else:
                stmt = stmt.where(
                    MedicationKnowledgeModel.manufacturer_reference.ilike(
                        f"%{manufacturer}%"
                    )
                )

        if dose_form:
            stmt = stmt.where(
                or_(
                    MedicationKnowledgeModel.dose_form_text.ilike(f"%{dose_form}%"),
                    MedicationKnowledgeModel.id.in_(
                        select(MedicationKnowledgeDoseFormCoding.medication_knowledge_pk).where(
                            or_(
                                MedicationKnowledgeDoseFormCoding.code == dose_form,
                                MedicationKnowledgeDoseFormCoding.display.ilike(f"%{dose_form}%"),
                            )
                        )
                    ),
                )
            )

        if monitoring_program:
            stmt = stmt.where(
                MedicationKnowledgeModel.id.in_(
                    select(MedicationKnowledgeMonitoringProgram.medication_knowledge_pk).where(
                        or_(
                            MedicationKnowledgeMonitoringProgram.name.ilike(f"%{monitoring_program}%"),
                            MedicationKnowledgeMonitoringProgram.type_text.ilike(f"%{monitoring_program}%"),
                        )
                    )
                )
            )

        if ingredient:
            res_type, res_id = parse_reference(
                ingredient, MedicationKnowledgeIngredientItemReferenceType
            )
            if res_id:
                stmt = stmt.where(
                    MedicationKnowledgeModel.id.in_(
                        select(MedicationKnowledgeIngredient.medication_knowledge_pk).where(
                            MedicationKnowledgeIngredient.item_id == res_id
                        )
                    )
                )
            else:
                stmt = stmt.where(
                    MedicationKnowledgeModel.id.in_(
                        select(MedicationKnowledgeIngredient.medication_knowledge_pk).where(
                            MedicationKnowledgeIngredient.item_reference.ilike(
                                f"%{ingredient}%"
                            )
                        )
                    )
                )

        if ingredient_code:
            stmt = stmt.where(
                MedicationKnowledgeModel.id.in_(
                    select(MedicationKnowledgeIngredient.medication_knowledge_pk).where(
                        or_(
                            MedicationKnowledgeIngredient.item_codeable_concept_text.ilike(
                                f"%{ingredient_code}%"
                            ),
                            MedicationKnowledgeIngredient.id.in_(
                                select(
                                    MedicationKnowledgeIngredientItemCoding.medication_knowledge_ingredient_id
                                ).where(
                                    or_(
                                        MedicationKnowledgeIngredientItemCoding.code == ingredient_code,
                                        MedicationKnowledgeIngredientItemCoding.display.ilike(
                                            f"%{ingredient_code}%"
                                        ),
                                    )
                                )
                            ),
                        )
                    )
                )
            )

        return stmt

    async def list(
        self,
        org_id: str,
        code: str | None = None,
        status: str | MedicationKnowledgeStatus | None = None,
        manufacturer: str | None = None,
        dose_form: str | None = None,
        monitoring_program: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MedicationKnowledgeModel], int]:
        async with self.session_factory() as session:
            base_stmt = select(MedicationKnowledgeModel)
            filtered_stmt = self._apply_list_filters(
                base_stmt,
                org_id=org_id,
                code=code,
                status=status,
                manufacturer=manufacturer,
                dose_form=dose_form,
                monitoring_program=monitoring_program,
                ingredient=ingredient,
                ingredient_code=ingredient_code,
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
                MedicationKnowledgeModel.medication_knowledge_id,
            )
            order_expr = sort_col.desc() if is_desc else sort_col.asc()
            data_stmt = data_stmt.order_by(order_expr).limit(limit).offset(offset)
            res = await session.execute(data_stmt)
            models = list(res.scalars().all())
            return models, total

    async def delete(self, medication_knowledge_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(MedicationKnowledgeModel).where(
                MedicationKnowledgeModel.medication_knowledge_id == medication_knowledge_id,
                MedicationKnowledgeModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

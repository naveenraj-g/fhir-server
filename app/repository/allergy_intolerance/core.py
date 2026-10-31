from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    ArrayContains,
    apply_child_exists_filter,
    apply_date_range_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.allergy_intolerance import (
    AllergyIntoleranceClinicalStatusCoding,
    AllergyIntoleranceCodeCoding,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceModel,
    AllergyIntoleranceReaction,
    AllergyIntoleranceType,
    AllergyIntoleranceVerificationStatusCoding,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_asserter_ref,
    _parse_patient_ref,
    _parse_recorder_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for AllergyIntolerance."""

    async def get_by_allergy_intolerance_id(
        self, allergy_intolerance_id: int
    ) -> AllergyIntoleranceModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AllergyIntoleranceModel).where(
                    AllergyIntoleranceModel.allergy_intolerance_id
                    == allergy_intolerance_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_allergy_intolerance_id_in_org(
        self, allergy_intolerance_id: int, org_id: str
    ) -> AllergyIntoleranceModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AllergyIntoleranceModel).where(
                    AllergyIntoleranceModel.allergy_intolerance_id
                    == allergy_intolerance_id,
                    AllergyIntoleranceModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def allergy_intolerance_belongs_to_org(
        self, allergy_intolerance_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(AllergyIntoleranceModel.id).where(
                AllergyIntoleranceModel.allergy_intolerance_id
                == allergy_intolerance_id,
                AllergyIntoleranceModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        type: str | AllergyIntoleranceType | None = None,
        category: str | None = None,
        criticality: str | AllergyIntoleranceCriticality | None = None,
        code: str | None = None,
        patient: str | None = None,
        severity: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        recorder: str | None = None,
        asserter: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(AllergyIntoleranceModel.tenant_id == org_id)

        if clinical_status:
            stmt = stmt.where(
                or_(
                    AllergyIntoleranceModel.clinical_status_text.ilike(
                        f"%{clinical_status}%"
                    ),
                    AllergyIntoleranceModel.id.in_(
                        select(
                            AllergyIntoleranceClinicalStatusCoding.allergy_intolerance_pk
                        ).where(
                            or_(
                                AllergyIntoleranceClinicalStatusCoding.code
                                == clinical_status,
                                AllergyIntoleranceClinicalStatusCoding.display.ilike(
                                    f"%{clinical_status}%"
                                ),
                            )
                        )
                    ),
                )
            )

        if verification_status:
            stmt = stmt.where(
                or_(
                    AllergyIntoleranceModel.verification_status_text.ilike(
                        f"%{verification_status}%"
                    ),
                    AllergyIntoleranceModel.id.in_(
                        select(
                            AllergyIntoleranceVerificationStatusCoding.allergy_intolerance_pk
                        ).where(
                            or_(
                                AllergyIntoleranceVerificationStatusCoding.code
                                == verification_status,
                                AllergyIntoleranceVerificationStatusCoding.display.ilike(
                                    f"%{verification_status}%"
                                ),
                            )
                        )
                    ),
                )
            )

        if type:
            stmt = apply_token_filter(stmt, AllergyIntoleranceModel.type, type)

        if category:
            cat_val = category.value if hasattr(category, "value") else str(category)
            stmt = stmt.where(ArrayContains(AllergyIntoleranceModel.category, cat_val))

        if criticality:
            stmt = apply_token_filter(
                stmt, AllergyIntoleranceModel.criticality, criticality
            )

        if code:
            stmt = stmt.where(
                or_(
                    AllergyIntoleranceModel.code_text.ilike(f"%{code}%"),
                    AllergyIntoleranceModel.id.in_(
                        select(
                            AllergyIntoleranceCodeCoding.allergy_intolerance_pk
                        ).where(
                            or_(
                                AllergyIntoleranceCodeCoding.code == code,
                                AllergyIntoleranceCodeCoding.display.ilike(
                                    f"%{code}%"
                                ),
                            )
                        )
                    ),
                )
            )

        if patient:
            p_type, p_id = _parse_patient_ref(patient)
            if p_id:
                stmt = stmt.where(AllergyIntoleranceModel.patient_id == p_id)
            else:
                stmt = stmt.where(
                    AllergyIntoleranceModel.patient_reference == patient
                )

        if severity:
            stmt = stmt.where(
                AllergyIntoleranceModel.id.in_(
                    select(
                        AllergyIntoleranceReaction.allergy_intolerance_pk
                    ).where(AllergyIntoleranceReaction.severity == severity)
                )
            )

        if date_val or date_from or date_to:
            stmt = apply_date_range_filter(
                stmt,
                AllergyIntoleranceModel.recorded_date,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
            )

        if recorder:
            r_type, r_id = _parse_recorder_ref(recorder)
            if r_id:
                stmt = stmt.where(AllergyIntoleranceModel.recorder_id == r_id)
            else:
                stmt = stmt.where(
                    AllergyIntoleranceModel.recorder_reference == recorder
                )

        if asserter:
            a_type, a_id = _parse_asserter_ref(asserter)
            if a_id:
                stmt = stmt.where(AllergyIntoleranceModel.asserter_id == a_id)
            else:
                stmt = stmt.where(
                    AllergyIntoleranceModel.asserter_reference == asserter
                )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(AllergyIntoleranceIdentifier.id).where(
                    AllergyIntoleranceIdentifier.allergy_intolerance_pk
                    == AllergyIntoleranceModel.id,
                    AllergyIntoleranceIdentifier.value == identifier,
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        type: str | None = None,
        category: str | None = None,
        criticality: str | None = None,
        code: str | None = None,
        patient: str | None = None,
        severity: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        recorder: str | None = None,
        asserter: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AllergyIntoleranceModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = dict(
                org_id=org_id,
                clinical_status=clinical_status,
                verification_status=verification_status,
                type=type,
                category=category,
                criticality=criticality,
                code=code,
                patient=patient,
                severity=severity,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                recorder=recorder,
                asserter=asserter,
                identifier=identifier,
            )
            base = self._apply_list_filters(
                select(AllergyIntoleranceModel), **filter_kwargs
            )
            base = _with_relationships(base)
            count_stmt = self._apply_list_filters(
                select(func.count()).select_from(AllergyIntoleranceModel),
                **filter_kwargs,
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                AllergyIntoleranceModel.allergy_intolerance_id,
            )

            rows, total = await self._execute_paginated(
                session,
                base,
                count_stmt,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
            return list(rows), total

    async def delete(self, allergy_intolerance_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(AllergyIntoleranceModel).where(
                AllergyIntoleranceModel.allergy_intolerance_id
                == allergy_intolerance_id,
                AllergyIntoleranceModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

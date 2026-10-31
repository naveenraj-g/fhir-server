from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_date_range_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.consent import (
    ConsentCategory,
    ConsentCategoryCoding,
    ConsentIdentifier,
    ConsentModel,
    ConsentOrganization,
    ConsentProvision,
    ConsentProvisionAction,
    ConsentProvisionActionCoding,
    ConsentProvisionActor,
    ConsentProvisionData,
    ConsentProvisionPurpose,
    ConsentScopeCoding,
    ConsentStatus,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_organization_ref,
    _parse_patient_ref,
    _parse_source_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for Consent."""

    async def get_by_consent_id(self, consent_id: int) -> ConsentModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ConsentModel).where(ConsentModel.consent_id == consent_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_consent_id_in_org(
        self, consent_id: int, org_id: str
    ) -> ConsentModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ConsentModel).where(
                    ConsentModel.consent_id == consent_id,
                    ConsentModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def consent_belongs_to_org(self, consent_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ConsentModel.id).where(
                ConsentModel.consent_id == consent_id,
                ConsentModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        status: str | ConsentStatus | None = None,
        scope: str | None = None,
        category: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        period_from: date | datetime | None = None,
        period_to: date | datetime | None = None,
        actor: str | None = None,
        action: str | None = None,
        purpose: str | None = None,
        data: str | None = None,
        source_reference: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ConsentModel.tenant_id == org_id)
        if status:
            stmt = apply_token_filter(stmt, ConsentModel.status, status)

        if patient:
            p_type, p_id = _parse_patient_ref(patient)
            if p_id:
                stmt = stmt.where(ConsentModel.patient_id == p_id)
            else:
                stmt = stmt.where(ConsentModel.patient_reference == patient)

        if scope:
            stmt = stmt.where(
                or_(
                    ConsentModel.scope_text.ilike(f"%{scope}%"),
                    ConsentModel.id.in_(
                        select(ConsentScopeCoding.consent_pk).where(
                            or_(
                                ConsentScopeCoding.code == scope,
                                ConsentScopeCoding.display.ilike(f"%{scope}%"),
                            )
                        )
                    ),
                )
            )

        if category:
            stmt = stmt.where(
                ConsentModel.id.in_(
                    select(ConsentCategory.consent_pk).where(
                        or_(
                            ConsentCategory.text.ilike(f"%{category}%"),
                            ConsentCategory.id.in_(
                                select(ConsentCategoryCoding.category_id).where(
                                    or_(
                                        ConsentCategoryCoding.code == category,
                                        ConsentCategoryCoding.display.ilike(
                                            f"%{category}%"
                                        ),
                                    )
                                )
                            ),
                        )
                    )
                )
            )

        if date_val:
            stmt = stmt.where(func.date(ConsentModel.date_time) == date_val)
        elif date_from or date_to:
            stmt = apply_date_range_filter(
                stmt,
                ConsentModel.date_time,
                date_from=date_from,
                date_to=date_to,
            )

        if period_from or period_to:
            sub = select(ConsentProvision.consent_pk)
            if period_from:
                sub = sub.where(ConsentProvision.period_end >= period_from)
            if period_to:
                sub = sub.where(ConsentProvision.period_start <= period_to)
            stmt = stmt.where(ConsentModel.id.in_(sub))

        if actor:
            stmt = stmt.where(
                ConsentModel.id.in_(
                    select(ConsentProvision.consent_pk).where(
                        ConsentProvision.id.in_(
                            select(ConsentProvisionActor.provision_id).where(
                                ConsentProvisionActor.reference_reference.ilike(
                                    f"%{actor}%"
                                )
                            )
                        )
                    )
                )
            )

        if action:
            stmt = stmt.where(
                ConsentModel.id.in_(
                    select(ConsentProvision.consent_pk).where(
                        ConsentProvision.id.in_(
                            select(ConsentProvisionAction.provision_id).where(
                                or_(
                                    ConsentProvisionAction.text.ilike(
                                        f"%{action}%"
                                    ),
                                    ConsentProvisionAction.id.in_(
                                        select(
                                            ConsentProvisionActionCoding.action_id
                                        ).where(
                                            or_(
                                                ConsentProvisionActionCoding.code
                                                == action,
                                                ConsentProvisionActionCoding.display.ilike(
                                                    f"%{action}%"
                                                ),
                                            )
                                        )
                                    ),
                                )
                            )
                        )
                    )
                )
            )

        if purpose:
            stmt = stmt.where(
                ConsentModel.id.in_(
                    select(ConsentProvision.consent_pk).where(
                        ConsentProvision.id.in_(
                            select(ConsentProvisionPurpose.provision_id).where(
                                or_(
                                    ConsentProvisionPurpose.code == purpose,
                                    ConsentProvisionPurpose.display.ilike(
                                        f"%{purpose}%"
                                    ),
                                )
                            )
                        )
                    )
                )
            )

        if data:
            stmt = stmt.where(
                ConsentModel.id.in_(
                    select(ConsentProvision.consent_pk).where(
                        ConsentProvision.id.in_(
                            select(ConsentProvisionData.provision_id).where(
                                ConsentProvisionData.reference_reference.ilike(
                                    f"%{data}%"
                                )
                            )
                        )
                    )
                )
            )

        if source_reference:
            s_type, s_id = _parse_source_ref(source_reference)
            if s_id:
                stmt = stmt.where(ConsentModel.source_reference_id == s_id)
            else:
                stmt = stmt.where(
                    ConsentModel.source_reference_reference == source_reference
                )

        if organization:
            o_type, o_id = _parse_organization_ref(organization)
            if o_id:
                stmt = stmt.where(
                    ConsentModel.id.in_(
                        select(ConsentOrganization.consent_pk).where(
                            ConsentOrganization.reference_id == o_id
                        )
                    )
                )
            else:
                stmt = stmt.where(
                    ConsentModel.id.in_(
                        select(ConsentOrganization.consent_pk).where(
                            ConsentOrganization.reference_reference.ilike(
                                f"%{organization}%"
                            )
                        )
                    )
                )

        if identifier:
            if "|" in identifier:
                sys, val = identifier.split("|", 1)
                stmt = stmt.where(
                    ConsentModel.id.in_(
                        select(ConsentIdentifier.consent_pk).where(
                            ConsentIdentifier.system == sys,
                            ConsentIdentifier.value == val,
                        )
                    )
                )
            else:
                stmt = stmt.where(
                    ConsentModel.id.in_(
                        select(ConsentIdentifier.consent_pk).where(
                            ConsentIdentifier.value == identifier
                        )
                    )
                )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        status: str | ConsentStatus | None = None,
        scope: str | None = None,
        category: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        period_from: date | datetime | None = None,
        period_to: date | datetime | None = None,
        actor: str | None = None,
        action: str | None = None,
        purpose: str | None = None,
        data: str | None = None,
        source_reference: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
        total_mode: str = "accurate",
    ) -> tuple[list[ConsentModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = dict(
                org_id=org_id,
                status=status,
                scope=scope,
                category=category,
                patient=patient,
                date_val=date_val,
                date_from=date_from,
                date_to=date_to,
                period_from=period_from,
                period_to=period_to,
                actor=actor,
                action=action,
                purpose=purpose,
                data=data,
                source_reference=source_reference,
                organization=organization,
                identifier=identifier,
            )
            base = self._apply_list_filters(select(ConsentModel), **filter_kwargs)
            base = _with_relationships(base)
            count_stmt = self._apply_list_filters(
                select(func.count()).select_from(ConsentModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                ConsentModel.consent_id,
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

    async def delete(self, consent_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ConsentModel).where(
                ConsentModel.consent_id == consent_id,
                ConsentModel.tenant_id == org_id,
            )
            consent = (await session.execute(stmt)).scalars().first()
            if not consent:
                return False
            await session.delete(consent)
            await session.commit()
            return True

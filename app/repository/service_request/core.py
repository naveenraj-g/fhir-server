from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.service_request import (
    ServiceRequestIdentifier,
    ServiceRequestIntent,
    ServiceRequestModel,
    ServiceRequestStatus,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the ServiceRequest parent row (no sub-resources).
    Default (gateway-trusted) pattern — same as QuestionnaireResponse: no
    org-scoped existence check or ownership enforcement here at all."""

    async def get_by_service_request_id(self, service_request_id: int) -> ServiceRequestModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ServiceRequestModel).where(ServiceRequestModel.service_request_id == service_request_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_service_request_id_in_org(
        self, service_request_id: int, org_id: str
    ) -> ServiceRequestModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ServiceRequestModel).where(
                    ServiceRequestModel.service_request_id == service_request_id,
                    ServiceRequestModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def service_request_belongs_to_org(self, service_request_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(ServiceRequestModel.id).where(
                ServiceRequestModel.service_request_id == service_request_id,
                ServiceRequestModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        user_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(ServiceRequestModel.tenant_id == org_id)
        if user_id:
            stmt = stmt.where(ServiceRequestModel.user_id == user_id)
        stmt = apply_token_filter(stmt, ServiceRequestModel.status, status)
        stmt = apply_token_filter(stmt, ServiceRequestModel.intent, intent)
        if subject:
            stmt = stmt.where(ServiceRequestModel.subject_reference == subject)
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(ServiceRequestIdentifier.id).where(
                    ServiceRequestIdentifier.service_request_pk == ServiceRequestModel.id,
                    ServiceRequestIdentifier.value == identifier,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ServiceRequestModel], int | None]:
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "status": status,
                "intent": intent,
                "subject": subject,
                "identifier": identifier,
            }
            base = self._apply_list_filters(_with_relationships(select(ServiceRequestModel)), **filter_kwargs)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ServiceRequestModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, default_column=ServiceRequestModel.service_request_id, default_desc=True
            )
            rows, total = await self._execute_paginated(
                session, base, count_base, sort_column=sort_column, sort_desc=sort_desc,
                limit=limit, offset=offset, total_mode=total_mode,
            )
        logger.debug(
            "ServiceRequests listed",
            extra={
                "event": "service_request.listed",
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
        org_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ServiceRequestModel], int | None]:
        return await self.list(
            org_id=org_id, user_id=user_id, status=status, intent=intent,
            subject=subject, identifier=identifier, limit=limit, offset=offset,
            sort=sort, total_mode=total_mode,
        )

    async def delete(self, service_request_id: int) -> bool:
        """No self-referential/mutual-recursion gotcha here (unlike
        QuestionnaireResponse's item/answer) — every sub-resource is a
        plain two-level child/grandchild, so a plain ORM
        `session.delete()` with the mixin's `cascade="all, delete-orphan"`
        relationships would actually work. Still bulk-deletes explicitly,
        matching every other resource's own `delete()` for consistency
        and because it's no slower."""
        async with self.session_factory() as session:
            stmt = select(ServiceRequestModel).where(ServiceRequestModel.service_request_id == service_request_id)
            sr = (await session.execute(stmt)).scalars().first()
            if not sr:
                return False
            try:
                await session.delete(sr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

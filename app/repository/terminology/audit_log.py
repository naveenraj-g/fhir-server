from sqlalchemy import func, select

from app.models.terminology.terminology import TerminologyAuditLog


class _AuditLogMixin:
    async def list_audit_log(
        self,
        action: str | None,
        performed_by: str | None,
        concept_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[TerminologyAuditLog]]:
        async with self.session_factory() as session:
            stmt = select(TerminologyAuditLog)
            count_stmt = select(func.count()).select_from(TerminologyAuditLog)
            if action:
                stmt = stmt.where(TerminologyAuditLog.action == action)
                count_stmt = count_stmt.where(TerminologyAuditLog.action == action)
            if performed_by:
                stmt = stmt.where(TerminologyAuditLog.performed_by == performed_by)
                count_stmt = count_stmt.where(TerminologyAuditLog.performed_by == performed_by)
            if concept_id is not None:
                stmt = stmt.where(TerminologyAuditLog.concept_id == concept_id)
                count_stmt = count_stmt.where(TerminologyAuditLog.concept_id == concept_id)
            count = await session.scalar(count_stmt)
            rows = await session.execute(
                stmt.order_by(TerminologyAuditLog.created_at.desc()).limit(limit).offset(offset)
            )
            return count or 0, list(rows.scalars().all())

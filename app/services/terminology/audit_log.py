from app.schemas.terminology import AuditLogListResponse, AuditLogRecord


class _AuditLogMixin:
    async def list_audit_log(
        self,
        action: str | None,
        performed_by: str | None,
        concept_id: int | None,
        limit: int,
        offset: int,
    ) -> AuditLogListResponse:
        count, rows = await self.repository.list_audit_log(
            action, performed_by, concept_id, limit, offset
        )
        data = [
            AuditLogRecord(
                id=entry.id,
                action=entry.action,
                concept_id=entry.concept_id,
                value_set_id=entry.value_set_id,
                performed_by=entry.performed_by,
                old_value=entry.old_value,
                new_value=entry.new_value,
                created_at=entry.created_at,
            )
            for entry in rows
        ]
        return AuditLogListResponse(total=count, limit=limit, offset=offset, data=data)
